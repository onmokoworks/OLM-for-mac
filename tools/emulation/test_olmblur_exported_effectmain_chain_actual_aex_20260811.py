#!/usr/bin/env python3
"""Execute the actual OLMBlur export through its public smart-render chain.

The retained typed-worker buffers are the oracle.  This probe only closes the
public command/suite plumbing seam; it does not introduce new pixel values.
"""

from __future__ import annotations

import hashlib
import json
import math
import struct
import sys
from pathlib import Path
from unicorn.x86_const import UC_X86_REG_RSP

sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402
from test_olmblur_fullentry import build_context, build_pf_suites  # noqa: E402
import test_olmblur_amount_repeat_legacy_matrix_actual_aex_20260810 as base  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "plugins_2025/OLMBlur.aex"
ENTRY = 0x18000A970
FIXTURE = Path(__file__).parent / "fixtures/olmblur_amount_repeat_legacy_matrix_20260810"
REPORT = ROOT / "refs/conformance/olmblur_exported_effectmain_chain_actual_aex_20260811.json"
WIDTH = HEIGHT = 24
PADDING = {8: 17, 16: 23, 32: 32}
PIXEL_BYTES = {8: 4, 16: 8, 32: 16}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def qword(loader: AexLoader, address: int, value: int) -> None:
    loader.write_bytes(address, struct.pack("<Q", value))


def stack_arg(loader: AexLoader, index: int) -> int:
    """Read a >=4 argument at a Windows x64 callback entry."""
    assert index >= 4
    rsp = loader.uc.reg_read(UC_X86_REG_RSP)
    return struct.unpack("<Q", loader.read_bytes(rsp + 0x28 + (index - 4) * 8, 8))[0]


def alloc(loader: AexLoader, size: int, fill: int = 0) -> int:
    address = loader.bump_alloc(size, align=64)
    loader.write_bytes(address, bytes((fill,)) * size)
    return address


