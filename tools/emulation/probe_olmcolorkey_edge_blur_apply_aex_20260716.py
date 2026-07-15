#!/usr/bin/env python3
"""Small PF Handle Suite shim harness for ColorKey Edge Blur apply."""

from __future__ import annotations

import argparse
import json
import re
import struct
import sys
from pathlib import Path
from unicorn.x86_const import UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9

sys.path.insert(0, str(Path(__file__).resolve().parent))
from aex_loader import AexLoader  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_AEX = ROOT / "aex/OLMColorKey/Plugins/64/2025/OLMColorKey.aex"
APPLY = 0x1800085B0
WEIGHT = 0x1800049A0


def alloc(loader: AexLoader, data: bytes, align: int = 16) -> int:
    address = loader.bump_alloc(len(data), align=align)
    loader.write_bytes(address, data)
    return address


def world(loader: AexLoader, width: int, height: int, pixel_size: int, data: bytes) -> tuple[int, int]:
    payload = alloc(loader, data, align=64)
    header = bytearray(0x30)
    struct.pack_into("<Q", header, 0x18, payload)
    struct.pack_into("<i", header, 0x20, width * pixel_size)
    struct.pack_into("<i", header, 0x24, width)
    struct.pack_into("<i", header, 0x28, height)
    return alloc(loader, bytes(header)), payload


def make_handle_suite(loader: AexLoader, events: list[dict]) -> tuple[int, int]:
    """Install the narrow PF_HandleSuite surface used by FUN_18000a250."""

    handle_size = {"last": 0}

    def acquire(_loader: AexLoader, args: list[int]) -> int:
        events.append({"callback": "PF_HandleSuite.acquire", "args": [hex(v) for v in args]})
        # out-param is RCX/RDX/R8 in the Windows ABI call made by the AEX.
        vtable = suite_ptr["value"]
        _loader.write_bytes(args[2], struct.pack("<Q", vtable))
        return 0

    def suite_new(_loader: AexLoader, args: list[int]) -> int:
        size = args[0]
        handle_size["last"] = size
        address = _loader.bump_alloc(size, align=16)
        _loader.write_bytes(address, b"\0" * size)
        events.append({"callback": "PF_HandleSuite.new_handle", "size": size, "result": hex(address)})
        return address

    def suite_lock(_loader: AexLoader, args: list[int]) -> int:
        events.append({"callback": "PF_HandleSuite.lock_handle", "handle": hex(args[0])})
        return args[0]

    def suite_unlock(_loader: AexLoader, args: list[int]) -> int:
        events.append({"callback": "PF_HandleSuite.unlock_handle", "handle": hex(args[0])})
        return 0

    def suite_dispose(_loader: AexLoader, args: list[int]) -> int:
        events.append({"callback": "PF_HandleSuite.dispose_handle", "handle": hex(args[0])})
        return 0

    def release(_loader: AexLoader, args: list[int]) -> int:
        events.append({"callback": "PF_HandleSuite.release_suite", "args": [hex(v) for v in args]})
        return 0

    acquire_ptr = loader.install_callback("PF_HandleSuite.acquire", acquire)
    release_ptr = loader.install_callback("PF_HandleSuite.release_suite", release)
    new_ptr = loader.install_callback("PF_HandleSuite.new_handle", suite_new)
    lock_ptr = loader.install_callback("PF_HandleSuite.lock_handle", suite_lock)
    unlock_ptr = loader.install_callback("PF_HandleSuite.unlock_handle", suite_unlock)
    dispose_ptr = loader.install_callback("PF_HandleSuite.dispose_handle", suite_dispose)

    vtable = alloc(loader, struct.pack("<6Q", new_ptr, lock_ptr, unlock_ptr, dispose_ptr, 0, 0))
    suite = alloc(loader, struct.pack("<3Q", acquire_ptr, release_ptr, vtable))
    # The AEX expects ctx+0x180 to point directly at the acquire/release object.
    # AcquireSuite returns the suite vtable; ctx+0x180 remains the host-side
    # acquire/release descriptor used to obtain it.
    suite_ptr = {"value": vtable}
    return suite, vtable


def read_rip(error: Exception) -> str | None:
    match = re.search(r"RIP=0x([0-9a-fA-F]+)", str(error))
    return f"0x{match.group(1).lower()}" if match else None


