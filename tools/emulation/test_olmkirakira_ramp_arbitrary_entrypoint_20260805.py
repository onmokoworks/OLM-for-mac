#!/usr/bin/env python3
"""Exercise OLMKiraKira's PF_Cmd_ARBITRARY_CALLBACK through entry_point."""

from __future__ import annotations

import hashlib
import json
import os
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "aex/OLMKiraKira/Plugins/64/2025/OLMKiraKira.aex"
REPORT = ROOT / "refs/conformance/olmkirakira_ramp_arbitrary_entrypoint_20260805.json"
ENTRY = 0x181155F20
CTOR = 0x1811513A0
MY_EFFECT_VTABLE = 0x18148DB50
RAMP_VTABLE = 0x18148D818
MODE2_MERGE = 0x18114FFD0
UI_STATE_NEW = 0x18123AA70

sys.path.insert(0, str(ROOT / "tools/emulation"))
from aex_loader import AexLoader  # noqa: E402


def main() -> int:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    preallocate = int(os.environ.get("OLM_KK_RAMP_PREALLOCATE", "0"))
    if preallocate:
        loader.host_alloc(preallocate)
    events: list[dict[str, object]] = []
    allocations: dict[int, int] = {}

    def cstr(emu: AexLoader, address: int) -> str:
        out = bytearray()
        while len(out) < 64:
            ch = emu.read_bytes(address + len(out), 1)
            if ch == b"\0":
                break
            out += ch
        return out.decode("ascii")

    def new_handle(emu: AexLoader, args: list[int]) -> int:
        handle = emu.host_alloc(args[0])
        emu.write_bytes(handle, bytes(args[0]))
        allocations[handle] = args[0]
        events.append({"op": "new", "handle": hex(handle), "size": args[0]})
        return handle

    def lock(_emu: AexLoader, args: list[int]) -> int:
        events.append({"op": "lock", "handle": hex(args[0])})
        return args[0]

    def unlock(_emu: AexLoader, args: list[int]) -> int:
        events.append({"op": "unlock", "handle": hex(args[0])})
        return 0

    def dispose(_emu: AexLoader, args: list[int]) -> int:
        events.append({"op": "dispose", "handle": hex(args[0])})
        return 0

    suite = loader.host_alloc(32)
    loader.write_bytes(suite, struct.pack("<4Q",
        loader.install_callback("NewHandle", new_handle),
        loader.install_callback("LockHandle", lock),
        loader.install_callback("UnlockHandle", unlock),
        loader.install_callback("DisposeHandle", dispose)))

    invalidations: list[dict[str, str]] = []
    picker_calls: list[dict[str, object]] = []
    app_suite = loader.host_alloc(0x50)
    loader.write_bytes(app_suite, bytes(0x50))
    picker_output = tuple(float(v) for v in os.environ.get(
        "OLM_KK_RAMP_UI_PICKER_RGBA", "0.25,0.125,0.5,0.875").split(","))

    def color_picker(emu: AexLoader, args: list[int]) -> int:
        before = list(struct.unpack("<4f", emu.read_bytes(args[1], 16)))
        if os.environ.get("OLM_KK_RAMP_UI_PICKER_WRITE", "1") == "1":
            emu.write_bytes(args[3], struct.pack("<4f", *picker_output))
        picker_calls.append({
            "title": cstr(emu, args[0]), "before": before,
            "use_ws_to_monitor": args[2], "after": list(picker_output),
            "input": hex(args[1]), "output": hex(args[3]),
        })
        return int(os.environ.get("OLM_KK_RAMP_UI_PICKER_RESULT", "0"), 0)

    loader.write_bytes(app_suite + 0x38, struct.pack("<Q", loader.install_callback("ColorPickerDialog", color_picker)))
    invalidate_cb = loader.install_callback("PF_InvalidateRect", lambda _emu, args: invalidations.append({"context": hex(args[0]), "rect": hex(args[1])}) or 0)
    loader.write_bytes(app_suite + 0x48, struct.pack("<Q", invalidate_cb))

    def acquire(emu: AexLoader, args: list[int]) -> int:
        name = cstr(emu, args[0])
        selected = app_suite if name == "PF AE App Suite" else suite
        emu.write_bytes(args[2], struct.pack("<Q", selected))
        events.append({"op": "acquire", "name": name, "version": args[1]})
        return 0

    def release(emu: AexLoader, args: list[int]) -> int:
        events.append({"op": "release", "name": cstr(emu, args[0]), "version": args[1]})
        return 0

    provider = loader.host_alloc(16)
    loader.write_bytes(provider, struct.pack("<2Q",
        loader.install_callback("AcquireSuite", acquire),
        loader.install_callback("ReleaseSuite", release)))
    in_data = loader.host_alloc(0x200)
    loader.write_bytes(in_data, bytes(0x200))
    loader.write_bytes(in_data + 0x180, struct.pack("<Q", provider))
    effect = loader.host_alloc(0x260)
    loader.write_bytes(effect, bytes(0x260))
    loader.call_function(CTOR, [effect], max_instructions=300_000)
    loader.write_bytes(effect, struct.pack("<Q", MY_EFFECT_VTABLE))
    assert struct.unpack("<Q", loader.read_bytes(effect + 0x200, 8))[0] == RAMP_VTABLE
    out_data = loader.host_alloc(0x200)
    loader.write_bytes(out_data, bytes(0x200))
    loader.write_bytes(out_data + 0x28, struct.pack("<Q", effect))
    refcon = effect + 0x200

    def arb_call(extra: int) -> int:
        return loader.call_function(ENTRY, [22, in_data, out_data, 0, 0, extra],
                                    max_instructions=1_000_000)["rax"] & 0xFFFFFFFF

    # NEW (selector 0): union.refconPV + union.arbPH.
    arb_out = loader.host_alloc(8)
    loader.write_bytes(arb_out, bytes(8))
    extra = loader.host_alloc(64)
    loader.write_bytes(extra, bytes(64))
    loader.write_bytes(extra, struct.pack("<IhhQQ", 0, 19, 0, refcon, arb_out))
    before = len(events)
    assert arb_call(extra) == 0
    new_events = events[before:]
    source = struct.unpack("<Q", loader.read_bytes(arb_out, 8))[0]
    assert allocations[source] == 0x260
    source_bytes = loader.read_bytes(source, 0x260)
    custom_stops_json = os.environ.get("OLM_KK_RAMP_CUSTOM_STOPS_JSON")
    if custom_stops_json:
        custom_stops = json.loads(custom_stops_json)
        assert 0 < len(custom_stops) <= 16 and all(len(stop) == 5 for stop in custom_stops)
        custom_payload = struct.pack("<I", len(custom_stops)) + b"".join(
            struct.pack("<5f", *stop) for stop in custom_stops)
        loader.write_bytes(source + 16, custom_payload + bytes(0x144 - len(custom_payload)))
        source_bytes = loader.read_bytes(source, 0x260)

    ui_probe = None
    if os.environ.get("OLM_KK_RAMP_UI_PROBE") == "1":
        loader.call_function(UI_STATE_NEW, [refcon, in_data, 0, 0], max_instructions=300_000)
        ui_state_handle = struct.unpack("<Q", loader.read_bytes(refcon + 8, 8))[0]
        parameter_index = 1
        event_results: list[dict[str, object]] = []
        loader.write_bytes(effect + 0xB0 + parameter_index * 8, struct.pack("<Q", refcon))
        param_def = loader.host_alloc(176)
        loader.write_bytes(param_def, bytes(176))
        loader.write_bytes(param_def + 12, struct.pack("<I", 11))
        loader.write_bytes(param_def + 72, struct.pack("<Q", source))
        loader.write_bytes(param_def + 80, struct.pack("<Q", refcon))
        params = loader.host_alloc(16)
        loader.write_bytes(params, struct.pack("<2Q", 0, param_def))

        def ui_event(kind: int, x: int, y: int, last: bool = False, click_count: int = 1) -> None:
            extra_ui = loader.host_alloc(208)
            loader.write_bytes(extra_ui, bytes(208))
            loader.write_bytes(extra_ui + 8, struct.pack("<I", kind))
            loader.write_bytes(extra_ui + 20, struct.pack("<ii", x, y))
            if kind == 2:
                # PF_Event_DO_CLICK click count; 1 maps to Ramp internal event 2
                # (single-click), while any other value maps to event 3.
                loader.write_bytes(extra_ui + 28, struct.pack("<I", click_count))
            loader.write_bytes(extra_ui + 73, bytes([int(last)]))
            loader.write_bytes(extra_ui + 80, struct.pack("<II4i", parameter_index, 2, 0, 0, 310, 170))
            result = loader.call_function(ENTRY, [15, in_data, out_data, params, 0, extra_ui], max_instructions=2_000_000)
            event_results.append({
                "kind": kind, "click_count": click_count, "last": last,
                "rax": result["rax"] & 0xFFFFFFFF,
                "evt_out_flags": struct.unpack("<I", loader.read_bytes(extra_ui + 0xCC, 4))[0],
                "param_change_flags": struct.unpack("<I", loader.read_bytes(param_def, 4))[0],
                "invalidation_count": len(invalidations),
            })

        ui_x = int(os.environ.get("OLM_KK_RAMP_UI_X", "20"))
        ui_y = int(os.environ.get("OLM_KK_RAMP_UI_Y", "30"))
        ui_dx = int(os.environ.get("OLM_KK_RAMP_UI_DX", "40"))
        ui_drag_y = int(os.environ.get("OLM_KK_RAMP_UI_DRAG_Y", str(ui_y)))
        color_probe = os.environ.get("OLM_KK_RAMP_UI_COLOR_PROBE") == "1"
        ui_event(2, ui_x, ui_y)
        if color_probe:
            loader.write_bytes(param_def, struct.pack("<I", 0))
            ui_event(2, ui_x, ui_y, click_count=2)
        else:
            ui_event(3, ui_x + ui_dx, ui_drag_y, True)
        after_ui = loader.read_bytes(source, 0x260)
        count_before = struct.unpack_from("<I", source_bytes, 16)[0]
        count_after = struct.unpack_from("<I", after_ui, 16)[0]
        unpack_stops = lambda blob, count: [list(struct.unpack_from("<5f", blob, 20 + i * 20)) for i in range(count)]
        ui_probe = {
            "ui_state_handle": hex(ui_state_handle),
            "click": [ui_x, ui_y],
            "drag": [ui_x + ui_dx, ui_drag_y],
            "changed_offsets": [i for i, (a, b) in enumerate(zip(source_bytes, after_ui)) if a != b],
            "selected_before_after": [struct.unpack_from("<i", source_bytes, 0x164)[0], struct.unpack_from("<i", after_ui, 0x164)[0]],
            "count_before_after": [count_before, count_after],
            "stops_before": unpack_stops(source_bytes, count_before),
            "stops_after": unpack_stops(after_ui, count_after),
            "invalidations": invalidations,
            "picker_calls": picker_calls,
            "event_results": event_results,
            "ramp_rect_before": list(struct.unpack_from("<4i", source_bytes, 0x154)),
        }
        source_bytes = after_ui

    # FLAT_SIZE (3) and FLATTEN (4).
    size_out = loader.host_alloc(4)
    flat_size_extra = loader.host_alloc(64)
    loader.write_bytes(flat_size_extra, bytes(64))
    loader.write_bytes(flat_size_extra, struct.pack("<IhhQQQ", 3, 19, 0, refcon, source, size_out))
    assert arb_call(flat_size_extra) == 0
    flat_size = struct.unpack("<I", loader.read_bytes(size_out, 4))[0]
    assert flat_size == 0x145
    flat = loader.host_alloc(flat_size)
    flatten_extra = loader.host_alloc(64)
    loader.write_bytes(flatten_extra, bytes(64))
    loader.write_bytes(flatten_extra, struct.pack("<IhhQQI4xQ", 4, 19, 0, refcon, source, flat_size, flat))
    assert arb_call(flatten_extra) == 0
    flat_bytes = loader.read_bytes(flat, flat_size)

    # UNFLATTEN (5), then COMPARE (7).
    def unflatten_blob(blob: bytes) -> int:
        blob_ptr = loader.host_alloc(len(blob))
        loader.write_bytes(blob_ptr, blob)
        restored_out = loader.host_alloc(8)
        unflatten_extra = loader.host_alloc(64)
        loader.write_bytes(unflatten_extra, bytes(64))
        loader.write_bytes(unflatten_extra, struct.pack("<IhhQI4xQQ", 5, 19, 0, refcon, len(blob), blob_ptr, restored_out))
        assert arb_call(unflatten_extra) == 0
        return struct.unpack("<Q", loader.read_bytes(restored_out, 8))[0]

    def compare_handles(left: int, right: int) -> int:
        compare_out = loader.host_alloc(4)
        compare_extra = loader.host_alloc(64)
        loader.write_bytes(compare_extra, bytes(64))
        loader.write_bytes(compare_extra, struct.pack("<IhhQQQQ", 7, 19, 0, refcon, left, right, compare_out))
        assert arb_call(compare_extra) == 0
        return struct.unpack("<I", loader.read_bytes(compare_out, 4))[0]

    restored = unflatten_blob(flat_bytes)
    compare = compare_handles(source, restored)

    count = struct.unpack_from("<I", flat_bytes, 1)[0]
    meaningful_end = 1 + 4 + count * 20
    assert 0 < count <= 16 and meaningful_end == 1 + 4 + count * 20
    canonical = flat_bytes[:meaningful_end] + bytes(flat_size - meaningful_end)
    taint_variants = {
        "canonical_zero": canonical,
        "garbage_a5": flat_bytes[:meaningful_end] + bytes([0xA5]) * (flat_size - meaningful_end),
        "garbage_allocation_pattern": flat_bytes[:meaningful_end] + bytes(
            ((i * 37 + preallocate // 0x100) & 0xFF) for i in range(flat_size - meaningful_end)),
    }
    variant_handles = {name: unflatten_blob(blob) for name, blob in taint_variants.items()}
    variant_compares = {name: compare_handles(source, handle) for name, handle in variant_handles.items()}
    assert all(value == 0 for value in variant_compares.values())

    version_variant_handles = {}
    version_variant_results = {}
    for version in (0, 2, 255):
        blob = bytearray(canonical)
        blob[0] = version
        blob_ptr = loader.host_alloc(len(blob))
        loader.write_bytes(blob_ptr, bytes(blob))
        out = loader.host_alloc(8)
        version_extra = loader.host_alloc(64)
        loader.write_bytes(version_extra, bytes(64))
        loader.write_bytes(version_extra, struct.pack("<IhhQI4xQQ", 5, 19, 0, refcon, len(blob), blob_ptr, out))
        err = arb_call(version_extra)
        handle = struct.unpack("<Q", loader.read_bytes(out, 8))[0]
        version_variant_results[str(version)] = {"err": err, "handle_created": bool(handle)}
        if handle:
            version_variant_handles[str(version)] = handle
            version_variant_results[str(version)]["compare_source"] = compare_handles(source, handle)
    assert version_variant_results == {
        "0": {"err": 0, "handle_created": True, "compare_source": 0},
        "2": {"err": 0, "handle_created": True, "compare_source": 0},
        "255": {"err": 0, "handle_created": True, "compare_source": 0},
    }

    signed_zero_blob = bytearray(canonical)
    signed_zero_blob[5:9] = struct.pack("<f", -0.0)
    signed_zero_handle = unflatten_blob(bytes(signed_zero_blob))
    signed_zero_compare = compare_handles(source, signed_zero_handle)
    if not custom_stops_json and os.environ.get("OLM_KK_RAMP_UI_PROBE") != "1":
        assert signed_zero_compare == 0
    byte_taint_verified_offsets = []
    for offset in range(meaningful_end, flat_size):
        mutated = bytearray(canonical)
        mutated[offset] = 0xA5
        tainted = unflatten_blob(bytes(mutated))
        assert compare_handles(source, tainted) == 0
        d = loader.host_alloc(32)
        loader.write_bytes(d, struct.pack("<IhhQQ", 1, 19, 0, refcon, tainted))
        assert arb_call(d) == 0
        byte_taint_verified_offsets.append(offset)

    def mode2_bits(handle: int) -> list[str]:
        ray_ptrs = []
        mode2_ray = float(os.environ.get("OLM_KK_RAMP_MODE2_RAY", "0.5"))
        for value in (mode2_ray, 0.0, 0.0, 0.0, 0.0):
            pointer = loader.host_alloc(4)
            loader.write_bytes(pointer, struct.pack("<f", value))
            ray_ptrs.append(pointer)
        rays = loader.host_alloc(40)
        loader.write_bytes(rays, struct.pack("<5Q", *ray_ptrs))
        colors = loader.host_alloc(80)
        loader.write_bytes(colors, struct.pack("<20f", *([0.0, 0.25, 0.75, 1.0] * 5)))
        flags = loader.host_alloc(5)
        loader.write_bytes(flags, b"\x01\0\0\0\0")
        ramps = loader.host_alloc(0x144 * 5)
        loader.write_bytes(ramps, loader.read_bytes(handle + 16, 0x144) + bytes(0x144 * 4))
        output = loader.host_alloc(16)
        loader.write_bytes(output, bytes(16))
        loader.call_function(MODE2_MERGE, [0, rays, colors, flags, ramps, 0, output, 1, 1], max_instructions=100_000)
        return [f"0x{x:08x}" for x in struct.unpack("<4I", loader.read_bytes(output, 16))]

    mode2_outputs = {"source": mode2_bits(source)}
    mode2_outputs.update({name: mode2_bits(handle) for name, handle in variant_handles.items()})
    assert len({tuple(value) for value in mode2_outputs.values()}) == 1

    # INTERPOLATE with unequal stop counts is a distinct public-entrypoint
    # branch from the equal-count numeric interpolation below.
    two_stop_blob = bytearray(canonical)
    struct.pack_into("<I", two_stop_blob, 1, 2)
    two_stop_blob[5:25] = flat_bytes[5:25]
    two_stop_blob[25:45] = flat_bytes[45:65]
    two_stop_blob[45:] = bytes(len(two_stop_blob) - 45)
    two_stop = unflatten_blob(bytes(two_stop_blob))

    def interpolate_handles(left: int, right: int, t: float) -> int:
        out = loader.host_alloc(8)
        interp_extra = loader.host_alloc(64)
        loader.write_bytes(interp_extra, bytes(64))
        loader.write_bytes(interp_extra, struct.pack("<IhhQQQdQ", 6, 19, 0, refcon, left, right, t, out))
        assert arb_call(interp_extra) == 0
        return struct.unpack("<Q", loader.read_bytes(out, 8))[0]

    mismatch_interpolated = {
        str(t): interpolate_handles(source, two_stop, t)
        for t in (0.25, 0.5, 0.75)
    }
    mismatch_results = {
        t: {
            "compare_source": compare_handles(handle, source),
            "compare_two_stop": compare_handles(handle, two_stop),
            "count": struct.unpack("<I", loader.read_bytes(handle + 16, 4))[0],
            "active_payload_hex": loader.read_bytes(
                handle + 16, 4 + struct.unpack("<I", loader.read_bytes(handle + 16, 4))[0] * 20).hex(),
        }
        for t, handle in mismatch_interpolated.items()
    }
    mismatch_expected_payloads = {
        "0.25": "03000000000000000000803f0000803f00000000000000008fc2553f0000803f0000803ff4fd3c3f0000803e0000803f0000803f0000803f0000803f0000803f",
        "0.5": "03000000000000000000803f0000803f00000000000000000ad7633f0000803f0000803ff853533f0000003f0000803f0000803f0000803f0000803f0000803f",
        "0.75": "03000000000000000000803f0000803f000000000000000085eb713f0000803f0000803ffca9693f0000403f0000803f0000803f0000803f0000803f0000803f",
    }
    if not custom_stops_json and os.environ.get("OLM_KK_RAMP_UI_PROBE") != "1":
        assert all(
            mismatch_results[t]["active_payload_hex"] == expected and
            mismatch_results[t]["count"] == 3 and
            mismatch_results[t]["compare_source"] == 3 and
            mismatch_results[t]["compare_two_stop"] == 3
            for t, expected in mismatch_expected_payloads.items()
        )

    # COPY (2), INTERPOLATE (6 at t=.5), then DISPOSE (1) all products.
    copied_out = loader.host_alloc(8)
    copy_extra = loader.host_alloc(64)
    loader.write_bytes(copy_extra, bytes(64))
    loader.write_bytes(copy_extra, struct.pack("<IhhQQQ", 2, 19, 0, refcon, source, copied_out))
    assert arb_call(copy_extra) == 0
    copied = struct.unpack("<Q", loader.read_bytes(copied_out, 8))[0]
    interp_out = loader.host_alloc(8)
    interp_extra = loader.host_alloc(64)
    loader.write_bytes(interp_extra, bytes(64))
    loader.write_bytes(interp_extra, struct.pack("<IhhQQQdQ", 6, 19, 0, refcon, source, restored, .5, interp_out))
    assert arb_call(interp_extra) == 0
    interp = struct.unpack("<Q", loader.read_bytes(interp_out, 8))[0]

    # PRINT_SIZE/PRINT/SCAN (8..10) dispatch to the recovered base no-op slots.
    print_size_out = loader.host_alloc(4)
    print_size_extra = loader.host_alloc(64)
    loader.write_bytes(print_size_extra, bytes(64))
    loader.write_bytes(print_size_extra, struct.pack("<IhhQQQ", 8, 19, 0, refcon, source, print_size_out))
    assert arb_call(print_size_extra) == 0
    assert struct.unpack("<I", loader.read_bytes(print_size_out, 4))[0] == 0
    print_extra = loader.host_alloc(64)
    loader.write_bytes(print_extra, bytes(64))
    loader.write_bytes(print_extra, struct.pack("<IhhQ", 9, 19, 0, refcon))
    assert arb_call(print_extra) == 0
    scan_extra = loader.host_alloc(64)
    loader.write_bytes(scan_extra, bytes(64))
    loader.write_bytes(scan_extra, struct.pack("<IhhQ", 10, 19, 0, refcon))
    assert arb_call(scan_extra) == 0

    disposed = []
    for handle in (source, restored, copied, interp, two_stop, signed_zero_handle, *mismatch_interpolated.values(), *variant_handles.values(), *version_variant_handles.values()):
        d = loader.host_alloc(32)
        loader.write_bytes(d, struct.pack("<IhhQQ", 1, 19, 0, refcon, handle))
        assert arb_call(d) == 0
        assert struct.unpack("<Q", loader.read_bytes(d + 16, 8))[0] == 0
        disposed.append(handle)

    assert compare == 0
    assert source_bytes[16:16 + 0x144] == loader.read_bytes(restored + 16, 0x144)
    # The meaningful wire prefix is version + count + active pointer-free records.
    assert len(flat_bytes) == 0x145
    payload_differences = [i for i, (a, b) in enumerate(
        zip(flat_bytes[1:], source_bytes[16:16 + 0x144])) if a != b]
    report = {
        "schema": "olmkirakira-ramp-arbitrary-entrypoint/1",
        "status": "actual_entrypoint_all_selectors_lifecycle_and_canonical_pointer_free_wire_grounded",
        "entry_point": hex(ENTRY),
        "pf_cmd": {"name": "PF_Cmd_ARBITRARY_CALLBACK", "value": 22},
        "id": 19,
        "custom_stops": json.loads(custom_stops_json) if custom_stops_json else None,
        "selector_to_derived_vtable": {
            "0_NEW": "+0x18", "1_DISPOSE": "+0x08", "2_COPY": "+0x20",
            "3_FLAT_SIZE": "+0x38", "4_FLATTEN": "+0x28", "5_UNFLATTEN": "+0x30",
            "6_INTERPOLATE": "+0x48", "7_COMPARE": "+0x40",
            "8_PRINT_SIZE": "+0x50", "9_PRINT": "+0x58", "10_SCAN": "+0x60",
        },
        "executed_selectors": [0, 3, 4, 5, 7, 2, 6, 8, 9, 10, 1],
        "new_events": new_events,
        "ui_probe": ui_probe,
        "handle_size": 0x260,
        "flat_size": flat_size,
        "flat_sha256": hashlib.sha256(flat_bytes).hexdigest(),
        "flat_hex": flat_bytes.hex(),
        "flat_version_byte": flat_bytes[0],
        "pointer_free_payload_sha256": hashlib.sha256(flat_bytes[1:]).hexdigest(),
        "source_inline_difference_offsets": payload_differences,
        "wire_fields": {
            "version": {"offset": 0, "size": 1, "value": flat_bytes[0]},
            "count": {"offset": 1, "size": 4, "value": count},
            "active_records": {"offset": 5, "record_size": 20, "count": count},
            "ignored_tail": {"offset": meaningful_end, "size": flat_size - meaningful_end},
        },
        "canonical_flat_sha256": hashlib.sha256(canonical).hexdigest(),
        "garbage_taint_compare_results": variant_compares,
        "version_byte_unflatten_results": version_variant_results,
        "signed_zero_compare": {
            "left_position_bits": "0x00000000",
            "right_position_bits": "0x80000000",
            "result": signed_zero_compare,
        },
        "byte_taint_verified_ignored_offsets": byte_taint_verified_offsets,
        "mode2_output_bits": mode2_outputs,
        "mismatched_count_interpolation": mismatch_results,
        "roundtrip_compare": compare,
        "preallocated_host_bytes": preallocate,
        "mac_registration": "canonical zero-fill wire accepted; five arbitrary rows and 41 params enabled",
        "disposed_handles": [hex(x) for x in disposed],
        "event_count": len(events),
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PASS_OLMKIRAKIRA_RAMP_ARBITRARY_ENTRYPOINT_20260805 selectors=11 flat=0x145 compare=0 canonical=accepted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