def run_row(case: dict[str, object]) -> dict[str, object]:
    depth, legacy = int(case["depth"]), int(case["legacy"])
    pixel_bytes, padding = PIXEL_BYTES[depth], PADDING[depth]
    active = WIDTH * pixel_bytes
    rowbytes = active + padding
    source = (FIXTURE / str(case["source"])).read_bytes()
    expected = (FIXTURE / str(case["expected"])).read_bytes()
    assert len(source) == len(expected) == active * HEIGHT

    loader = AexLoader(str(AEX), verbose=False, fast=True)
    loader.register_libm_impls(max_threads=1)
    loader.register_import_impl("pow", lambda ld, args: (ld.write_xmm_f64(0, math.pow(ld.read_xmm_f64(0), ld.read_xmm_f64(1))) or 0))
    loader.register_import_impl("powf", lambda ld, args: (ld.write_xmm_f32(0, math.pow(ld.read_xmm_f32(0), ld.read_xmm_f32(1))) or 0))
    spbasic, handle_events = build_pf_suites(loader)
    in_data = build_context(loader, spbasic)
    out_data = loader.host_alloc(0x300)
    loader.write_bytes(out_data, b"\0" * 0x300)
    effect_ref = 0x12345678
    qword(loader, in_data + 0xB8, effect_ref)
    loader.write_bytes(in_data + 0xE0, struct.pack("<iii", 7, 1, 24))

    source_data, output_data = alloc(loader, rowbytes * HEIGHT, 0xA5), alloc(loader, rowbytes * HEIGHT, 0xEE)
    for y in range(HEIGHT):
        loader.write_bytes(source_data + y * rowbytes, source[y * active:(y + 1) * active])

    def world(data: int) -> int:
        address = loader.host_alloc(0x80)
        loader.write_bytes(address, b"\0" * 0x80)
        qword(loader, address + 0x18, data)
        loader.write_bytes(address + 0x20, struct.pack("<IIIH", rowbytes, WIDTH, HEIGHT, depth))
        return address

    input_world, output_world = world(source_data), world(output_data)
    callback_events: list[str] = []
    param_order: list[int] = []

    # PF_UtilCallbacks::copy at +0x40.  OLMBlur initializes the destination
    # before its RGB-only workers run, preserving source alpha and row padding.
    def copy_world(ld: AexLoader, args: list[int]) -> int:
        callback_events.append("copy_world")
        source_world, destination_world = args[1], args[2]
        source_pointer = struct.unpack("<Q", ld.read_bytes(source_world + 0x18, 8))[0]
        destination_pointer = struct.unpack("<Q", ld.read_bytes(destination_world + 0x18, 8))[0]
        ld.write_bytes(destination_pointer, ld.read_bytes(source_pointer, rowbytes * HEIGHT))
        return 0

    utils = loader.host_alloc(0x48)
    loader.write_bytes(utils, b"\0" * 0x48)
    qword(loader, utils + 0x40, loader.install_callback("PF/copy", copy_world))
    qword(loader, in_data + 0xB0, utils)

    values = {1: float(case["amount"]), 2: 100, 3: 1, 4: 1, 5: legacy}

    def checkout_param(ld: AexLoader, args: list[int]) -> int:
        index, out = int(args[1]), stack_arg(ld, 5)
        param_order.append(index)
        ld.write_bytes(out, b"\0" * 0xB0)
        if index == 1:
            ld.write_bytes(out + 0x38, struct.pack("<d", values[index]))
        elif index == 2:
            ld.write_bytes(out + 0x3A, struct.pack("<h", values[index]))
        elif index in (3, 4):
            ld.write_bytes(out + 0x38, struct.pack("<i", values[index]))
        elif index == 5:
            ld.write_bytes(out + 0x38, bytes((values[index],)))
        else:
            return 91
        return 0

    def checkin_param(_ld: AexLoader, args: list[int]) -> int:
        callback_events.append(f"checkin_param_{param_order[-1]}")
        return 0

    qword(loader, in_data, loader.install_callback("PF/checkout_param", checkout_param))
    qword(loader, in_data + 8, loader.install_callback("PF/checkin_param", checkin_param))

    # SMART_PRE_RENDER.  The callback returns a PF_CheckoutResult-like record;
    # the export copies its two rectangles into PF_PreRenderOutput.
    def pre_checkout(ld: AexLoader, args: list[int]) -> int:
        callback_events.append("pre_checkout_layer")
        result = stack_arg(ld, 7)
        rect = struct.pack("<4i", 0, 0, WIDTH, HEIGHT)
        ld.write_bytes(result, rect + rect + struct.pack("<i", WIDTH))
        return 0

    request = loader.host_alloc(0x30)
    loader.write_bytes(request, b"\0" * 0x30)
    pre_input, pre_output = loader.host_alloc(0x40), loader.host_alloc(0x80)
    loader.write_bytes(pre_input, b"\0" * 0x40)
    loader.write_bytes(pre_output, b"\0" * 0x80)
    qword(loader, pre_input, request)
    pre_callbacks = loader.host_alloc(0x18)
    loader.write_bytes(pre_callbacks, b"\0" * 0x18)
    qword(loader, pre_callbacks, loader.install_callback("PF/pre_checkout_layer", pre_checkout))
    pre_extra = loader.host_alloc(0x18)
    qword(loader, pre_extra, pre_input)
    qword(loader, pre_extra + 8, pre_output)
    qword(loader, pre_extra + 0x10, pre_callbacks)
    pre = loader.call_function(ENTRY, int_args=[23, in_data, out_data, 0, 0, pre_extra], max_instructions=100_000)

    def checkout_pixels(ld: AexLoader, args: list[int]) -> int:
        callback_events.append("checkout_layer_pixels")
        qword(ld, args[2], input_world)
        return 0

    def checkout_output(ld: AexLoader, args: list[int]) -> int:
        callback_events.append("checkout_output")
        qword(ld, args[1], output_world)
        return 0

    smart_input = loader.host_alloc(0x40)
    loader.write_bytes(smart_input, b"\0" * 0x40)
    loader.write_bytes(smart_input + 0x2C, struct.pack("<H", depth))
    smart_callbacks = loader.host_alloc(0x18)
    loader.write_bytes(smart_callbacks, b"\0" * 0x18)
    qword(loader, smart_callbacks, loader.install_callback("PF/checkout_layer_pixels", checkout_pixels))
    qword(loader, smart_callbacks + 0x10, loader.install_callback("PF/checkout_output", checkout_output))
    smart_extra = loader.host_alloc(0x10)
    qword(loader, smart_extra, smart_input)
    qword(loader, smart_extra + 8, smart_callbacks)
    render = loader.call_function(ENTRY, int_args=[24, in_data, out_data, 0, 0, smart_extra], max_instructions=100_000_000)

    actual = bytearray()
    padding_mismatches = 0
    for y in range(HEIGHT):
        row = loader.read_bytes(output_data + y * rowbytes, rowbytes)
        actual.extend(row[:active])
        padding_mismatches += sum(byte != 0xA5 for byte in row[active:])
    mismatches = sum(a != b for a, b in zip(actual, expected))
    assert pre["rax"] == render["rax"] == 0
    assert param_order == [1, 2, 3, 4, 5]
    assert callback_events[:3] == ["pre_checkout_layer", "checkout_layer_pixels", "checkout_output"]
    assert mismatches == padding_mismatches == 0, (case["id"], mismatches, padding_mismatches, param_order, callback_events)
    return {
        "id": case["id"], "depth": depth, "legacy": legacy,
        "commands": [23, 24], "return_codes": [pre["rax"], render["rax"]],
        "parameter_checkout_order": param_order,
        "callback_events": callback_events,
        "active_sha256": sha256(bytes(actual)), "oracle_sha256": case["expected_sha256"],
        "mismatched_bytes": mismatches, "padding_mismatches": padding_mismatches,
        "instructions": {"smart_pre_render": pre["instructions"], "smart_render": render["instructions"]},
        "handle_suite_events": len(handle_events),
    }


