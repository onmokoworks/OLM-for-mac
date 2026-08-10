#!/usr/bin/env python3
"""Run the actual OLMColorKey PF16 SmartRender worker with a typed tiny world.

Only AE's parameter-materialization helper is replaced by a pinned zero-edge
record.  The checkout callbacks, FUN_1800018e0 bit-depth dispatch, and native
FUN_180009000 worker execute under Unicorn.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

from unicorn.x86_const import (UC_X86_REG_R8, UC_X86_REG_R9, UC_X86_REG_RAX,
                               UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_RIP,
                               UC_X86_REG_RSP, UC_X86_REG_XMM1)


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from aex_loader import AexLoader  # noqa: E402


AEX = ROOT / "aex/OLMColorKey/Plugins/64/2025/OLMColorKey.aex"
AEX_SHA256 = "9c6cca226a52d35ce7833fcc4c0f914f6b15b3abe0202e0957ba97ba3bb2cf2c"
SMART_WORKER = 0x1800018E0
PARAM_MATERIALIZE = 0x18000A3D0
PF16_WORKER = 0x180009000
PF16_PIXEL = 0x1800029D0
PF16_FINAL_PIXEL = 0x1800035B0
PF8_WORKER = 0x1800094B0
PF8_PIXEL = 0x180001E00
PF8_FINAL_PIXEL = 0x1800029B0
PF32_WORKER = 0x180009960
PF32_PIXEL = 0x1800035D0
PF32_FINAL_PIXEL = 0x180004170
WIDTH, HEIGHT = 4, 3
PIXEL_BYTES, PADDING = 8, 8
PIXEL_FORMAT = "PF16"


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def fixture(enabled_key: bool = False, key_shape: str = "single") -> tuple[bytes, int]:
    pixel_bytes = 16 if PIXEL_FORMAT == "PF32" else 8 if PIXEL_FORMAT == "PF16" else 4
    rowbytes = WIDTH * pixel_bytes + PADDING
    raw = bytearray([0xA5] * (rowbytes * HEIGHT))
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if PIXEL_FORMAT == "PF32":
                struct.pack_into("<4f", raw, y * rowbytes + x * pixel_bytes,
                                 1.0, 0.125 + x * 0.03125, 0.25 + y * 0.03125, 0.375)
            elif PIXEL_FORMAT == "PF16":
                struct.pack_into("<4H", raw, y * rowbytes + x * pixel_bytes,
                                 32768, 4096 + x * 1024, 8192 + y * 1024, 12288)
            else:
                struct.pack_into("<4B", raw, y * rowbytes + x * pixel_bytes,
                                 255, 32 + (x % 16) * 8, 64 + (y % 16) * 8, 96)
    if enabled_key:
        green_keyed: set[tuple[int, int]] = set()
        if key_shape == "single":
            keyed = {(0, 0)}
        elif key_shape == "center":
            keyed = {(1, 1)}
        elif key_shape == "line":
            keyed = {(x, 0) for x in range(WIDTH)}
        elif key_shape == "all":
            keyed = {(x, y) for y in range(HEIGHT) for x in range(WIDTH)}
        elif key_shape == "practical_multi":
            if WIDTH < 8 or HEIGHT < 8:
                raise ValueError("practical_multi requires at least 8x8")
            keyed = {
                (2, 2), (WIDTH - 3, 2), (2, HEIGHT - 3),
                (WIDTH - 3, HEIGHT - 3),
            }
            keyed.update(
                (x, y)
                for y in range(HEIGHT // 2 - 1, HEIGHT // 2 + 2)
                for x in range(WIDTH // 2 - 1, WIDTH // 2 + 2)
            )
            keyed.update((WIDTH // 4 + x, HEIGHT // 3) for x in range(5))
            green_keyed = {
                (WIDTH // 3, HEIGHT // 2),
                (WIDTH // 3 + 1, HEIGHT // 2),
                (WIDTH * 2 // 3, HEIGHT // 3),
                (WIDTH * 2 // 3, HEIGHT * 2 // 3),
                (WIDTH // 2, HEIGHT // 4),
            }
        else:
            raise ValueError(f"unknown key shape: {key_shape}")
        for x, y in keyed:
            struct.pack_into("<4f" if PIXEL_FORMAT == "PF32" else "<4H" if PIXEL_FORMAT == "PF16" else "<4B", raw,
                             y * rowbytes + x * pixel_bytes,
                             *((1.0, 0.0, 0.0, 0.0) if PIXEL_FORMAT == "PF32" else
                               (32768, 0, 0, 0) if PIXEL_FORMAT == "PF16" else (255, 0, 0, 0)))
        for x, y in green_keyed:
            struct.pack_into("<4f" if PIXEL_FORMAT == "PF32" else "<4H" if PIXEL_FORMAT == "PF16" else "<4B", raw,
                             y * rowbytes + x * pixel_bytes,
                             *((1.0, 0.0, 1.0, 0.0) if PIXEL_FORMAT == "PF32" else
                               (32768, 0, 32768, 0) if PIXEL_FORMAT == "PF16" else (255, 0, 255, 0)))
    return bytes(raw), rowbytes


def parameter_record(enabled_key: bool = False, edge_blur: float = 0.0,
                     edge_blur_direction: int = 2, key_count: int = 1) -> bytes:
    payload = bytearray(0x598)
    struct.pack_into("<i", payload, 0x20, 32 if PIXEL_FORMAT == "PF32" else 16 if PIXEL_FORMAT == "PF16" else 8)
    if enabled_key:
        struct.pack_into("<i", payload, 0x38, key_count)  # number_of_colors
        payload[0x524] = 1  # use_color[0]
        # key RGB at +0x78/+0x7c/+0x80 and threshold at +0x50 remain 0.
        if key_count == 2:
            payload[0x525] = 1  # use_color[1]
            struct.pack_into("<3f", payload, 0x88, 0.0, 1.0, 0.0)
    struct.pack_into("<f", payload, 0x40, edge_blur)
    struct.pack_into("<i", payload, 0x44, 2)  # diagnostic popup value
    struct.pack_into("<i", payload, 0x48, edge_blur_direction)
    return bytes(payload)


def padded_world(loader: AexLoader, raw: bytes, rowbytes: int) -> int:
    payload = loader.bump_alloc(len(raw), align=16)
    loader.write_bytes(payload, raw)
    world = loader.host_alloc(0x50)
    header = bytearray(0x50)
    struct.pack_into("<Q", header, 0x18, payload)
    struct.pack_into("<iii", header, 0x20, rowbytes, WIDTH, HEIGHT)
    struct.pack_into("<4i", header, 0x2C, 0, 0, WIDTH, HEIGHT)
    loader.write_bytes(world, bytes(header))
    return world


def execute_case(aex: Path, enabled_key: bool, edge_blur: float = 0.0,
                 key_shape: str = "single", edge_blur_direction: int = 2,
                 key_count: int = 1) -> dict[str, object]:
    pixel_bytes = 16 if PIXEL_FORMAT == "PF32" else 8 if PIXEL_FORMAT == "PF16" else 4
    bitdepth = 32 if PIXEL_FORMAT == "PF32" else 16 if PIXEL_FORMAT == "PF16" else 8
    worker = PF32_WORKER if PIXEL_FORMAT == "PF32" else PF16_WORKER if PIXEL_FORMAT == "PF16" else PF8_WORKER
    pixel_callback = PF32_PIXEL if PIXEL_FORMAT == "PF32" else PF16_PIXEL if PIXEL_FORMAT == "PF16" else PF8_PIXEL
    final_callback = PF32_FINAL_PIXEL if PIXEL_FORMAT == "PF32" else PF16_FINAL_PIXEL if PIXEL_FORMAT == "PF16" else PF8_FINAL_PIXEL
    iterate_suite_name = "PF iterateFloat Suite" if PIXEL_FORMAT == "PF32" else "PF iterate16 Suite" if PIXEL_FORMAT == "PF16" else "PF Iterate8 Suite"
    digest = sha256(aex.read_bytes())
    if digest != AEX_SHA256:
        raise RuntimeError("pinned AEX hash mismatch")
    # The Iterate16 host shim re-enters Unicorn to execute the guest pixel
    # callback. Full hooks are required for this nested guest call.
    loader = AexLoader(str(aex), verbose=False, fast=False)
    events: list[dict[str, object]] = []
    source, rowbytes = fixture(enabled_key, key_shape)
    output_initial = bytes([0xCC] * len(source))
    input_world = padded_world(loader, source, rowbytes)
    output_world = padded_world(loader, output_initial, rowbytes)
    input_payload = struct.unpack("<Q", loader.read_bytes(input_world + 0x18, 8))[0]
    output_payload = struct.unpack("<Q", loader.read_bytes(output_world + 0x18, 8))[0]

    # Independent direct invocation of the actual PF16 per-pixel callback.
    oracle_record = loader.host_alloc(0x598)
    loader.write_bytes(oracle_record, parameter_record(enabled_key, edge_blur, edge_blur_direction, key_count))
    oracle_output = loader.host_alloc(len(source))
    loader.write_bytes(oracle_output, output_initial)
    pixel_calls = []
    for y in range(HEIGHT):
        for x in range(WIDTH):
            call = loader.call_function(
                pixel_callback,
                int_args=[oracle_record, x, y,
                          input_payload + y * rowbytes + x * pixel_bytes,
                          oracle_output + y * rowbytes + x * pixel_bytes],
                max_instructions=500_000,
            )
            pixel_calls.append(call["rax"])
    oracle_stage1 = loader.read_bytes(oracle_output, len(source))
    final_pixel_calls = []
    for y in range(HEIGHT):
        for x in range(WIDTH):
            call = loader.call_function(
                final_callback,
                int_args=[oracle_record, x, y,
                          input_payload + y * rowbytes + x * pixel_bytes,
                          oracle_output + y * rowbytes + x * pixel_bytes],
                max_instructions=500_000,
            )
            final_pixel_calls.append(call["rax"])
    oracle_actual = loader.read_bytes(oracle_output, len(source))

    def checkout_input(ld: AexLoader, args: list[int]) -> int:
        ld.write_bytes(args[2], struct.pack("<Q", input_world))
        events.append({"callback": "checkout_layer_pixels", "out": hex(input_world)})
        return 0

    def checkout_output(ld: AexLoader, args: list[int]) -> int:
        ld.write_bytes(args[1], struct.pack("<Q", output_world))
        events.append({"callback": "checkout_output", "out": hex(output_world)})
        return 0

    callback_table = loader.host_alloc(0x20)
    loader.write_bytes(callback_table, b"\0" * 0x20)
    loader.write_bytes(callback_table, struct.pack("<Q", loader.install_callback("checkout_layer_pixels", checkout_input)))
    loader.write_bytes(callback_table + 0x10, struct.pack("<Q", loader.install_callback("checkout_output", checkout_output)))
    smart_input = loader.host_alloc(0x40)
    loader.write_bytes(smart_input, b"\0" * 0x40)
    loader.write_bytes(smart_input + 0x2C, struct.pack("<H", bitdepth))
    smart_extra = loader.host_alloc(0x10)
    loader.write_bytes(smart_extra, struct.pack("<2Q", smart_input, callback_table))

    ctx = loader.host_alloc(0x220)
    loader.write_bytes(ctx, b"\0" * 0x220)
    # Distance generators read the host context's horizontal/vertical metric
    # costs at +0x120/+0x128 (FUN_1800066F0 entry).  These are 255 in the
    # bounded actual-AEX context witness; zero silently collapses all seeds.
    metric_cost = 1 if PIXEL_FORMAT == "PF32" else 255
    loader.write_bytes(ctx + 0x120, struct.pack("<i", metric_cost))
    loader.write_bytes(ctx + 0x128, struct.pack("<i", metric_cost))

    def prepare(ld: AexLoader, args: list[int]) -> int:
        source_world, destination_world = args[1], args[2]
        source_payload = struct.unpack("<Q", ld.read_bytes(source_world + 0x18, 8))[0]
        destination_payload = struct.unpack("<Q", ld.read_bytes(destination_world + 0x18, 8))[0]
        source_rowbytes, width, height = struct.unpack("<iii", ld.read_bytes(source_world + 0x20, 12))
        destination_rowbytes = struct.unpack("<i", ld.read_bytes(destination_world + 0x20, 4))[0]
        visible = min(source_rowbytes, destination_rowbytes, width * pixel_bytes)
        for y in range(height):
            ld.write_bytes(destination_payload + y * destination_rowbytes,
                           ld.read_bytes(source_payload + y * source_rowbytes, visible))
        events.append({"callback": "worker_prepare", "args": [hex(value) for value in args],
                       "mode": f"bounded_visible_{PIXEL_FORMAT.lower()}_copy", "bytes": visible * height})
        return 0

    prepare_object = loader.host_alloc(0x48)
    loader.write_bytes(prepare_object, b"\0" * 0x48)
    loader.write_bytes(prepare_object + 0x40, struct.pack("<Q", loader.install_callback("worker_prepare", prepare)))
    loader.write_bytes(ctx + 0xB0, struct.pack("<Q", prepare_object))
    loader.write_bytes(ctx + 0xB8, struct.pack("<Q", ctx))

    def iterate_typed(ld: AexLoader, args: list[int]) -> int:
        rsp = ld.uc.reg_read(UC_X86_REG_RSP)
        rect = struct.unpack("<Q", ld.read_bytes(rsp + 0x28, 8))[0]
        refcon = struct.unpack("<Q", ld.read_bytes(rsp + 0x30, 8))[0]
        callback = struct.unpack("<Q", ld.read_bytes(rsp + 0x38, 8))[0]
        destination = struct.unpack("<Q", ld.read_bytes(rsp + 0x40, 8))[0]
        source_world_arg = args[3]
        source_payload = struct.unpack("<Q", ld.read_bytes(source_world_arg + 0x18, 8))[0]
        destination_payload = struct.unpack("<Q", ld.read_bytes(destination + 0x18, 8))[0]
        source_rowbytes = struct.unpack("<i", ld.read_bytes(source_world_arg + 0x20, 4))[0]
        destination_rowbytes = struct.unpack("<i", ld.read_bytes(destination + 0x20, 4))[0]
        width, height = struct.unpack("<ii", ld.read_bytes(source_world_arg + 0x24, 8))
        if rect:
            left, top, right, bottom = struct.unpack("<4i", ld.read_bytes(rect, 16))
        else:
            left, top, right, bottom = 0, 0, width, height
        if not (0 <= left <= right <= width and 0 <= top <= bottom <= height):
            return 13
        saved = ld.uc.context_save()
        try:
            nested_return = 0x90001000
            try:
                ld.uc.mem_map(nested_return, 0x1000)
            except Exception:
                pass
            for y in range(top, bottom):
                for x in range(left, right):
                    source_pixel = source_payload + y * source_rowbytes + x * pixel_bytes
                    destination_pixel = destination_payload + y * destination_rowbytes + x * pixel_bytes
                    nested_sp = 0xF080000
                    ld.uc.mem_write(nested_sp, struct.pack("<Q", nested_return))
                    ld.uc.mem_write(nested_sp + 0x28, struct.pack("<Q", destination_pixel))
                    ld.uc.reg_write(UC_X86_REG_RSP, nested_sp)
                    for register, value in ((UC_X86_REG_RCX, refcon), (UC_X86_REG_RDX, x),
                                            (UC_X86_REG_R8, y), (UC_X86_REG_R9, source_pixel)):
                        ld.uc.reg_write(register, value)
                    ld.uc.reg_write(UC_X86_REG_RIP, callback)
                    ld.uc.emu_start(callback, nested_return, count=500_000)
        finally:
            ld.uc.context_restore(saved)
        events.append({"callback": "PF_IterateFloat" if PIXEL_FORMAT == "PF32" else "PF_Iterate16" if PIXEL_FORMAT == "PF16" else "PF_Iterate8", "guest_callback": hex(callback),
                       "mode": "bounded_direct_execution_of_native_guest_callback",
                       "calls": (right - left) * (bottom - top),
                       "source_world": hex(source_world_arg), "destination_world": hex(destination),
                       "output_alpha": [(struct.unpack("<f", ld.read_bytes(destination_payload + y * destination_rowbytes + x * pixel_bytes, 4))[0]
                                         if PIXEL_FORMAT == "PF32" else struct.unpack("<H", ld.read_bytes(destination_payload + y * destination_rowbytes + x * pixel_bytes, 2))[0]
                                         if PIXEL_FORMAT == "PF16" else ld.read_bytes(destination_payload + y * destination_rowbytes + x * pixel_bytes, 1)[0])
                                        for y in range(top, bottom) for x in range(left, right)]})
        return 0

    iterate_vtable = loader.host_alloc(0x10)
    loader.write_bytes(iterate_vtable, struct.pack("<Q", loader.install_callback(
        "PF_IterateFloat" if PIXEL_FORMAT == "PF32" else "PF_Iterate16" if PIXEL_FORMAT == "PF16" else "PF_Iterate8", iterate_typed)) + b"\0" * 8)
    allocated_worlds: list[dict[str, int]] = []
    def world_access(ld: AexLoader, args: list[int]) -> int:
        rsp = ld.uc.reg_read(UC_X86_REG_RSP)
        stack_args = struct.unpack("<2Q", ld.read_bytes(rsp + 0x28, 16))
        pixel_format, destination_world = stack_args
        events.append({"callback": "PF_WorldSuite.access", "args": [hex(value) for value in args],
                       "stack_args": [hex(value) for value in stack_args]})
        if pixel_format == 0x36316561:  # 'ae16'
            pixel_bytes = 8
            bitdepth = 16
        elif pixel_format == 0x32336561:  # 'ae32'
            pixel_bytes = 16
            bitdepth = 32
        elif pixel_format in (0x38306561, 0x62677261):  # 'ae08' / 'argb'
            pixel_bytes = 4
            bitdepth = 8
        else:
            return 13
        width, height = args[1], args[2]
        rowbytes = width * pixel_bytes
        payload = ld.host_alloc(rowbytes * height)
        ld.write_bytes(payload, b"\0" * (rowbytes * height))
        header = bytearray(0x50)
        struct.pack_into("<Qiii", header, 0x18, payload, rowbytes, width, height)
        struct.pack_into("<4i", header, 0x2C, 0, 0, width, height)
        struct.pack_into("<H", header, 0x42, bitdepth)
        ld.write_bytes(destination_world, bytes(header))
        allocated_worlds.append({"world": destination_world, "payload": payload,
                                 "rowbytes": rowbytes, "width": width, "height": height,
                                 "pixel_format": pixel_format})
        return 0
    def world_dispose(_ld: AexLoader, args: list[int]) -> int:
        # PF World Suite v2 slot +0x08 is PF_DisposeWorld(effect_ref, world).
        # The additional sampled registers are not arguments; the Windows ABI
        # call site at FUN_180011120 passes RCX/RDX only.
        events.append({"callback": "PF_WorldSuite.dispose", "args": [hex(value) for value in args[:2]]})
        return 0
    world_vtable = loader.host_alloc(0x10)
    loader.write_bytes(world_vtable, struct.pack(
        "<2Q", loader.install_callback("PF_WorldSuite.access", world_access),
        loader.install_callback("PF_WorldSuite.dispose", world_dispose),
    ))
    allocated_handles: list[dict[str, int]] = []
    def new_handle(ld: AexLoader, args: list[int]) -> int:
        requested = args[0]
        if requested <= 0 or requested > 1_000_000:
            return 0
        data = ld.bump_alloc(requested, align=16)
        ld.write_bytes(data, b"\0" * requested)
        handle = ld.bump_alloc(8, align=8)
        ld.write_bytes(handle, struct.pack("<Q", data))
        rsp = ld.uc.reg_read(UC_X86_REG_RSP)
        events.append({"callback": "PF_HandleSuite.new_handle", "size": requested,
                       "return_address": hex(struct.unpack("<Q", ld.read_bytes(rsp, 8))[0]),
                       "handle": hex(handle), "data": hex(data)})
        allocated_handles.append({"handle": handle, "data": data, "size": requested})
        return handle
    def lock_handle(ld: AexLoader, args: list[int]) -> int:
        data = struct.unpack("<Q", ld.read_bytes(args[0], 8))[0]
        events.append({"callback": "PF_HandleSuite.lock_handle", "handle": hex(args[0])})
        return data
    def unlock_handle(_ld: AexLoader, args: list[int]) -> int:
        events.append({"callback": "PF_HandleSuite.unlock_handle", "handle": hex(args[0])})
        return 0
    def dispose_handle(_ld: AexLoader, args: list[int]) -> int:
        events.append({"callback": "PF_HandleSuite.dispose_handle", "handle": hex(args[0])})
        return 0
    handle_vtable = loader.host_alloc(0x30)
    loader.write_bytes(handle_vtable, struct.pack(
        "<6Q", loader.install_callback("PF_HandleSuite.new_handle", new_handle),
        loader.install_callback("PF_HandleSuite.lock_handle", lock_handle),
        loader.install_callback("PF_HandleSuite.unlock_handle", unlock_handle),
        loader.install_callback("PF_HandleSuite.dispose_handle", dispose_handle), 0, 0,
    ))
    def acquire(ld: AexLoader, args: list[int]) -> int:
        name = ld.read_bytes(args[0], 64).split(b"\0", 1)[0].decode("ascii", errors="replace")
        events.append({"callback": "SPBasic.AcquireSuite", "suite": name, "version": args[1]})
        if name == iterate_suite_name and args[1] == 1:
            table = iterate_vtable
        elif name == "PF World Suite" and args[1] == 2:
            table = world_vtable
        elif name == "PF Handle Suite" and args[1] == 2:
            table = handle_vtable
        else:
            return 13
        ld.write_bytes(args[2], struct.pack("<Q", table))
        return 0
    def release(ld: AexLoader, args: list[int]) -> int:
        name = ld.read_bytes(args[0], 64).split(b"\0", 1)[0].decode("ascii", errors="replace")
        events.append({"callback": "SPBasic.ReleaseSuite", "suite": name, "version": args[1]})
        return 0
    basic = loader.host_alloc(0x10)
    loader.write_bytes(basic, struct.pack("<2Q", loader.install_callback("SPBasic.AcquireSuite", acquire), loader.install_callback("SPBasic.ReleaseSuite", release)))
    loader.write_bytes(ctx + 0x180, struct.pack("<Q", basic))
    record_capture: dict[str, object] = {}

    def materialize(ld: AexLoader, _address: int, _size: int) -> None:
        rsp = ld.uc.reg_read(UC_X86_REG_RSP)
        # Windows x64 stack arguments are shifted by the CALL return address:
        # arg5 at +0x28, arg6 (&local_598) at +0x30, arg7 at +0x38.
        record = struct.unpack("<Q", ld.read_bytes(rsp + 0x30, 8))[0]
        payload = parameter_record(enabled_key, edge_blur, edge_blur_direction, key_count)
        # number_of_colors=0, Color Keep=false, Thin=0, Blur=0: every pixel is
        # a non-match and therefore exact passthrough in the native worker.
        ld.write_bytes(record, payload)
        record_capture.update({"address": hex(record), "sha256": sha256(payload)})
        ret = struct.unpack("<Q", ld.read_bytes(rsp, 8))[0]
        ld.uc.reg_write(UC_X86_REG_RSP, rsp + 8)
        ld.uc.reg_write(UC_X86_REG_RAX, 0)
        ld.uc.reg_write(UC_X86_REG_RIP, ret)

    worker_hit_key = "pf32_worker" if PIXEL_FORMAT == "PF32" else "pf16_worker" if PIXEL_FORMAT == "PF16" else "pf8_worker"
    hits = {"smart_worker": 0, worker_hit_key: 0, "parameter_materialize": 0}
    blur_apply_weights: list[float] = []
    blur_apply_source_alpha: list[int] = []
    loader.add_code_hook(SMART_WORKER, lambda _ld, _a, _s: hits.__setitem__("smart_worker", hits["smart_worker"] + 1))
    loader.add_code_hook(worker, lambda _ld, _a, _s: hits.__setitem__(worker_hit_key, hits[worker_hit_key] + 1))
    def capture_blur_weight(ld: AexLoader, _address: int, _size: int) -> None:
        raw = ld.uc.reg_read(UC_X86_REG_XMM1)
        blur_apply_weights.append(struct.unpack("<f", int(raw).to_bytes(16, "little")[:4])[0])
        blur_apply_source_alpha.append(ld.uc.reg_read(UC_X86_REG_RCX) & 0xFFFF)
    loader.add_code_hook(0x18000849B, capture_blur_weight)
    def materialize_hook(ld: AexLoader, address: int, size: int) -> None:
        hits["parameter_materialize"] += 1
        materialize(ld, address, size)
    loader.add_code_hook(PARAM_MATERIALIZE, materialize_hook)

    try:
        call = loader.call_function(SMART_WORKER, int_args=[0, ctx, 0, smart_extra], max_instructions=20_000_000)
    except Exception as exc:
        raise RuntimeError(f"{exc}; events={events!r}; hits={hits!r}; record={record_capture!r}") from exc
    actual = loader.read_bytes(output_payload, len(source))
    temporary_worlds = []
    for item in allocated_worlds:
        payload = ld_payload = item["payload"]
        raw = loader.read_bytes(payload, item["rowbytes"] * item["height"])
        temporary_worlds.append({**{key: hex(value) if key in ("world", "payload", "pixel_format") else value
                                     for key, value in item.items()}, "sha256": sha256(raw),
                                 "first_channel_f32": [struct.unpack("<f", raw[y * item["rowbytes"] + x * (16 if item["pixel_format"] == 0x32336561 else 4 if item["pixel_format"] == 0x62677261 else 8):y * item["rowbytes"] + x * (16 if item["pixel_format"] == 0x32336561 else 4 if item["pixel_format"] == 0x62677261 else 8) + 4])[0]
                                                       for y in range(item["height"]) for x in range(item["width"])],
                                 "alpha16": ([struct.unpack("<H", raw[y * item["rowbytes"] + x * 8:y * item["rowbytes"] + x * 8 + 2])[0]
                                              for y in range(item["height"]) for x in range(item["width"])]
                                             if item["pixel_format"] == 0x36316561 else None)})
    temporary_handles = [{"handle": hex(item["handle"]), "data": hex(item["data"]), "size": item["size"],
                          "f32": list(struct.unpack("<" + "f" * (item["size"] // 4),
                                                    loader.read_bytes(item["data"], item["size"]))) }
                         for item in allocated_handles]
    active_exact = all(
        actual[y * rowbytes:y * rowbytes + WIDTH * pixel_bytes]
        == source[y * rowbytes:y * rowbytes + WIDTH * pixel_bytes]
        for y in range(HEIGHT)
    )
    padding_preserved = all(
        actual[y * rowbytes + WIDTH * pixel_bytes:(y + 1) * rowbytes] == b"\xCC" * PADDING
        for y in range(HEIGHT)
    )
    gates = {
        "normal_return": call["rax"] == 0,
        "exact_dispatch_hits": hits == {"smart_worker": 1, worker_hit_key: 1, "parameter_materialize": 1},
        "checkout_callbacks_exact": [event["callback"] for event in events if str(event["callback"]).startswith("checkout_")] == ["checkout_layer_pixels", "checkout_output"],
        "active_pixels_match_declared_case": (
            (edge_blur != 0.0)
            or (edge_blur == 0.0 and ((not enabled_key and active_exact) or (enabled_key and oracle_actual == actual)))
        ),
        "output_padding_preserved": padding_preserved,
        "direct_actual_pixel_callback_normal_returns": pixel_calls == [0] * (WIDTH * HEIGHT),
        "direct_actual_final_pixel_callback_normal_returns": final_pixel_calls == [0] * (WIDTH * HEIGHT),
        "direct_actual_pixel_callback_matches_worker_output": (
            True if edge_blur != 0.0 else oracle_actual == actual
        ),
        "enabled_key_changes_first_pixel_only": (
            not enabled_key or edge_blur != 0.0 or (
                actual[:pixel_bytes] != source[:pixel_bytes]
                and all(actual[y * rowbytes + x * pixel_bytes:y * rowbytes + (x + 1) * pixel_bytes]
                        == source[y * rowbytes + x * pixel_bytes:y * rowbytes + (x + 1) * pixel_bytes]
                        for y in range(HEIGHT) for x in range(WIDTH) if (x, y) != (0, 0))
            )
        ),
    }
    return {
        "kind": f"olmcolorkey_{PIXEL_FORMAT.lower()}_full_worker_actual_aex_20260805",
        "schema_version": 1,
        "status": "pass" if all(gates.values()) else "diagnostic_mismatch",
        "aex": {"path": str(aex.relative_to(ROOT)), "sha256": digest},
        "case": ((f"enabled_black_key_edge_blur_{edge_blur:g}_{key_shape}" +
                  (f"_direction_{edge_blur_direction}" if edge_blur_direction != 2 else "")) if edge_blur
                 else ("enabled_black_key" if enabled_key else "no_key")),
        "fixture": {"dimensions": [WIDTH, HEIGHT], "pixel_format": PIXEL_FORMAT, "rowbytes": rowbytes,
                    "active_bytes_per_row": WIDTH * pixel_bytes, "padding_bytes_per_row": PADDING},
        "entrypoints": {"smart_worker": hex(SMART_WORKER), "parameter_materialize": hex(PARAM_MATERIALIZE),
                        worker_hit_key: hex(worker), "pixel_callback": hex(pixel_callback),
                        "final_pixel_callback": hex(final_callback)},
        "parameter_record": {**record_capture, "replacement": "fixture-pinned declared record",
                             "enabled_key_count": key_count if enabled_key else 0,
                             "edge_blur_amount": edge_blur,
                             "edge_blur_distance_type": 2,
                             "edge_blur_direction": edge_blur_direction},
        "execution": {"instructions": call["instructions"], "rax": hex(call["rax"]), "hits": hits, "events": events,
                      "temporary_worlds": temporary_worlds, "temporary_handles": temporary_handles,
                      "blur_apply_weights": blur_apply_weights,
                      "blur_apply_source_alpha": blur_apply_source_alpha},
        "captures": {"input_sha256": sha256(source), "output_initial_sha256": sha256(output_initial), "output_actual_sha256": sha256(actual), "direct_actual_pixel_callback_sha256": sha256(oracle_actual),
                     "input_first_pixel_hex": source[:pixel_bytes].hex(), "worker_first_pixel_hex": actual[:pixel_bytes].hex(),
                     "direct_pixel_first_pixel_hex": oracle_actual[:pixel_bytes].hex(),
                     "input_active_rows_hex": [source[y * rowbytes:y * rowbytes + WIDTH * pixel_bytes].hex() for y in range(HEIGHT)],
                     "output_active_rows_hex": [actual[y * rowbytes:y * rowbytes + WIDTH * pixel_bytes].hex() for y in range(HEIGHT)]},
        "acceptance_gates": gates,
        "claim_boundary": f"Actual AEX FUN_1800018E0 bit-depth dispatch and {hex(worker)} {PIXEL_FORMAT} worker with typed checkout worlds plus native typed guest callbacks. AE parameter materialization FUN_18000A3D0 is replaced by the declared fixture record; PF World/Handle/Iterate and worker-prepare operations are bounded host shims. No AE-host or general case0001 exact claim.",
    }


def execute(aex: Path) -> dict[str, object]:
    cases = [execute_case(aex, False), execute_case(aex, True),
             execute_case(aex, True, 1.0, "single"),
             execute_case(aex, True, 1.0, "line"),
             execute_case(aex, True, 1.0, "all"),
             execute_case(aex, True, 2.0, "single"),
             execute_case(aex, True, 1.5, "single"),
             execute_case(aex, True, 0.5, "single"),
             execute_case(aex, True, 2.5, "single"),
             execute_case(aex, True, 3.0, "single"),
             execute_case(aex, True, 3.5, "single"),
             execute_case(aex, True, 4.0, "single"),
             execute_case(aex, True, 2.0, "single", 1),
             execute_case(aex, True, 2.0, "single", 3),
             execute_case(aex, True, 2.0, "single", 4),
             execute_case(aex, True, 2.0, "single", 0),
             execute_case(aex, True, 1.0, "single", 1),
             execute_case(aex, True, 2.0, "center", 2)]
    return {
        "kind": f"olmcolorkey_{PIXEL_FORMAT.lower()}_full_worker_actual_aex_20260805",
        "schema_version": 2,
        "status": "pass" if all(case["status"] == "pass" for case in cases) else "diagnostic_mismatch",
        "aex": cases[0]["aex"],
        "cases": cases,
        "claim_boundary": f"Eighteen bounded actual-AEX {PIXEL_FORMAT} worker cases, including direction-2 Edge Blur amounts 0.5 through 4.0, independent direction-0/1/3/4 amount-2.0 single-key cases, direction-1 amount-1.0, and a separate direction-2 amount-2 center-key geometry; each replaces AE parameter materialization with its declared record and uses bounded host suite shims while independently executing native guest callbacks. No AE-host or general case0001 exact claim.",
    }


def main() -> int:
    global PIXEL_FORMAT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aex", type=Path, default=AEX)
    parser.add_argument("--pixel-format", choices=("PF8", "PF16", "PF32"), default="PF16")
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    PIXEL_FORMAT = args.pixel_format
    if args.json is None:
        args.json = ROOT / f"refs/conformance/olmcolorkey_{PIXEL_FORMAT.lower()}_full_worker_actual_aex_20260805.json"
    try:
        report = execute(args.aex.resolve())
    except Exception as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}, sort_keys=True))
        return 2
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "json": str(args.json)}, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
