#!/usr/bin/env python3
"""Actual-AEX entry probe for DG's PF16 staging wrapper.

This probe is intentionally fail-closed.  It enters FUN_181170ff0 with the
smallest callback-backed parameter/world scaffold and records the first
wrapper, fieldgen, compose, import, or callback boundary reached.  A PASS is
reserved for an actual wrapper return with all three path hooks observed.
"""

from __future__ import annotations

import hashlib
import json
import struct
import sys
import traceback
from pathlib import Path

import numpy as np
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_RAX, UC_X86_REG_RBX, UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9, UC_X86_REG_R10, UC_X86_REG_R11, UC_X86_REG_R12, UC_X86_REG_R13, UC_X86_REG_R14, UC_X86_REG_R15, UC_X86_REG_RDI, UC_X86_REG_RIP, UC_X86_REG_RSP

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

import cv_bridge as cvb  # noqa: E402
import opencv_impls as ocv  # noqa: E402
from aex_loader import AexLoader, TEB_BASE  # noqa: E402
from test_dg_compose import build_world, make_loader  # noqa: E402
from windows_runtime import WindowsOpenCVRuntime  # noqa: E402

FUN_WRAPPER = 0x181170FF0
FUN_ITERATE_DRIVER = 0x181170280
FUN_FIELDGEN = 0x181174760
FUN_COMPOSE = 0x181170480
WIDTH, HEIGHT, PAD = 8, 5, 12
ROWBYTES = WIDTH * 8 + PAD
SENTINEL = 0xA5

# Compose refcon contract audited against test_dg_compose.py::build_case0023_refcon.
REFCON_OFFSETS = {
    "src_world": 0x00,
    "field_world": 0x08,
    "degenerate": 0x90,
    "inout_mode": 0x94,
    "grad_g": 0x9C,
    "grad_r": 0xA0,
    "grad_b": 0xA4,
    "bg_g": 0xAC,
    "bg_r": 0xB0,
    "bg_b": 0xB4,
    "use_bg": 0xC0,
    "invert": 0xC1,
    "render_mode": 0xC8,
    "interp_mode": 0xCC,
    "power": 0xD0,
}
CONTRACT = {
    "invert": 1,
    "inout_mode": 3,
    "render_mode": 1,
    "use_bg": 1,
    "interp_mode": 1,
    "power": 1.0,
    "grad_rgb": (28.0 / 255.0, 0.0, 238.0 / 255.0),
    "bg_rgb": (0.0, 0.0, 0.0),
}


def u64(ld: AexLoader, address: int) -> int:
    return struct.unpack("<Q", ld.read_bytes(address, 8))[0]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def setup_tls(ld: AexLoader) -> None:
    block = ld.host_alloc(0x4000, align=16)
    ld.write_bytes(block, b"\x00" * 0x4000)
    slots = ld.host_alloc(256 * 8, align=16)
    for i in range(256):
        ld.write_bytes(slots + i * 8, struct.pack("<Q", block))
    ld.write_bytes(TEB_BASE + 0x58, struct.pack("<Q", slots))