def run(aex_path: Path, direction: int = 1) -> dict:
    loader = AexLoader(str(aex_path), verbose=False, fast=True)
    width, height = 4, 2
    # ARGB bytes: target writes one byte per destination pixel; retaining all
    # bytes makes accidental world/stride confusion visible in the witness.
    source_bytes = bytes([255, 10, 20, 30, 255, 40, 50, 60, 255, 70, 80, 90, 255, 100, 110, 120,
                          255, 130, 140, 150, 255, 160, 170, 180, 255, 190, 200, 210, 255, 220, 230, 240])
    boundary_bytes = bytes([255, 0, 255, 0, 255, 255, 0, 255])
    distance_values = [0.0, 1.0, 2.0, 3.0, 1.0, 2.0, 3.0, 4.0]
    distance_bytes = struct.pack("<%df" % (width * height * 4), *[v for v in distance_values for _ in range(4)])
    destination_bytes = bytes([0xCC] * (width * height * 4))
    source_world, source_payload = world(loader, width, height, 4, source_bytes)
    boundary_world, boundary_payload = world(loader, width, height, 4, boundary_bytes)
    distance_world, distance_payload = world(loader, width, height, 16, distance_bytes)
    destination_world, destination_payload = world(loader, width, height, 4, destination_bytes)

    ctx = loader.host_alloc(0x200)
    loader.write_bytes(ctx, b"\0" * 0x200)
    events: list[dict] = []
    suite, vtable = make_handle_suite(loader, events)
    loader.write_bytes(ctx + 0x180, struct.pack("<Q", suite))

    # Direction 1 selects FUN_1800049a0 inside the apply helper.
    result: dict[str, object] = {"status": "blocked", "direction": direction}
    try:
        call = loader.call_function(
            APPLY,
            # Keep unused GP slots explicit: RCX=ctx, RDX=unused, R8=direction,
            # R9=source bytes, then boundary/distance/destination are 5th-7th.
            int_args=[ctx, 0, direction, source_world, boundary_world, distance_world, destination_world, 0],
            float_args={1: 4.0},
            max_instructions=1_000_000,
        )
        result.update({
            "status": "pass",
            "rax": hex(call["rax"]),
            "instructions": call["instructions"],
            "destination_bytes": list(loader.read_bytes(destination_payload, len(destination_bytes))),
        })
    except Exception as error:  # retain exact ABI boundary for the report
        result.update({
            "error": str(error),
            "deepest_rip": read_rip(error),
            "fault_registers": {
                name: hex(loader.uc.reg_read(reg))
                for name, reg in (("RCX", UC_X86_REG_RCX), ("RDX", UC_X86_REG_RDX),
                                  ("R8", UC_X86_REG_R8), ("R9", UC_X86_REG_R9))
            },
        })

    result.update({
        "target": {"va": hex(APPLY), "name": "FUN_1800085b0"},
        "independent_weight": {"va": hex(WEIGHT), "name": "FUN_1800049a0"},
        "worlds": {
            "source": {"ptr": hex(source_world), "payload": hex(source_payload), "bytes": list(source_bytes)},
            "boundary": {"ptr": hex(boundary_world), "payload": hex(boundary_payload), "bytes": list(boundary_bytes)},
            "distance": {"ptr": hex(distance_world), "payload": hex(distance_payload), "values": distance_values},
            "destination": {"ptr": hex(destination_world), "payload": hex(destination_payload),
                             "initial_bytes": list(destination_bytes)},
        },
        "shim": {"suite": hex(suite), "vtable": hex(vtable), "events": events,
                 "callbacks_seen": [item["callback"] for item in events]},
        "cleanup_observed": any(item["callback"] == "PF_HandleSuite.release_suite" for item in events),
        "classification": "Mac-local Unicorn execution of checked-in Windows PE with a narrow PF Handle Suite shim; not AE-host execution and not AE-exact",
    })
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--aex", type=Path, default=DEFAULT_AEX)
    parser.add_argument("--direction", type=int, choices=(1, 2, 3), default=1)
    parser.add_argument("--json", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.aex, args.direction)
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "json": str(args.json), "deepest_rip": report.get("deepest_rip")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
