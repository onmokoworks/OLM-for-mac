#!/usr/bin/env python3
"""Compare OLMBlur PF32 direct-worker and exported-Smart entry state.

Diagnostic only: this executes the pinned Windows AEX under the repository's
AexLoader/Unicorn harness.  It does not write canonical evidence or change the
production admission map.
"""

from __future__ import annotations

import hashlib
import json
import math
import struct
import sys
from pathlib import Path

from unicorn.x86_const import (
    UC_X86_REG_R8,
    UC_X86_REG_R9,
    UC_X86_REG_RCX,
    UC_X86_REG_RDX,
    UC_X86_REG_RSP,
)

sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402
from test_olmblur_fullentry import build_context, build_pf_suites  # noqa: E402
from test_olmblur_worker32_nonlegacy import source_bytes  # noqa: E402


ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "plugins_2025/OLMBlur.aex"
ENTRY = 0x18000A970
WORKER = 0x180004B80
WIDTH, HEIGHT, DEPTH = 4, 3, 32
ROWBYTES = WIDTH * 16 + 13
AMOUNT, SMOOTHNESS, REPEAT, BIAS = 129.4, 100, 2, 1


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def qword(loader: AexLoader, address: int, value: int) -> None:
    loader.write_bytes(address, struct.pack("<Q", value))


def stack_arg(loader: AexLoader, index: int) -> int:
    rsp = loader.uc.reg_read(UC_X86_REG_RSP)
    return struct.unpack("<Q", loader.read_bytes(rsp + 0x28 + (index - 4) * 8, 8))[0]


def make_loader(set_time: bool = True) -> tuple[AexLoader, int]:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    loader.register_libm_impls(max_threads=1)
    # Import handlers receive the raw Unicorn object, not AexLoader.  Close
    # over ``loader`` exactly as the original direct-worker fixture exporter
    # does; using the callback's first argument would silently raise inside
    # AexLoader and leave XMM0 unchanged.
    def impl_pow(_uc, _args):
        loader.write_xmm_f64(0, math.pow(loader.read_xmm_f64(0), loader.read_xmm_f64(1)))
        return 0

    def impl_powf(_uc, _args):
        loader.write_xmm_f32(0, math.pow(loader.read_xmm_f32(0), loader.read_xmm_f32(1)))
        return 0

    loader.register_import_impl("pow", impl_pow)
    loader.register_import_impl("powf", impl_powf)
    spbasic, _events = build_pf_suites(loader)
    context = build_context(loader, spbasic)
    if set_time:
        loader.write_bytes(context + 0xE0, struct.pack("<iii", 7, 1, 24))
    return loader, context


def alloc(loader: AexLoader, size: int, fill: int) -> int:
    address = loader.bump_alloc(size, align=64)
    loader.write_bytes(address, bytes((fill,)) * size)
    return address


def make_world(loader: AexLoader, data: int, rowbytes: int = ROWBYTES) -> int:
    world = loader.host_alloc(0x80)
    loader.write_bytes(world, bytes(0x80))
    qword(loader, world + 0x18, data)
    loader.write_bytes(world + 0x20, struct.pack("<IIIH", rowbytes, WIDTH, HEIGHT, DEPTH))
    return world


def active(loader: AexLoader, data: int, rowbytes: int = ROWBYTES) -> bytes:
    return b"".join(loader.read_bytes(data + y * rowbytes, WIDTH * 16) for y in range(HEIGHT))