def setup_handle_and_spbasic(ld: AexLoader) -> tuple[int, list[dict[str, object]], list[dict[str, object]], dict[str, object]]:
    suite_events: list[dict[str, object]] = []
    iterate_events: list[dict[str, object]] = []
    iterate_state: dict[str, object] = {}
    def h_new(loader, args):
        size = max(1, args[0])
        data = loader.bump_alloc(size, align=64)
        loader.write_bytes(data, b"\x00" * size)
        handle = loader.host_alloc(8)
        loader.write_bytes(handle, struct.pack("<Q", data))
        return handle

    def h_lock(loader, args):
        return u64(loader, args[0])

    def h_noop(_loader, _args):
        return 0

    handle_suite = ld.host_alloc(0x20)
    ld.write_bytes(handle_suite, struct.pack(
        "<4Q", ld.install_callback("PFHandle.new", h_new),
        ld.install_callback("PFHandle.lock", h_lock),
        ld.install_callback("PFHandle.unlock", h_noop),
        ld.install_callback("PFHandle.dispose", h_noop)))

    def color_get(loader, args):
        # PF ColorParamSuite::PF_GetColor(param, value, PF_PixelFloat* out).
        loader.write_bytes(args[2], struct.pack("<4f", *CONTRACT["grad_rgb"], 1.0))
        return 0

    color_suite = ld.host_alloc(0x08)
    ld.write_bytes(color_suite, struct.pack("<Q", ld.install_callback("PFColor.get", color_get)))

    def iterate16(loader, args):
        rsp = loader.uc.reg_read(UC_X86_REG_RSP)
        stack = {hex(off): hex(u64(loader, rsp + off)) for off in range(0x20, 0x60, 8)}
        callback = u64(loader, rsp + 0x38)
        compose_refcon = u64(loader, rsp + 0x40)
        event = {
            "args": [hex(v) for v in args],
            "stack": stack,
            "callback_candidates": [hex(callback)] if callback == FUN_COMPOSE else [],
            "callback_invocations": 0,
        }
        iterate_events.append(event)

        state = iterate_state
        if callback != FUN_COMPOSE or compose_refcon == 0:
            raise RuntimeError("PF Iterate16 callback contract is not the expected DG compose dispatch")
        output_world = int(state.get("output_world", 0))
        width = int(state.get("width", 0))
        height = args[2]
        if output_world == 0 or width <= 0 or height <= 0 or height > HEIGHT:
            raise RuntimeError("PF Iterate16 callback has no bounded output geometry")

        output_data = u64(loader, output_world + 0x18)
        rowbytes = struct.unpack("<I", loader.read_bytes(output_world + 0x20, 4))[0]
        if rowbytes < width * 8:
            raise RuntimeError("PF Iterate16 output rowbytes is smaller than active pixels")
        loader.read_bytes(output_data, width * 8)
        if "field_capture" not in state:
            field_active = b"".join(loader.read_bytes(output_data + y * rowbytes, width * 8) for y in range(height))
            state["field_capture"] = {
                "raw_words_agrb": [list(struct.unpack("<4H", field_active[i:i + 8])) for i in range(0, len(field_active), 8)],
                "x_values": [struct.unpack("<H", field_active[i + 2:i + 4])[0] / 32768.0 for i in range(0, len(field_active), 8)],
                "active_sha256": hashlib.sha256(field_active).hexdigest(),
                "rowbytes": rowbytes,
            }
        if "compose_observation" not in state:
            src_world = u64(loader, compose_refcon + REFCON_OFFSETS["src_world"])
            src_data = u64(loader, src_world + 0x18)
            state["compose_observation"] = {
                "xy": [0, 0],
                "refcon": {
                    "degenerate": loader.read_bytes(compose_refcon + REFCON_OFFSETS["degenerate"], 1)[0],
                    "inout_mode": struct.unpack("<i", loader.read_bytes(compose_refcon + REFCON_OFFSETS["inout_mode"], 4))[0],
                    "use_bg": loader.read_bytes(compose_refcon + REFCON_OFFSETS["use_bg"], 1)[0],
                    "invert": loader.read_bytes(compose_refcon + REFCON_OFFSETS["invert"], 1)[0],
                    "render_mode": struct.unpack("<i", loader.read_bytes(compose_refcon + REFCON_OFFSETS["render_mode"], 4))[0],
                    "interp_mode": struct.unpack("<i", loader.read_bytes(compose_refcon + REFCON_OFFSETS["interp_mode"], 4))[0],
                    "power": struct.unpack("<f", loader.read_bytes(compose_refcon + REFCON_OFFSETS["power"], 4))[0],
                    "grad_rgb": [struct.unpack("<f", loader.read_bytes(compose_refcon + REFCON_OFFSETS[name], 4))[0] for name in ("grad_r", "grad_g", "grad_b")],
                    "bg_rgb": [struct.unpack("<f", loader.read_bytes(compose_refcon + REFCON_OFFSETS[name], 4))[0] for name in ("bg_r", "bg_g", "bg_b")],
                },
                "source_pixel_agrb": list(struct.unpack("<4H", loader.read_bytes(src_data, 8))),
            }

        # AexLoader.call_function() uses one global return trampoline.  The
        # suite callback runs while that trampoline is already owned by the
        # suspended driver, so run each real AEX compose call on a private
        # guest stack and restore the suspended CPU context after the batch.
        saved = loader.uc.context_save()
        nested_return = int(state["nested_return"])
        nested_stack = int(state["nested_stack"])
        output_ptr = int(state["output_ptr"])
        event.update(nested_stack=hex(nested_stack), output_ptr=hex(output_ptr), compose_refcon=hex(compose_refcon))
        try:
            for y in range(height):
                for x in range(width):
                    loader.write_bytes(output_ptr, b"\xee" * 8)
                    loader.uc.mem_write(nested_stack, struct.pack("<Q", nested_return))
                    loader.uc.mem_write(nested_stack + 0x28, struct.pack("<Q", output_ptr))
                    loader.uc.reg_write(UC_X86_REG_RSP, nested_stack)
                    loader.uc.reg_write(UC_X86_REG_RCX, compose_refcon)
                    loader.uc.reg_write(UC_X86_REG_RDX, x)
                    loader.uc.reg_write(UC_X86_REG_R8, y)
                    loader.uc.reg_write(UC_X86_REG_R9, 0)
                    loader.uc.reg_write(UC_X86_REG_RIP, callback)
                    loader.uc.emu_start(callback, 0, count=200_000)
                    event["nested_rip"] = hex(loader.uc.reg_read(UC_X86_REG_RIP))
                    words = loader.read_bytes(output_ptr, 8)
                    if words == b"\xee" * 8:
                        raise RuntimeError(f"FUN_181170480 wrote no output at ({x},{y})")
                    loader.write_bytes(output_data + y * rowbytes + x * 8, words)
                    event["callback_invocations"] += 1
        finally:
            loader.uc.context_restore(saved)
        return 0

    iterate_suite = ld.host_alloc(0x08)
    ld.write_bytes(iterate_suite, struct.pack("<Q", ld.install_callback("PFIterate16.iterate", iterate16)))

    def acquire(loader, args):
        name_ptr = args[0]
        raw = bytearray()
        for i in range(128):
            byte = loader.read_bytes(name_ptr + i, 1)
            if byte == b"\x00":
                break
            raw.extend(byte)
        name = raw.decode("ascii", errors="replace")
        if "ColorParamSuite" in name:
            suite = color_suite
            result = 0
        elif "Handle Suite" in name:
            suite = handle_suite
            result = 0
        elif "iterate16 Suite" in name:
            suite = iterate_suite
            result = 0
        else:
            suite = 0
            result = 1
        if result == 0:
            loader.write_bytes(args[2], struct.pack("<Q", suite))
        suite_events.append({"name": name, "version": args[1], "out": hex(args[2]), "returned": result, "suite": hex(suite)})
        return result

    spbasic = ld.host_alloc(0x10)
    ld.write_bytes(spbasic, struct.pack(
        "<2Q", ld.install_callback("SPBasic.AcquireSuite", acquire),
        ld.install_callback("SPBasic.ReleaseSuite", h_noop)))
    return spbasic, suite_events, iterate_events, iterate_state