def main() -> int:
    assert sha256(AEX.read_bytes()) == base.AEX_SHA256
    manifest = json.loads((FIXTURE / "manifest.json").read_text())
    rows = [row for row in manifest["cases"] if row["amount"] == 5.0 and row["repeat"] == 1]
    assert len(rows) == 6
    results = [run_row(row) for row in rows]
    report = {
        "schema": "olmblur.exported-effectmain-chain.actual-aex/1",
        "status": "exact",
        "plugin": "OLMBlur", "actual_aex_sha256": base.AEX_SHA256,
        "exported_entry": f"0x{ENTRY:x}", "geometry": [WIDTH, HEIGHT],
        "row_padding_bytes": PADDING, "matrix": {"depth": [8, 16, 32], "legacy": [0, 1]},
        "parameters": {"amount": 5, "smoothness": 100, "repeat": 1, "bias_direction": 1},
        "path": ["exported EffectMain(PF_Cmd_SMART_PRE_RENDER)", "checkout_layer", "exported EffectMain(PF_Cmd_SMART_RENDER)", "checkout_layer_pixels", "checkout_output", "checkout_param 1..5", "typed worker", "typed writer"],
        "case_count": len(results), "raw_exact": len(results), "cases": results,
        "production_changed": False,
        "evidence_boundary": "Actual Windows 2025 AEX export under AEXCompat/Unicorn with bounded synthetic suites. Complete active typed buffers equal retained actual-worker oracles and row padding is untouched. This is not native AE execution.",
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("PASS_OLMBLUR_EXPORTED_EFFECTMAIN_CHAIN cases=6 raw_exact=6")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