def install_worker_capture(loader: AexLoader, label: str, captures: list[dict[str, object]]) -> None:
    def capture(ld: AexLoader, _address: int, _size: int) -> None:
        registers = [
            ld.uc.reg_read(UC_X86_REG_RCX),
            ld.uc.reg_read(UC_X86_REG_RDX),
            ld.uc.reg_read(UC_X86_REG_R8),
            ld.uc.reg_read(UC_X86_REG_R9),
        ]
        context, source_world, output_world, params = registers
        ld.add_read_trace_range(params, params + 0x40, f"{label}.params")
        source_data = struct.unpack("<Q", ld.read_bytes(source_world + 0x18, 8))[0]
        row = {
            "label": label,
            "registers": [hex(value) for value in registers],
            "context_0xe0_0x128": ld.read_bytes(context + 0xE0, 0x48).hex(),
            "source_world_0x18_0x30": ld.read_bytes(source_world + 0x18, 0x18).hex(),
            "output_world_0x18_0x30": ld.read_bytes(output_world + 0x18, 0x18).hex(),
            "params_0x00_0x40": ld.read_bytes(params, 0x40).hex(),
            "params_fields": {
                "depth": struct.unpack("<I", ld.read_bytes(params + 0x18, 4))[0],
                "offset_0x1c_float": struct.unpack("<f", ld.read_bytes(params + 0x1C, 4))[0],
                "amount": struct.unpack("<f", ld.read_bytes(params + 0x20, 4))[0],
                "smoothness": struct.unpack("<f", ld.read_bytes(params + 0x24, 4))[0],
                "repeat": struct.unpack("<I", ld.read_bytes(params + 0x28, 4))[0],
                "bias": struct.unpack("<I", ld.read_bytes(params + 0x2C, 4))[0],
            },
            "source_active_sha256": sha(active(ld, source_data)),
        }
        captures.append(row)

    loader.add_code_hook(WORKER, capture)


def initialize_source(loader: AexLoader) -> tuple[int, int, bytes]:
    source = source_bytes(WIDTH, HEIGHT)
    source_data = alloc(loader, ROWBYTES * HEIGHT, 0xA5)
    output_data = alloc(loader, ROWBYTES * HEIGHT, 0xEE)
    for y in range(HEIGHT):
        loader.write_bytes(source_data + y * ROWBYTES, source[y * WIDTH * 16:(y + 1) * WIDTH * 16])
    return source_data, output_data, source


def run_direct(offset_1c: float, rowbytes: int, set_time: bool, capture_worker: bool = True) -> dict[str, object]:
    loader, context = make_loader(set_time=set_time)
    source = source_bytes(WIDTH, HEIGHT)
    source_data = alloc(loader, rowbytes * HEIGHT, 0xA5)
    output_data = alloc(loader, rowbytes * HEIGHT, 0xEE)
    for y in range(HEIGHT):
        loader.write_bytes(source_data + y * rowbytes, source[y * WIDTH * 16:(y + 1) * WIDTH * 16])
    loader.write_bytes(output_data, loader.read_bytes(source_data, rowbytes * HEIGHT))
    source_world, output_world = make_world(loader, source_data, rowbytes), make_world(loader, output_data, rowbytes)
    params = loader.host_alloc(0x40)
    loader.write_bytes(params, bytes(0x40))
    loader.write_bytes(params + 0x18, struct.pack("<Iff fII", DEPTH, offset_1c, AMOUNT, float(SMOOTHNESS), REPEAT, BIAS))
    captures: list[dict[str, object]] = []
    if capture_worker:
        install_worker_capture(loader, f"direct_{offset_1c:g}", captures)
    result = loader.call_function(WORKER, int_args=[context, source_world, output_world, params], max_instructions=8_000_000)
    output = active(loader, output_data, rowbytes)
    return {
        "kind": "direct",
        "offset_0x1c": offset_1c,
        "rowbytes": rowbytes,
        "set_time": set_time,
        "return": result["rax"],
        "instructions": result["instructions"],
        "source_sha256": sha(source),
        "output_sha256": sha(output),
        "capture": captures[0] if captures else None,
        "param_reads": [list(item) for item in loader.read_trace if item[0].startswith("direct_")],
    }


