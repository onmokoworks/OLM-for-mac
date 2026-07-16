#!/usr/bin/env python3
"""Follow-up probe for the OLMColorKey Replace + Edge entry callback."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

from unicorn.x86_const import (UC_X86_REG_R8, UC_X86_REG_R9, UC_X86_REG_RAX,
                                UC_X86_REG_RCX, UC_X86_REG_RDI, UC_X86_REG_RDX,
                                UC_X86_REG_RIP, UC_X86_REG_RSP)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_AEX = ROOT / "aex/OLMColorKey/Plugins/64/2025/OLMColorKey.aex"
ORCHESTRATOR = 0x1800094B0
HOOKS = {
    "replacement_write": 0x18000291A,
    "thin_boundary": 0x180009625,
    "blur_boundary": 0x18000983C,
    "blur_apply": 0x1800098CC,
}
AEX_SHA256 = "9c6cca226a52d35ce7833fcc4c0f914f6b15b3abe0202e0957ba97ba3bb2cf2c"
MAX_COPY_BYTES = 1 << 20

sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402


def make_world(loader: AexLoader, width: int, height: int, rowbytes: int, data: bytes) -> tuple[int, int]:
    payload = loader.bump_alloc(len(data), align=64)
    loader.write_bytes(payload, data)
    header = bytearray(0x40)
    struct.pack_into("<Q", header, 0x18, payload)
    struct.pack_into("<i", header, 0x20, rowbytes)
    struct.pack_into("<i", header, 0x24, width)
    struct.pack_into("<i", header, 0x28, height)
    address = loader.host_alloc(len(header), align=16)
    loader.write_bytes(address, bytes(header))
    return address, payload


def bounded_copy(loader: AexLoader, source: int, output: int) -> dict[str, object]:
    """Copy visible rows only; reject malformed or oversized synthetic worlds."""
    source_payload = struct.unpack("<Q", loader.read_bytes(source + 0x18, 8))[0]
    output_payload = struct.unpack("<Q", loader.read_bytes(output + 0x18, 8))[0]
    source_rowbytes = struct.unpack("<i", loader.read_bytes(source + 0x20, 4))[0]
    output_rowbytes = struct.unpack("<i", loader.read_bytes(output + 0x20, 4))[0]
    width, height = struct.unpack("<ii", loader.read_bytes(source + 0x24, 8))
    output_width, output_height = struct.unpack("<ii", loader.read_bytes(output + 0x24, 8))
    visible = min(width * 4, output_width * 4)
    rows = min(height, output_height)
    total = visible * rows
    if min(source_payload, output_payload, source_rowbytes, output_rowbytes, width, height) <= 0:
        raise ValueError("callback world contract is not positive")
    if total > MAX_COPY_BYTES or visible > source_rowbytes or visible > output_rowbytes:
        raise ValueError("callback copy exceeds bounded visible-world contract")
    for row in range(rows):
        data = loader.read_bytes(source_payload + row * source_rowbytes, visible)
        loader.write_bytes(output_payload + row * output_rowbytes, data)
    return {"source_world": hex(source), "output_world": hex(output), "visible_bytes_per_row": visible,
            "rows": rows, "copied_bytes": total}


def make_safe_handle_suite(loader: AexLoader, events: list[dict[str, object]]) -> tuple[int, int]:
    """Model SPBasic dispatch while retaining the proven type-3 HandleSuite slots."""
    suite_tables: dict[str, int] = {}

    def world_suite_call(ld: AexLoader, args: list[int]) -> int:
        events.append({"callback": "PF_WorldSuite", "args": [hex(v) for v in args],
                       "contract": "PF World Suite v2 first slot; bounded host-world access result"})
        return 0

    def world_suite_populate(ld: AexLoader, args: list[int]) -> int:
        source, destination = args[0], args[1]
        events.append({"callback": "PF_WorldSuite.populate", "args": [hex(v) for v in args]})
        if not source or not destination:
            return 1
        # FUN_180011120 supplies the source world and an internal world object.
        # Populate only the proven PF_EffectWorld header/payload fields.
        header = ld.read_bytes(source + 0x18, 0x14)
        ld.write_bytes(destination + 0x18, header)
        return 0

    def iterate8(ld: AexLoader, args: list[int]) -> int:
        rsp = ld.uc.reg_read(UC_X86_REG_RSP)
        rect = struct.unpack("<Q", ld.read_bytes(rsp + 0x28, 8))[0]
        refcon = struct.unpack("<Q", ld.read_bytes(rsp + 0x30, 8))[0]
        callback = struct.unpack("<Q", ld.read_bytes(rsp + 0x38, 8))[0]
        destination = struct.unpack("<Q", ld.read_bytes(rsp + 0x40, 8))[0]
        events.append({"callback": "PF_Iterate8", "args": [hex(v) for v in args],
                       "stack": {"rect": hex(rect), "refcon": hex(refcon),
                                 "callback": hex(callback), "destination_world": hex(destination),
                                 "refcon_words": [hex(v) for v in struct.unpack("<8Q", ld.read_bytes(refcon, 64))] if refcon else [],
                                 "arg0_words": [hex(v) for v in struct.unpack("<8Q", ld.read_bytes(args[0], 64))] if args[0] else []}})
        if not rect or not destination:
            return 1
        left, top, right, bottom = struct.unpack("<4i", ld.read_bytes(rect, 16))
        source = args[3]
        sw, sh = struct.unpack("<ii", ld.read_bytes(source + 0x24, 8))
        dw, dh = struct.unpack("<ii", ld.read_bytes(destination + 0x24, 8))
        if dw <= 0 or dh <= 0:
            payload = ld.bump_alloc(sw * sh * 4, align=16)
            world_header = bytearray(0x14)
            struct.pack_into("<Q", world_header, 0, payload)
            struct.pack_into("<i", world_header, 8, sw * 4)
            struct.pack_into("<i", world_header, 12, sw)
            struct.pack_into("<i", world_header, 16, sh)
            ld.write_bytes(destination + 0x18, bytes(world_header))
            dw, dh = sw, sh
        srow = struct.unpack("<i", ld.read_bytes(source + 0x20, 4))[0]
        drow = struct.unpack("<i", ld.read_bytes(destination + 0x20, 4))[0]
        if not (0 <= left <= right <= sw and 0 <= top <= bottom <= sh and
                right <= dw and bottom <= dh):
            events[-1]["mode"] = "pass_through_uninspectable"
            return 0
        width_bytes = (right - left) * 4
        if width_bytes * (bottom - top) > MAX_COPY_BYTES:
            return 1
        sp = struct.unpack("<Q", ld.read_bytes(source + 0x18, 8))[0]
        dp = struct.unpack("<Q", ld.read_bytes(destination + 0x18, 8))[0]
        if callback == 0x180001E00:
            # FUN_180001e00 reads this compact Replace+Key state from its
            # Iterate8 refcon. These fields are the exact predicates used by
            # 0x1800028d3..0x1800028eb before the replacement write.
            ld.write_bytes(refcon + 0x30, struct.pack("<i", 2))
            ld.write_bytes(refcon + 0x38, struct.pack("<i", 1))
            ld.write_bytes(refcon + 0x24, b"\1")
            ld.write_bytes(refcon + 0x4d, b"\1")
            ld.write_bytes(refcon + 0x53d, b"\1")
            ld.write_bytes(refcon + 0x524, b"\1")
            ld.write_bytes(refcon + 0x20, struct.pack("<i", 255))
            ld.write_bytes(refcon + 0x50, struct.pack("<f", 1.0))
            ld.write_bytes(refcon + 0x54, struct.pack("<f", 0.0))
            ld.write_bytes(refcon + 0x7c, struct.pack("<4f", 1.0, 0.0, 0.0, 1.0))
            ld.write_bytes(refcon + 0x208, struct.pack("<f", 0.0))
            ld.write_bytes(refcon + 0x20c, struct.pack("<f", 0.0))
            ld.write_bytes(refcon + 0x210, struct.pack("<f", 1.0))
            saved = ld.uc.context_save()
            try:
                nested_return = 0x90001000
                try:
                    ld.uc.mem_map(nested_return, 0x1000)
                except Exception:
                    pass
                for y in range(top, bottom):
                    for x in range(left, right):
                        source_pixel = sp + y * srow + x * 4
                        destination_pixel = dp + y * drow + x * 4
                        nested_sp = 0xF080000
                        ld.uc.mem_write(nested_sp, struct.pack("<Q", nested_return))
                        ld.uc.mem_write(nested_sp + 0x28, struct.pack("<Q", destination_pixel))
                        ld.uc.reg_write(UC_X86_REG_RSP, nested_sp)
                        for register, value in ((UC_X86_REG_RCX, refcon),
                                                (UC_X86_REG_RDX, x),
                                                (UC_X86_REG_R8, y),
                                                (UC_X86_REG_R9, source_pixel)):
                            ld.uc.reg_write(register, value)
                        ld.uc.reg_write(UC_X86_REG_RIP, callback)
                        ld.uc.emu_start(callback, nested_return, count=300_000)
            finally:
                ld.uc.context_restore(saved)
            events[-1]["guest_callback_calls"] = (right - left) * (bottom - top)
        for y in range(top, bottom):
            data = ld.read_bytes(sp + y * srow + left * 4, width_bytes)
            ld.write_bytes(dp + y * drow + left * 4, data)
        events[-1]["bounded_pass_through"] = {"area": [left, top, right, bottom],
                                               "copied_bytes": width_bytes * (bottom - top)}
        return 0

    def acquire(ld: AexLoader, args: list[int]) -> int:
        name = ld.read_bytes(args[0], 64).split(b"\0", 1)[0].decode("ascii", errors="replace")
        table = suite_tables.get(name)
        events.append({"callback": "SPBasic.AcquireSuite", "args": [hex(v) for v in args],
                       "suite_name": name, "table": hex(table) if table else None})
        if table is None:
            return 1
        ld.write_bytes(args[2], struct.pack("<Q", table))
        return 0

    def release(_ld: AexLoader, args: list[int]) -> int:
        events.append({"callback": "PF_HandleSuite.release_suite", "args": [hex(v) for v in args]})
        return 0

    def new_handle(ld: AexLoader, args: list[int]) -> int:
        requested = args[0]
        size = requested if 0 < requested <= MAX_COPY_BYTES else 0x100
        address = ld.bump_alloc(size, align=16)
        ld.write_bytes(address, b"\0" * size)
        events.append({"callback": "PF_HandleSuite.new_handle", "requested_size": requested,
                       "size": size, "result": hex(address)})
        return address

    def lock(ld: AexLoader, args: list[int]) -> int:
        events.append({"callback": "PF_HandleSuite.lock_handle", "handle": hex(args[0])})
        return args[0]

    def unlock(_ld: AexLoader, args: list[int]) -> int:
        events.append({"callback": "PF_HandleSuite.unlock_handle", "handle": hex(args[0])})
        return 0

    def dispose(_ld: AexLoader, args: list[int]) -> int:
        events.append({"callback": "PF_HandleSuite.dispose_handle", "handle": hex(args[0])})
        return 0

    acquire_ptr = loader.install_callback("SPBasic.AcquireSuite", acquire)
    release_ptr = loader.install_callback("SPBasic.ReleaseSuite", release)
    new_ptr = loader.install_callback("PF_HandleSuite.new_handle", new_handle)
    lock_ptr = loader.install_callback("PF_HandleSuite.lock_handle", lock)
    unlock_ptr = loader.install_callback("PF_HandleSuite.unlock_handle", unlock)
    dispose_ptr = loader.install_callback("PF_HandleSuite.dispose_handle", dispose)
    vtable_address = loader.bump_alloc(0x30, align=16)
    loader.write_bytes(vtable_address, struct.pack("<6Q", new_ptr, lock_ptr, unlock_ptr, dispose_ptr, 0, 0))
    iterate_ptr = loader.install_callback("PF_Iterate8", iterate8)
    iterate_table = loader.bump_alloc(8, align=8)
    loader.write_bytes(iterate_table, struct.pack("<Q", iterate_ptr))
    world_ptr = loader.install_callback("PF_WorldSuite", world_suite_call)
    world_populate_ptr = loader.install_callback("PF_WorldSuite.populate", world_suite_populate)
    world_table = loader.bump_alloc(0x10, align=8)
    loader.write_bytes(world_table, struct.pack("<2Q", world_ptr, world_populate_ptr))
    suite_tables["PF Handle Suite"] = vtable_address
    suite_tables["PF Iterate8 Suite"] = iterate_table
    suite_tables["PF World Suite"] = world_table
    suite = loader.bump_alloc(0x18, align=16)
    loader.write_bytes(suite, struct.pack("<3Q", acquire_ptr, release_ptr, vtable_address))
    vtable = {"value": vtable_address}
    return suite, vtable_address


def run(aex_path: Path) -> dict[str, object]:
    digest = hashlib.sha256(aex_path.read_bytes()).hexdigest()
    if digest != AEX_SHA256:
        return {"status": "blocked", "reason": "AEX SHA-256 mismatch", "binary_sha256": digest,
                "expected_sha256": AEX_SHA256}

    loader = AexLoader(str(aex_path), verbose=False, fast=False)
    width = height = 5
    source_bytes = bytes([255, 0, 255, 0] * (width * height))
    source_bytes = source_bytes[:(2 * width + 2) * 4] + bytes([255, 255, 0, 0]) + source_bytes[(2 * width + 3) * 4:]
    output_bytes = bytes([0xCC] * len(source_bytes))
    source_world, source_payload = make_world(loader, width, height, width * 4, source_bytes)
    output_world, output_payload = make_world(loader, width, height, width * 4, output_bytes)
    params = loader.host_alloc(0x400)
    loader.write_bytes(params, b"\0" * 0x400)
    loader.write_bytes(params + 0x2c, struct.pack("<4i", 0, 0, width, height))
    # FUN_1800085b0 later uses its params-derived object as a PF_EffectWorld:
    # 0x18 payload, 0x20 rowbytes, 0x24 width, 0x28 height.  Populate only
    # those fields from the already valid source-world contract.
    loader.write_bytes(params + 0x18, struct.pack("<Qiii", source_payload,
                                                    width * 4, width, height))
    config = loader.host_alloc(0x60)
    config_bytes = bytearray(0x60)
    # R14 is the fifth entry argument: edge amounts/types/direction.
    struct.pack_into("<i", config_bytes, 0x20, 2)  # thin amount
    struct.pack_into("<i", config_bytes, 0x28, 1)  # thin distance type
    struct.pack_into("<f", config_bytes, 0x40, 2.0)  # blur amount
    struct.pack_into("<i", config_bytes, 0x44, 1)  # blur distance type
    struct.pack_into("<i", config_bytes, 0x48, 0)  # Around
    loader.write_bytes(config, bytes(config_bytes))

    context = loader.host_alloc(0x400)
    loader.write_bytes(context, b"\0" * 0x400)
    # Proven type-3 distance context state from the bounded leaf witness.
    loader.write_bytes(context + 0x120, struct.pack("<i", 255))
    loader.write_bytes(context + 0x128, struct.pack("<i", 255))
    events: list[dict[str, object]] = []
    callback_copies: list[dict[str, object]] = []
    suite, vtable = make_safe_handle_suite(loader, events)
    loader.write_bytes(context + 0x180, struct.pack("<Q", suite))

    def orchestration_callback(ld: AexLoader, args: list[int]) -> int:
        rsp = ld.uc.reg_read(UC_X86_REG_RSP)
        stack_arg5 = struct.unpack("<Q", ld.read_bytes(rsp + 0x28, 8))[0]
        event = {"callback": "OLMColorKey.replace_edge", "args": [hex(v) for v in args],
                 "stack_arg5": hex(stack_arg5), "order": len(callback_copies) + 1}
        events.append(event)
        try:
            copy = bounded_copy(ld, source_world, args[1])
        except ValueError as error:
            # The second call uses an AEX stack-built temporary world. If its
            # visible payload contract is not inspectable, pass through and
            # let the native stage own that temporary's lifetime.
            copy = {"mode": "pass_through", "reason": str(error),
                    "output_world": hex(args[1])}
        event["copy"] = copy
        callback_copies.append(copy)
        return 0  # PF_Err_NONE

    callback = loader.install_callback("OLMColorKey.replace_edge", orchestration_callback)
    callback_object = loader.host_alloc(0x48)
    loader.write_bytes(callback_object, b"\0" * 0x48)
    loader.write_bytes(callback_object + 0x40, struct.pack("<Q", callback))
    loader.write_bytes(context + 0xb0, struct.pack("<Q", callback_object))
    loader.write_bytes(context + 0xb8, struct.pack("<Q", source_world))

    stage_events: list[str] = []
    host_world_events: list[dict[str, object]] = []
    predicate_events: list[dict[str, object]] = []
    blur_world_diagnostics: list[dict[str, object]] = []
    for label, address in HOOKS.items():
        loader.add_code_hook(address, lambda _ld, _addr, _size, label=label: stage_events.append(label))

    def materialize_distance_world(ld: AexLoader, _address: int, _size: int) -> None:
        # FUN_180006e20 consumes the temporary world at RDX. The standalone
        # PF World Suite scaffold cannot own that stack object, so materialize
        # only its proven PF_EffectWorld header from the callback refcon.
        from unicorn.x86_const import UC_X86_REG_R8, UC_X86_REG_RDX
        destination = ld.uc.reg_read(UC_X86_REG_RDX)
        output = ld.uc.reg_read(UC_X86_REG_R8)
        header = ld.read_bytes(source_world + 0x18, 0x14)
        ld.write_bytes(destination + 0x18, header)
        output_payload = ld.bump_alloc(width * height * 16, align=16)
        output_header = bytearray(0x14)
        struct.pack_into("<Q", output_header, 0, output_payload)
        struct.pack_into("<i", output_header, 8, width * 16)
        struct.pack_into("<i", output_header, 12, width)
        struct.pack_into("<i", output_header, 16, height)
        ld.write_bytes(output + 0x18, bytes(output_header))
        host_world_events.append({"hook": "FUN_180006e20.entry", "temporary_world": hex(destination),
                                  "output_world": hex(output), "source_world": hex(source_world),
                                  "copied_header_bytes": len(header), "output_payload": hex(output_payload)})

    loader.add_code_hook(0x180006E20, materialize_distance_world)

    def materialize_blur_worlds(ld: AexLoader, _address: int, _size: int) -> None:
        def ensure_world(address: int) -> dict[str, object]:
            width_value = struct.unpack("<i", ld.read_bytes(address + 0x24, 4))[0]
            height_value = struct.unpack("<i", ld.read_bytes(address + 0x28, 4))[0]
            if width_value <= 0 or height_value <= 0:
                width_value, height_value = width, height
                payload = ld.bump_alloc(width_value * height_value * 4, align=16)
                header = bytearray(0x14)
                struct.pack_into("<Q", header, 0, payload)
                struct.pack_into("<i", header, 8, width_value * 4)
                struct.pack_into("<i", header, 12, width_value)
                struct.pack_into("<i", header, 16, height_value)
                ld.write_bytes(address + 0x18, bytes(header))
                return {"world": hex(address), "payload": hex(payload), "width": width_value,
                        "height": height_value}
            return {"world": hex(address), "existing": True}

        source_address = ld.uc.reg_read(UC_X86_REG_RCX)
        destination_address = ld.uc.reg_read(UC_X86_REG_RDX)
        host_world_events.append({"hook": "FUN_180008c90.entry",
                                  "source": ensure_world(source_address),
                                  "destination": ensure_world(destination_address)})

    loader.add_code_hook(0x180008C90, materialize_blur_worlds)

    def capture_blur_apply_worlds(ld: AexLoader, _address: int, _size: int) -> None:
        # FUN_1800085b0 calls PF_WorldSuite row access at 0x1800113c0.  Record
        # the exact world pointers it derives before any repair is attempted.
        rsp = ld.uc.reg_read(UC_X86_REG_RSP)
        words = {}
        for offset in (0x20, 0x28, 0x30, 0x38, 0x40, 0x48):
            address = rsp + offset
            words[hex(offset)] = hex(struct.unpack("<Q", ld.read_bytes(address, 8))[0])

        def world_header(address: int) -> dict[str, object]:
            if not address:
                return {"address": hex(address), "valid": False}
            try:
                payload, rowbytes, world_width, world_height = struct.unpack(
                    "<Qiii", ld.read_bytes(address + 0x18, 0x14))
                return {"address": hex(address), "payload": hex(payload),
                        "rowbytes": rowbytes, "width": world_width, "height": world_height}
            except Exception as error:
                return {"address": hex(address), "valid": False, "error": str(error)}

        blur_world_diagnostics.append({
            "hook": "FUN_1800085b0.entry",
            "rcx_context": hex(ld.uc.reg_read(UC_X86_REG_RCX)),
            "rdx_temporary": world_header(ld.uc.reg_read(UC_X86_REG_RDX)),
            "r9_world": world_header(ld.uc.reg_read(UC_X86_REG_R9)),
            "stack_words": words,
        })

    loader.add_code_hook(0x1800085B0, capture_blur_apply_worlds)

    def capture_replace_predicate(ld: AexLoader, _address: int, _size: int) -> None:
        rdi = ld.uc.reg_read(UC_X86_REG_RDI)
        rax = ld.uc.reg_read(UC_X86_REG_RAX) & 0xFFFFFFFF
        predicate_events.append({"hook": "0x1800028aa", "refcon": hex(rdi), "hit_index": rax,
                                 "enable_replace": ld.read_bytes(rdi + 0x4d, 1)[0],
                                 "use_replace_index0": ld.read_bytes(rdi + 0x53d, 1)[0],
                                 "color_keep_gate": ld.read_bytes(rdi + 0x24, 1)[0]})

    loader.add_code_hook(0x1800028AA, capture_replace_predicate)

    result: dict[str, object] = {"status": "blocked", "entry": hex(ORCHESTRATOR)}
    try:
        call = loader.call_function(ORCHESTRATOR,
                                    int_args=[context, source_world, output_world, params, config],
                                    max_instructions=2_000_000)
        result.update({"status": "pass", "rax": hex(call["rax"]), "instructions": call["instructions"]})
    except Exception as error:
        result["error"] = f"{type(error).__name__}: {error}"
    stage_order = list(dict.fromkeys(stage_events))
    result.update({
        "binary_sha256": digest, "expected_sha256": AEX_SHA256,
        "callback_contract": "callback(refcon, output_world, params, 0, 0) -> PF_Err",
        "callback_object": {"ctx_plus_b0": hex(callback_object), "callback_slot": hex(callback),
                             "ctx_plus_b8_refcon": hex(source_world)},
        "handle_suite": {"ctx_plus_180": hex(suite), "vtable": hex(vtable), "type": 3},
        "callback_events": events, "stage_events": stage_events,
        "stage_order": stage_order,
        "host_world_events": host_world_events,
        "blur_world_diagnostics": blur_world_diagnostics,
        "replace_predicate_events": predicate_events,
        "diagnostics": {
            "next_blocker": result.get("error"),
            "last_callback": events[-1] if events else None,
            "stage_hooks_observed": bool(stage_events),
            "cleanup_observed": any(item.get("callback") == "PF_HandleSuite.release_suite" for item in events),
        },
        "output_matches_source": loader.read_bytes(output_payload, len(output_bytes)) == source_bytes,
        "cleanup_observed": any(item.get("callback") == "PF_HandleSuite.release_suite" for item in events),
        "required_stage_order": ["replacement_write", "thin_boundary", "blur_boundary", "blur_apply"],
        "scope": "Mac-local Unicorn follow-up against hash-pinned checked-in Windows PE; next-stage classification only, not AE exact",
    })
    required_stage_order = ["replacement_write", "thin_boundary", "blur_boundary", "blur_apply"]
    result["status"] = (
        "pass" if result["status"] == "pass"
        and stage_order == required_stage_order
        and result["cleanup_observed"]
        and not result.get("error")
        else "blocked"
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--aex", type=Path, default=DEFAULT_AEX)
    parser.add_argument("--json", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.aex)
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "json": str(args.json),
                      "stage_events": report.get("stage_events", [])}, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