def build_param_table(ld: AexLoader, spbasic: int) -> tuple[int, list[dict[str, int]]]:
    events: list[dict[str, int]] = []

    values = {
        1: (1, 1),       # invert
        2: (3, 4),       # in/out
        3: (158, 4),     # inside threshold
        4: (13, 4),      # outside threshold
        5: (1, 4),       # use background
        6: (1, 4),       # render mode RGB
        9: (4, 4),       # interpolation power
        10: (0, 4),      # blur mode
        11: (0, 4),      # blur size
        12: (0, 4),      # reserved scalar
    }

    def checkout(loader, args):
        rsp = loader.uc.reg_read(UC_X86_REG_RSP)
        selector = args[1] & 0xFFFFFFFF
        # The wrapper call site reserves one additional stack slot for the
        # callback ABI; the live output pointer is at callback RSP+0x30.
        out = u64(loader, rsp + 0x30)
        events.append({"kind": "param_checkout_attempt", "selector": selector, "args": [hex(v) for v in args], "out": out, "rsp": rsp, "stack20": u64(loader, rsp + 0x20), "stack28": u64(loader, rsp + 0x28), "stack30": u64(loader, rsp + 0x30), "stack38": u64(loader, rsp + 0x38)})
        value, size = values.get(selector, (0, 4))
        value_out = out + 0x38
        if selector == 10:
            loader.write_bytes(value_out, struct.pack("<d", 2.59740734100342))
            size = 8
        elif selector in (7, 8):
            loader.write_bytes(out, struct.pack("<4f", *CONTRACT["grad_rgb"], 1.0))
            size = 16
        elif size == 1:
            loader.write_bytes(value_out, bytes([value]))
        else:
            loader.write_bytes(value_out, struct.pack("<I", value))
        events.append({"kind": "param_checkout", "selector": selector, "out": out, "size": size, "value": value})
        return 0

    def release(_loader, _args):
        return 0

    checkout_addr = ld.install_callback("PFParam.checkout", checkout)
    release_addr = ld.install_callback("PFParam.release", release)
    table = ld.host_alloc(0x20)
    ld.write_bytes(table, struct.pack("<4Q", checkout_addr, release_addr, 0, 0))
    handle = ld.host_alloc(8)
    ld.write_bytes(handle, struct.pack("<Q", 0x1234))
    params = ld.host_alloc(0x200, align=16)
    ld.write_bytes(params, b"\x00" * 0x200)
    for off, data in (
        (0x00, struct.pack("<Q", checkout_addr)), (0x08, struct.pack("<Q", release_addr)),
        (0xB8, struct.pack("<Q", handle)), (0xE0, struct.pack("<I", 0)),
        (0xE4, struct.pack("<I", 0)), (0xF0, struct.pack("<I", 0)),
        # PF_InData downsample ratios are denominator/numerator pairs.  These
        # fields are not the world dimensions; putting WIDTH/HEIGHT here makes
        # the AEX stage an 8x5 world as 64x25 and invalidates field comparisons.
        (0x11C, struct.pack("<I", 1)), (0x120, struct.pack("<I", 1)),
        (0x124, struct.pack("<I", 1)), (0x128, struct.pack("<I", 1)),
        (0x180, struct.pack("<Q", spbasic)),
    ):
        ld.write_bytes(params + off, data)
    return params, events