def run_public() -> dict[str, object]:
    loader, context = make_loader()
    source_data, output_data, source = initialize_source(loader)
    source_world, output_world = make_world(loader, source_data), make_world(loader, output_data)
    out_data = loader.host_alloc(0x300)
    loader.write_bytes(out_data, bytes(0x300))
    effect_ref = 0x12345678
    qword(loader, context + 0xB8, effect_ref)

    utils = loader.host_alloc(0x48)
    loader.write_bytes(utils, bytes(0x48))

    def copy_world(ld: AexLoader, args: list[int]) -> int:
        source_pointer = struct.unpack("<Q", ld.read_bytes(args[1] + 0x18, 8))[0]
        destination_pointer = struct.unpack("<Q", ld.read_bytes(args[2] + 0x18, 8))[0]
        ld.write_bytes(destination_pointer, ld.read_bytes(source_pointer, ROWBYTES * HEIGHT))
        return 0

    qword(loader, utils + 0x40, loader.install_callback("PF/copy", copy_world))
    qword(loader, context + 0xB0, utils)

    def checkout_param(ld: AexLoader, args: list[int]) -> int:
        index, out = int(args[1]), stack_arg(ld, 5)
        ld.write_bytes(out, bytes(0xB0))
        if index == 1:
            ld.write_bytes(out + 0x38, struct.pack("<d", AMOUNT))
        elif index == 2:
            ld.write_bytes(out + 0x3A, struct.pack("<h", SMOOTHNESS))
        elif index == 3:
            ld.write_bytes(out + 0x38, struct.pack("<i", REPEAT))
        elif index == 4:
            ld.write_bytes(out + 0x38, struct.pack("<i", BIAS))
        elif index == 5:
            ld.write_bytes(out + 0x38, b"\0")
        else:
            return 91
        return 0

    qword(loader, context, loader.install_callback("PF/checkout_param", checkout_param))
    qword(loader, context + 8, loader.install_callback("PF/checkin_param", lambda _ld, _args: 0))

    def pre_checkout(ld: AexLoader, _args: list[int]) -> int:
        result = stack_arg(ld, 7)
        rect = struct.pack("<4i", 0, 0, WIDTH, HEIGHT)
        ld.write_bytes(result, rect + rect + struct.pack("<i", WIDTH))
        return 0

    request = loader.host_alloc(0x30)
    loader.write_bytes(request, bytes(0x30))
    pre_input, pre_output = loader.host_alloc(0x40), loader.host_alloc(0x80)
    loader.write_bytes(pre_input, bytes(0x40))
    loader.write_bytes(pre_output, bytes(0x80))
    qword(loader, pre_input, request)
    pre_callbacks = loader.host_alloc(0x18)
    loader.write_bytes(pre_callbacks, bytes(0x18))
    qword(loader, pre_callbacks, loader.install_callback("PF/pre_checkout_layer", pre_checkout))
    pre_extra = loader.host_alloc(0x18)
    qword(loader, pre_extra, pre_input)
    qword(loader, pre_extra + 8, pre_output)
    qword(loader, pre_extra + 0x10, pre_callbacks)
    pre = loader.call_function(ENTRY, int_args=[23, context, out_data, 0, 0, pre_extra], max_instructions=100_000)

    def checkout_pixels(ld: AexLoader, args: list[int]) -> int:
        qword(ld, args[2], source_world)
        return 0

    def checkout_output(ld: AexLoader, args: list[int]) -> int:
        qword(ld, args[1], output_world)
        return 0

    smart_input = loader.host_alloc(0x40)
    loader.write_bytes(smart_input, bytes(0x40))
    loader.write_bytes(smart_input + 0x2C, struct.pack("<H", DEPTH))
    smart_callbacks = loader.host_alloc(0x18)
    loader.write_bytes(smart_callbacks, bytes(0x18))
    qword(loader, smart_callbacks, loader.install_callback("PF/checkout_layer_pixels", checkout_pixels))
    qword(loader, smart_callbacks + 0x10, loader.install_callback("PF/checkout_output", checkout_output))
    smart_extra = loader.host_alloc(0x10)
    qword(loader, smart_extra, smart_input)
    qword(loader, smart_extra + 8, smart_callbacks)
    captures: list[dict[str, object]] = []
    install_worker_capture(loader, "public", captures)
    render = loader.call_function(ENTRY, int_args=[24, context, out_data, 0, 0, smart_extra], max_instructions=8_000_000)
    output = active(loader, output_data)
    return {
        "kind": "public",
        "return": render["rax"],
        "pre_return": pre["rax"],
        "instructions": render["instructions"],
        "source_sha256": sha(source),
        "output_sha256": sha(output),
        "capture": captures[0],
        "param_reads": [list(item) for item in loader.read_trace if item[0] == "public.params"],
    }


def main() -> int:
    rows = [run_direct(0.0, WIDTH * 16, False, False), run_direct(0.0, WIDTH * 16, False), run_direct(0.0, WIDTH * 16, True), run_direct(0.0, ROWBYTES, True), run_direct(20.0, ROWBYTES, True), run_public()]
    report = {"schema": "olmblur.pf32-public-direct-context-diagnostic/1", "rows": rows}
    print(json.dumps(report, indent=2, sort_keys=True))
    assert rows[0]["output_sha256"] == rows[1]["output_sha256"] == rows[2]["output_sha256"] == rows[3]["output_sha256"] == rows[4]["output_sha256"] == rows[5]["output_sha256"]
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
