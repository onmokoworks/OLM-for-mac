#!/usr/bin/env python3
"""Bounded, hash-pinned actual-AEX execution of ColorKey FUN_180009000."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from aex_loader import AexLoader  # noqa: E402
from probe_olmcolorkey_boundary_to_distance_actual_aex_20260716 import alloc, plane  # noqa: E402
from probe_olmcolorkey_edge_blur_apply_aex_20260716 import make_handle_suite  # noqa: E402

AEX_SHA256 = "9c6cca226a52d35ce7833fcc4c0f914f6b15b3abe0202e0957ba97ba3bb2cf2c"
CALLER = 0x180009000
CALLSITE = 0x18000941D
BOUNDARY = 0x180008AD0
DISTANCE = 0x1800058A0
ERODE = 0x180008320
WIDTH, HEIGHT = 5, 1
RECORD = {0x20: 8, 0x24: 1, 0x28: 0, 0x2C: 2, 0x40: -2.0, 0x44: 2, 0x48: 2}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def make_context(loader: AexLoader, events: list[dict]) -> int:
    ctx = loader.host_alloc(0x220)
    loader.write_bytes(ctx, b"\0" * 0x220)
    suite, vtable = make_handle_suite(loader, events)
    # FUN_1800118E0 uses the handle suite for a short-lived processor object;
    # its new-handle call has (constant, 1, out_handle), unlike the leaf's
    # byte-count allocation ABI. Keep the established suite entries and
    # replace only that one entry with this bounded adapter.
    def processor(_loader: AexLoader, args: list[int]) -> int:
        events.append({"callback": "OLMColorKey.processor", "args": [hex(v) for v in args]})
        return 0

    processor_ptr = loader.install_callback("OLMColorKey.processor", processor)
    def caller_new(_loader: AexLoader, args: list[int]) -> int:
        events.append({"callback": "PF_HandleSuite.new_handle.caller", "args": [hex(v) for v in args]})
        if args[2] == 1:
            return 0
        if args[1] == 1 and args[2] >= 0x40000000:
            address = _loader.bump_alloc(0x20, align=16)
            _loader.write_bytes(address, struct.pack("<Q", processor_ptr) + b"\0" * 0x18)
            _loader.write_bytes(args[2], struct.pack("<Q", address))
            return 0
        size = args[0] if 0 < args[0] <= 0x100000 else 0x100
        address = _loader.bump_alloc(size, align=16)
        _loader.write_bytes(address, b"\0" * size)
        events.append({"callback": "PF_HandleSuite.new_handle", "size": size, "result": hex(address)})
        return address
    caller_new_ptr = loader.install_callback("PF_HandleSuite.new_handle.caller", caller_new)
    loader.write_bytes(vtable, struct.pack("<Q", caller_new_ptr))
    loader.write_bytes(ctx + 0x180, struct.pack("<Q", suite))

    # The caller's initial host-side preparation callback is intentionally
    # narrow: it records the ABI and returns PF_Err_NONE.
    def prepare(_loader: AexLoader, args: list[int]) -> int:
        events.append({"callback": "OLMColorKey.prepare", "args": [hex(v) for v in args]})
        return 0

    prepare_ptr = loader.install_callback("OLMColorKey.prepare", prepare)
    callback_object = loader.host_alloc(0x48)
    loader.write_bytes(callback_object, b"\0" * 0x48)
    loader.write_bytes(callback_object + 0x40, struct.pack("<Q", prepare_ptr))
    loader.write_bytes(ctx + 0xB0, struct.pack("<Q", callback_object))
    loader.write_bytes(ctx + 0xB8, struct.pack("<Q", ctx))
    return ctx


def execute(aex_path: Path, amount: float) -> dict[str, object]:
    loader = AexLoader(str(aex_path), verbose=False, fast=True)
    events: list[dict] = []
    hits: dict[str, int] = {"caller_callsite": 0, "boundary": 0, "distance": 0, "erode": 0}
    observations: dict[str, object] = {}

    def hook(label: str):
        def capture(ld: AexLoader, _address: int, _size: int) -> None:
            hits[label] += 1
            def ensure_world(world_ptr: int, pixel_size: int, payload: bytes) -> int:
                payload_ptr = struct.unpack("<Q", ld.read_bytes(world_ptr + 0x18, 8))[0]
                if payload_ptr < 0x20000000 or payload_ptr >= 0x21000000:
                    payload_ptr = alloc(ld, payload)
                    ld.write_bytes(world_ptr + 0x18, struct.pack("<Q", payload_ptr))
                ld.write_bytes(world_ptr + 0x20, struct.pack("<i", WIDTH * pixel_size))
                ld.write_bytes(world_ptr + 0x24, struct.pack("<i", WIDTH))
                ld.write_bytes(world_ptr + 0x28, struct.pack("<i", HEIGHT))
                return payload_ptr
            if label == "boundary":
                ensure_world(ld.uc.reg_read(UC_X86_REG_RCX), 8, source)
                ensure_world(ld.uc.reg_read(UC_X86_REG_RDX), 8, b"\0" * (WIDTH * HEIGHT * 8))
            elif label == "distance":
                ensure_world(ld.uc.reg_read(UC_X86_REG_RDX), 8, b"\0" * (WIDTH * HEIGHT * 8))
                distance_payload_ptr = ensure_world(ld.uc.reg_read(UC_X86_REG_R8), 16, b"\0" * (WIDTH * HEIGHT * 16))
                observations["distance_entry_payload"] = hex(distance_payload_ptr)
                observations["distance_entry_world"] = hex(ld.uc.reg_read(UC_X86_REG_R8))
                observations["distance_before_hex"] = ld.read_bytes(distance_payload_ptr, WIDTH * HEIGHT * 16).hex()
            if label == "caller_callsite":
                rsp = ld.uc.reg_read(UC_X86_REG_RSP)
                outgoing_work_world = struct.unpack("<Q", ld.read_bytes(rsp + 0x20, 8))[0]
                rdx_before_binding = ld.uc.reg_read(UC_X86_REG_RDX)
                # RDX is volatile across FUN_1800058A0. Bind it at the exact
                # native CALL instruction so the ERODE-entry snapshot exposes
                # the complete seam ABI before selected leaf worlds are repaired.
                ld.uc.reg_write(UC_X86_REG_RDX, outgoing_work_world)
                observations["caller_callsite"] = {
                    "RCX": hex(ld.uc.reg_read(UC_X86_REG_RCX)),
                    "RDX_before_binding": hex(rdx_before_binding),
                    "RDX_bound_for_seam": hex(outgoing_work_world),
                    "R8": hex(ld.uc.reg_read(UC_X86_REG_R8)),
                    "R9": hex(ld.uc.reg_read(UC_X86_REG_R9)),
                    "stack5": hex(outgoing_work_world),
                }
            elif label == "distance":
                observations["distance"] = {"XMM3": ld.read_xmm_f32(3)}
            elif label == "erode":
                rsp = ld.uc.reg_read(UC_X86_REG_RSP)
                raw_stack = [struct.unpack("<Q", ld.read_bytes(rsp + offset, 8))[0]
                             for offset in (0x28, 0x30, 0x38)]
                raw = {
                    "RDX_after_callsite_binding": hex(ld.uc.reg_read(UC_X86_REG_RDX)),
                    "R8D_native": ld.uc.reg_read(UC_X86_REG_R8) & 0xFFFFFFFF,
                    "R9_native": hex(ld.uc.reg_read(UC_X86_REG_R9)),
                    "stack5_native": hex(raw_stack[0]),
                    "stack6_native": hex(raw_stack[1]),
                    "stack7_native": hex(raw_stack[2]),
                    "XMM1_native": ld.read_xmm_f32(1),
                }
                distance_world_ptr = raw_stack[1]
                distance_payload_ptr = struct.unpack("<Q", ld.read_bytes(distance_world_ptr + 0x18, 8))[0]
                observations["raw_stack6_world"] = hex(distance_world_ptr)
                observations["raw_stack6_payload"] = hex(distance_payload_ptr)
                observations["distance_before_leaf_hex"] = ld.read_bytes(distance_payload_ptr, WIDTH * HEIGHT * 16).hex()
                ld.uc.reg_write(UC_X86_REG_RDX, source_world)
                ld.uc.reg_write(UC_X86_REG_R9, matched_world)
                for offset, value in ((0x28, source_world), (0x30, distance_world_ptr), (0x38, destination_world)):
                    ld.write_bytes(rsp + offset, struct.pack("<Q", value))
                observations["destination_payload"] = hex(destination_payload)
                observations["destination_before_hex"] = ld.read_bytes(destination_payload, WIDTH * HEIGHT * 8).hex()
                observations["erode"] = {
                    "raw": raw,
                    "repaired": {
                        "RDX": hex(source_world),
                        "R9": hex(matched_world),
                        "stack5": hex(source_world),
                        "stack6": hex(distance_world_ptr),
                        "stack7": hex(destination_world),
                    },
                }
        return capture

    from unicorn.x86_const import UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9, UC_X86_REG_RSP
    loader.add_code_hook(CALLSITE, hook("caller_callsite"))
    loader.add_code_hook(BOUNDARY, hook("boundary"))
    loader.add_code_hook(DISTANCE, hook("distance"))
    loader.add_code_hook(ERODE, hook("erode"))

    source = b"".join(struct.pack("<4H", 32767, 0, 0, 0) for _ in range(WIDTH))
    matched = b"".join(struct.pack("<4H", 12345, 0, 0, 0) for _ in range(WIDTH))
    source_world = plane(loader, WIDTH, HEIGHT, 8, source)
    matched_world = plane(loader, WIDTH, HEIGHT, 8, matched)
    destination_initial = bytes([0xCC] * (WIDTH * HEIGHT * 8))
    destination_payload = alloc(loader, destination_initial)
    destination_world = plane(loader, WIDTH, HEIGHT, 8, destination_initial)
    loader.write_bytes(destination_world + 0x18, struct.pack("<Q", destination_payload))
    record = loader.host_alloc(0x60)
    record_bytes = bytearray(0x60)
    for offset, value in RECORD.items():
        struct.pack_into("<f" if offset == 0x40 else "<i", record_bytes, offset, amount if offset == 0x40 else value)
    loader.write_bytes(record, bytes(record_bytes))
    ctx = make_context(loader, events)
    loader.write_bytes(ctx + 0x40, struct.pack("<f", amount))

    try:
        call = loader.call_function(CALLER, int_args=[ctx, source_world, source_world, matched_world, record], max_instructions=2_000_000)
    except Exception as error:
        raise RuntimeError(f"{error}; events={events!r}; hits={hits!r}") from error
    actual = loader.read_bytes(destination_payload, len(destination_initial))
    distance_before = bytes.fromhex(str(observations["distance_before_leaf_hex"]))
    distance_after = loader.read_bytes(int(observations["raw_stack6_payload"], 16), WIDTH * HEIGHT * 16)
    raw = observations["erode"]["raw"]
    repaired = observations["erode"]["repaired"]
    sentinel_integrity = all(actual[index * 8 + 2:(index + 1) * 8] == b"\xCC" * 6
                             for index in range(WIDTH * HEIGHT))
    invariants = {
        "native_chain_hits_once": hits == {"caller_callsite": 1, "boundary": 1, "distance": 1, "erode": 1},
        "exact_dimensions_5x1": [WIDTH, HEIGHT] == [5, 1],
        "distance_xmm3_4000": observations["distance"]["XMM3"] == 4000.0,
        "bound_rdx_equals_native_stack5": raw["RDX_after_callsite_binding"] == raw["stack5_native"],
        "native_r9_equals_original_r8_source": raw["R9_native"] == hex(source_world),
        "native_stack7_equals_original_r9_matched": raw["stack7_native"] == hex(matched_world),
        "native_stack6_is_exact_distance_world": raw["stack6_native"] == observations["distance_entry_world"],
        "native_r8d_is_2": raw["R8D_native"] == 2,
        "native_xmm1_equals_record_amount": raw["XMM1_native"] == amount,
        "native_and_repaired_stacks_are_distinct": raw["stack5_native"] != repaired["stack5"] and raw["stack7_native"] != repaired["stack7"],
        "distance_identity_preserved": distance_before == distance_after,
        "destination_sentinel_integrity": sentinel_integrity,
    }
    failed = [name for name, passed in invariants.items() if not passed]
    if failed:
        raise RuntimeError("fail-closed: invariant failure: " + ", ".join(failed))
    return {
        "amount": amount,
        "record_amount": amount,
        "status": "pass",
        "returns": {"caller_rax": hex(call["rax"]), "caller_instructions": call["instructions"]},
        "hits": hits,
        "original_arguments": {
            "R8_source_world": hex(source_world),
            "R9_matched_world": hex(matched_world),
        },
        "observations": observations,
        "destination_actual_hex": actual.hex(),
        "destination_initial_hex": destination_initial.hex(),
        "destination_initial_sha256": sha256(destination_initial),
        "destination_actual_sha256": sha256(actual),
        "distance_before_hex": distance_before.hex(),
        "distance_after_hex": distance_after.hex(),
        "distance_identity_preserved": distance_before == distance_after,
        "destination_sentinel_integrity": sentinel_integrity,
        "repaired_leaf_observation": {
            "classification": "observed native leaf output after explicit world repairs; no independent semantic oracle is claimed",
            "actual_hex": actual.hex(),
            "sentinel_integrity": sentinel_integrity,
        },
        "invariants": invariants,
        "suite_callbacks": [event["callback"] for event in events],
    }


def run(aex_path: Path) -> dict[str, object]:
    blob = aex_path.resolve().read_bytes()
    if sha256(blob) != AEX_SHA256:
        raise RuntimeError("fail-closed: pinned AEX SHA-256 mismatch")
    rows = [execute(aex_path.resolve(), -1.0), execute(aex_path.resolve(), -3.0)]
    if any(row["status"] != "pass" for row in rows):
        raise RuntimeError("fail-closed: native caller or requested chain was not reached")
    observed_amounts = [row["observations"]["erode"]["raw"]["XMM1_native"] for row in rows]
    if observed_amounts != [-1.0, -3.0]:
        raise RuntimeError("fail-closed: paired record amounts were not forwarded to raw XMM1")
    return {
        "kind": "olmcolorkey_edge_thin_actual_caller_20260717",
        "schema": 2,
        "status": "pass",
        "classification": "Mac-local bounded Unicorn execution of hash-pinned FUN_180009000 to the native ERODE seam; the harness binds volatile RDX at 0x18000941D and repairs selected worlds after the raw ERODE-entry snapshot before executing the native leaf",
        "provenance": {"aex": str(aex_path.resolve().relative_to(ROOT)), "aex_sha256": sha256(blob), "constant_0x18001f754_float32": 4000.0},
        "fixture": {"dimensions": [WIDTH, HEIGHT], "pixel_format": "PF16", "record": {hex(k): v for k, v in RECORD.items()}},
        "chain": [hex(BOUNDARY), hex(DISTANCE), hex(ERODE)],
        "runs": rows,
        "paired_amount_forwarding": {"amounts": [-1.0, -3.0], "observed_raw_xmm1": observed_amounts, "exact_forwarding": observed_amounts == [-1.0, -3.0]},
        "claim_boundary": "Native FUN_180009000 reaches the ERODE seam and exposes the reported raw ABI after the explicitly reported callsite RDX binding. Selected world arguments are then repaired before native FUN_180008320. This is not untouched full caller-to-leaf execution and makes no AE exact, threshold, full-host, PNG, or general semantic claim.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--aex", type=Path, default=ROOT / "aex/OLMColorKey/Plugins/64/2025/OLMColorKey.aex")
    parser.add_argument("--json", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = run(args.aex)
    except Exception as error:
        print(json.dumps({"status": "blocked", "error": str(error)}, sort_keys=True))
        return 2
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "json": str(args.json)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