def build_world_provider(ld: AexLoader, output_world: int) -> int:
    provider = ld.host_alloc(0x20)

    def get_world(loader, args):
        loader.write_bytes(args[1], struct.pack("<Q", output_world))
        return 0

    ld.write_bytes(provider, struct.pack("<3Q", 0, 0, ld.install_callback("PFWorld.get", get_world)))
    return provider


def run(
    degenerate: bool = True,
    source_alpha_words: list[int] | None = None,
) -> dict[str, object]:
    ld = make_loader()
    ld.register_libm_impls(max_threads=1)
    WindowsOpenCVRuntime(ld).install()
    spbasic, suite_events, iterate_events, iterate_state = setup_handle_and_spbasic(ld)
    if source_alpha_words is None:
        source_alpha_words = [32768] * (WIDTH * HEIGHT)
    if len(source_alpha_words) != WIDTH * HEIGHT:
        raise ValueError(f"source_alpha_words must contain {WIDTH * HEIGHT} values")
    source_pixels = {
        (x, y): (int(source_alpha_words[y * WIDTH + x]), 0, 0, 0)
        for y in range(HEIGHT)
        for x in range(WIDTH)
    }
    source_world = build_world(ld, WIDTH, HEIGHT, source_pixels)
    compose_source_world = build_world(ld, WIDTH, HEIGHT, source_pixels)
    compose_source_tight = u64(ld, compose_source_world + 0x18)
    compose_source_padded = ld.bump_alloc(ROWBYTES * HEIGHT, align=64)
    ld.write_bytes(compose_source_padded, bytes([SENTINEL]) * (ROWBYTES * HEIGHT))
    for y in range(HEIGHT):
        ld.write_bytes(compose_source_padded + y * ROWBYTES,
                       ld.read_bytes(compose_source_tight + y * WIDTH * 8, WIDTH * 8))
    ld.write_bytes(compose_source_world + 0x18, struct.pack("<Q", compose_source_padded))
    ld.write_bytes(compose_source_world + 0x20, struct.pack("<I", ROWBYTES))
    source_data = u64(ld, source_world + 0x18)
    padded = ld.bump_alloc(ROWBYTES * HEIGHT, align=64)
    ld.write_bytes(padded, bytes([SENTINEL]) * (ROWBYTES * HEIGHT))
    for y in range(HEIGHT):
        ld.write_bytes(padded + y * ROWBYTES, ld.read_bytes(source_data + y * WIDTH * 8, WIDTH * 8))
    ld.write_bytes(source_world + 0x18, struct.pack("<Q", padded))
    ld.write_bytes(source_world + 0x20, struct.pack("<I", ROWBYTES))
    output_world = build_world(ld, WIDTH, HEIGHT, {})
    output_data = ld.bump_alloc(ROWBYTES * HEIGHT, align=64)
    ld.write_bytes(output_data, bytes([SENTINEL]) * (ROWBYTES * HEIGHT))
    ld.write_bytes(output_world + 0x18, struct.pack("<Q", output_data))
    ld.write_bytes(output_world + 0x20, struct.pack("<I", ROWBYTES))
    provider = build_world_provider(ld, output_world)
    params, checkout_events = build_param_table(ld, spbasic)
    result = ld.host_alloc(0x300, align=16)
    ld.write_bytes(result, b"\x00" * 0x300)
    # param_4+8 is the provider object; param_5 is the PF16 input world.
    param4 = ld.host_alloc(0x20)
    ld.write_bytes(param4 + 8, struct.pack("<Q", provider))

    stages: list[dict[str, object]] = []

    def hook(label: str):
        def capture(loader: AexLoader, address: int, size: int):
            rsp = loader.uc.reg_read(UC_X86_REG_RSP)
            stages.append({"stage": label, "address": hex(address), "size": size, "rsp": hex(rsp), "rcx": hex(loader.uc.reg_read(UC_X86_REG_RCX)), "rdx": hex(loader.uc.reg_read(UC_X86_REG_RDX)), "r8": hex(loader.uc.reg_read(UC_X86_REG_R8)), "r9": hex(loader.uc.reg_read(UC_X86_REG_R9)), "stack28": hex(u64(loader, rsp + 0x28)), "stack30": hex(u64(loader, rsp + 0x30))})
        return capture

    ld.add_code_hook(FUN_WRAPPER, hook("FUN_181170ff0"))
    ld.add_code_hook(FUN_FIELDGEN, hook("FUN_181174760"))
    ld.add_code_hook(FUN_COMPOSE, hook("FUN_181170480"))
    report: dict[str, object] = {
        "status": "blocked", "function": hex(FUN_WRAPPER),
        "classification": "bounded same-loader actual-AEX reachability probe; no AE-exact claim",
        "compose_fixture": "degenerate PF16 compose branch" if degenerate else "non-degenerate PF16 compose branch",
        "ae_exact_claim": False,
        "binary_sha256": sha256_file(ROOT / "aex/OLMDistanceGradation/Plugins/64/2025/DistanceGradation.aex"),
        "stages": stages, "callback_events": checkout_events,
        "callbacks_before_call": list(ld.callback_log),
        "import_names": [], "wrapper_returned": False,
    }
    try:
        regs = ld.call_function(FUN_WRAPPER, int_args=[0x10, params, 0, param4, source_world, result], max_instructions=20_000_000)
        report.update(wrapper_returned=True, registers={key: (value.hex() if isinstance(value, bytes) else value) for key, value in regs.items()})

        # FUN_181170ff0 is the field-producing half of the 16bpc caller.  Use
        # its actual output world as refcon[1], then enter the caller's real
        # iterate16 dispatch in this same AEX loader.
        refcon = ld.host_alloc(0x100, align=16)
        ld.write_bytes(refcon, b"\x00" * 0x100)
        ld.write_bytes(refcon + REFCON_OFFSETS["src_world"], struct.pack("<Q", compose_source_world))
        ld.write_bytes(refcon + REFCON_OFFSETS["field_world"], struct.pack("<Q", output_world))
        ld.write_bytes(refcon + REFCON_OFFSETS["degenerate"], bytes([1 if degenerate else 0]))
        ld.write_bytes(refcon + REFCON_OFFSETS["inout_mode"], struct.pack("<i", CONTRACT["inout_mode"]))
        grad_r, grad_g, grad_b = CONTRACT["grad_rgb"]
        bg_r, bg_g, bg_b = CONTRACT["bg_rgb"]
        for name, value in (("grad_g", grad_g), ("grad_r", grad_r), ("grad_b", grad_b),
                            ("bg_g", bg_g), ("bg_r", bg_r), ("bg_b", bg_b)):
            ld.write_bytes(refcon + REFCON_OFFSETS[name], struct.pack("<f", value))
        ld.write_bytes(refcon + REFCON_OFFSETS["use_bg"], bytes([CONTRACT["use_bg"]]))
        ld.write_bytes(refcon + REFCON_OFFSETS["invert"], bytes([CONTRACT["invert"]]))
        ld.write_bytes(refcon + REFCON_OFFSETS["render_mode"], struct.pack("<i", CONTRACT["render_mode"]))
        ld.write_bytes(refcon + REFCON_OFFSETS["interp_mode"], struct.pack("<i", CONTRACT["interp_mode"]))
        ld.write_bytes(refcon + REFCON_OFFSETS["power"], struct.pack("<f", CONTRACT["power"]))
        scalar_contract = {
            "degenerate": int(degenerate),
            "inout_mode": CONTRACT["inout_mode"], "use_bg": CONTRACT["use_bg"],
            "invert": CONTRACT["invert"], "render_mode": CONTRACT["render_mode"],
            "interp_mode": CONTRACT["interp_mode"], "power": CONTRACT["power"],
            "grad_rgb": list(CONTRACT["grad_rgb"]), "bg_rgb": list(CONTRACT["bg_rgb"]),
        }
        assert struct.unpack("<i", ld.read_bytes(refcon + REFCON_OFFSETS["inout_mode"], 4))[0] == 3
        assert struct.unpack("<i", ld.read_bytes(refcon + REFCON_OFFSETS["render_mode"], 4))[0] == 1
        assert struct.unpack("<i", ld.read_bytes(refcon + REFCON_OFFSETS["interp_mode"], 4))[0] == 1
        assert ld.read_bytes(refcon + REFCON_OFFSETS["grad_r"], 4) == struct.pack("<f", grad_r)
        assert ld.read_bytes(refcon + REFCON_OFFSETS["grad_b"], 4) == struct.pack("<f", grad_b)
        assert ld.read_bytes(refcon + REFCON_OFFSETS["bg_r"], 4) == struct.pack("<f", bg_r)
        assert ld.read_bytes(refcon + REFCON_OFFSETS["bg_b"], 4) == struct.pack("<f", bg_b)
        # FUN_181170280 passes param_5[1] as the compose callback refcon.
        # Keep that driver context distinct from the actual compose state.
        driver_context = ld.host_alloc(0x10, align=16)
        ld.write_bytes(driver_context, b"\x00" * 0x10)
        ld.write_bytes(driver_context + 0x08, struct.pack("<Q", refcon))
        iterate_state.update(
            output_world=output_world,
            width=WIDTH,
            nested_return=0x90001000,
            nested_stack=0xE080000,
            output_ptr=ld.bump_alloc(8, align=16),
        )
        try:
            ld.uc.mem_map(0x90001000, 0x1000)
        except Exception:
            pass
        def stop_nested(uc, address, _size, _user_data):
            if address == 0x90001000:
                uc.emu_stop()
        ld.uc.hook_add(UC_HOOK_CODE, stop_nested, begin=0x90001000, end=0x90001000)
        try:
            ld.uc.mem_map(0xE000000, 0x100000)
        except Exception:
            pass
        render_context = ld.host_alloc(0x80, align=16)
        ld.write_bytes(render_context, b"\x00" * 0x80)
        ld.write_bytes(render_context + 0x30, struct.pack("<i", 0))
        ld.write_bytes(render_context + 0x38, struct.pack("<i", HEIGHT))
        ld.call_function(FUN_ITERATE_DRIVER, int_args=[params, 0, source_world, render_context, driver_context], max_instructions=5_000_000)
        downstream = any(stage["stage"] == "FUN_181174760" for stage in stages) and any(stage["stage"] == "FUN_181170480" for stage in stages)
        report["status"] = "PASS" if downstream else "blocked"
        report["iterate_callback_invocations"] = sum(item["callback_invocations"] for item in iterate_events)
        active = b"".join(ld.read_bytes(output_data + y * ROWBYTES, WIDTH * 8) for y in range(HEIGHT))
        padding = b"".join(ld.read_bytes(output_data + y * ROWBYTES + WIDTH * 8, PAD) for y in range(HEIGHT))
        report["output_active_sha256"] = hashlib.sha256(active).hexdigest()
        report["parameter_contract"] = {"offsets": {key: hex(value) for key, value in REFCON_OFFSETS.items()}, "values": scalar_contract}
        report["world_contract"] = {
            "width": WIDTH, "height": HEIGHT, "rowbytes": ROWBYTES,
            "source_active_sha256": hashlib.sha256(b"".join(ld.read_bytes(u64(ld, compose_source_world + 0x18) + y * ROWBYTES, WIDTH * 8) for y in range(HEIGHT))).hexdigest(),
            "field_world_data": hex(u64(ld, output_world + 0x18)),
            "field_world_rowbytes": struct.unpack("<I", ld.read_bytes(output_world + 0x20, 4))[0],
        }
        report["field_capture"] = iterate_state["field_capture"]
        report["compose_observation"] = iterate_state["compose_observation"]
        report["output_active_words_agrb"] = [
            list(struct.unpack("<4H", active[offset : offset + 8]))
            for offset in range(0, len(active), 8)
        ]
        report["padding_canary"] = {"observable": True, "preserved": padding == bytes([SENTINEL]) * (PAD * HEIGHT), "sha256": hashlib.sha256(padding).hexdigest()}
        if not downstream:
            report["blocker"] = "FUN_181170280 returned before FUN_181170480; PF Iterate16 suite callback did not reach compose"
    except Exception as exc:
        report.update(
            blocker=type(exc).__name__ + ": " + str(exc),
            traceback=traceback.format_exc(limit=5),
            rip=hex(ld.uc.reg_read(UC_X86_REG_RIP)),
            callback_at_fault=(ld.callbacks.get(ld.uc.reg_read(UC_X86_REG_RIP), (None, None))[0]),
            callback_args_at_fault=[hex(v) for v in ld._read_int_args(ld.uc, 4)],
            registers_at_fault={name: hex(ld.uc.reg_read(reg)) for name, reg in (("rax", UC_X86_REG_RAX), ("rbx", UC_X86_REG_RBX), ("rcx", UC_X86_REG_RCX), ("rdx", UC_X86_REG_RDX), ("r8", UC_X86_REG_R8), ("r9", UC_X86_REG_R9), ("rsp", UC_X86_REG_RSP))},
            return_address=hex(u64(ld, ld.uc.reg_read(UC_X86_REG_RSP) + 0x78)),
        )
    report["callback_log"] = [{"label": label, "args": [hex(v) for v in args], "ret": ret} for label, args, ret in ld.callback_log]
    report["import_names"] = [entry.name for entry in ld.import_log]
    report["callback_map"] = {hex(address): label for address, (label, _handler) in ld.callbacks.items()}
    report["suite_events"] = suite_events
    report["iterate_events"] = iterate_events
    report["result_context_fields"] = {
        hex(off): ld.read_bytes(result + off, 4).hex()
        for off in (0x12, 0x94, 0xB8, 0xBC, 0xC0, 0xC1, 0xC8, 0xCC, 0xD0, 0xD4, 0xD8)
    }
    report["result_qwords_0_4"] = [hex(u64(ld, result + off)) for off in (0, 8, 16, 24, 32)]
    report["wrapper_entry_hook_hits"] = sum(stage["stage"] == "FUN_181170ff0" for stage in stages)
    report["fieldgen_entry_hook_hits"] = sum(stage["stage"] == "FUN_181174760" for stage in stages)
    report["compose_entry_hook_hits"] = sum(stage["stage"] == "FUN_181170480" for stage in stages)
    return report


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
