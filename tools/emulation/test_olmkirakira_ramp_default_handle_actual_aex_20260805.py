#!/usr/bin/env python3
"""Execute the concrete RampDataHandler default-handle producer."""

from __future__ import annotations

import hashlib
import json
import os
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "aex/OLMKiraKira/Plugins/64/2025/OLMKiraKira.aex"
REPORT = ROOT / "refs/conformance/olmkirakira_ramp_default_handle_actual_aex_20260805.json"
VTABLE = 0x18148D818
TARGET = 0x18123ABF0

sys.path.insert(0, str(ROOT / "tools/emulation"))
from aex_loader import AexLoader  # noqa: E402


def main() -> int:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    preallocate = int(os.environ.get("OLM_KK_RAMP_PREALLOCATE", "0"))
    if preallocate:
        loader.host_alloc(preallocate)
    events: list[dict[str, object]] = []
    allocations: dict[int, int] = {}

    def c_string(emu: AexLoader, address: int) -> str:
        data = bytearray()
        while len(data) < 128:
            value = emu.read_bytes(address + len(data), 1)
            if value == b"\0":
                break
            data += value
        return data.decode("ascii")

    def new_handle(emu: AexLoader, args: list[int]) -> int:
        size = args[0]
        handle = emu.host_alloc(size)
        # Match the checked-in host scaffold's zero-filled fresh handle.
        emu.write_bytes(handle, bytes(size))
        allocations[handle] = size
        events.append({"op": "new", "size": size, "handle": hex(handle)})
        return handle

    def lock_handle(_emu: AexLoader, args: list[int]) -> int:
        events.append({"op": "lock", "handle": hex(args[0])})
        return args[0]

    def unlock_handle(_emu: AexLoader, args: list[int]) -> int:
        events.append({"op": "unlock", "handle": hex(args[0])})
        return 0

    def dispose_handle(_emu: AexLoader, args: list[int]) -> int:
        events.append({"op": "dispose", "handle": hex(args[0])})
        return 0

    suite = loader.host_alloc(32)
    suite_callbacks = [
        loader.install_callback("NewHandle", new_handle),
        loader.install_callback("LockHandle", lock_handle),
        loader.install_callback("UnlockHandle", unlock_handle),
        loader.install_callback("DisposeHandle", dispose_handle),
    ]
    loader.write_bytes(suite, struct.pack("<4Q", *suite_callbacks))

    def acquire(emu: AexLoader, args: list[int]) -> int:
        emu.write_bytes(args[2], struct.pack("<Q", suite))
        events.append({"op": "acquire", "name": c_string(emu, args[0]), "version": args[1]})
        return 0

    def release(emu: AexLoader, args: list[int]) -> int:
        events.append({"op": "release", "name": c_string(emu, args[0]), "version": args[1]})
        return 0

    provider = loader.host_alloc(16)
    loader.write_bytes(provider, struct.pack("<2Q",
        loader.install_callback("AcquireSuite", acquire),
        loader.install_callback("ReleaseSuite", release)))
    in_data = loader.host_alloc(0x200)
    loader.write_bytes(in_data, bytes(0x200))
    loader.write_bytes(in_data + 0x180, struct.pack("<Q", provider))
    handler = loader.host_alloc(16)
    loader.write_bytes(handler, struct.pack("<2Q", VTABLE, 0))
    output_handle = loader.host_alloc(8)
    loader.write_bytes(output_handle, bytes(8))

    result = loader.call_function(TARGET, [handler, in_data, output_handle], max_instructions=500_000)
    handle = struct.unpack("<Q", loader.read_bytes(output_handle, 8))[0]
    size = allocations[handle]
    data = loader.read_bytes(handle, size)
    assert size == 0x260
    assert [event["op"] for event in events] == ["acquire", "new", "lock", "unlock", "release"]
    report = {
        "schema": "olmkirakira-ramp-default-handle-actual-aex/1",
        "status": "default_new_lock_initialize_unlock_grounded",
        "aex_sha256": hashlib.sha256(AEX.read_bytes()).hexdigest(),
        "constructor_vptr_chain": [
            {"write": "effect+0x200", "value": "0x1814d66c8", "role": "base ArbitraryDataHandler vtable"},
            {"write": "effect+0x200", "value": hex(VTABLE), "role": "derived RampDataHandler vtable overwrite"},
        ],
        "target": hex(TARGET),
        "events": events,
        "requested_size": size,
        "handle_data_sha256": hashlib.sha256(data).hexdigest(),
        "handle_data_hex": data.hex(),
        "preallocated_host_bytes": preallocate,
        "layout": {
            "container_vptr_offset": 0,
            "ramp_vptr_offset": 8,
            "inline_payload_offset": 16,
            "inline_payload_size": 0x144,
            "stop_count": struct.unpack_from("<I", data, 16)[0],
            "stops_position_alpha_red_green_blue": [
                list(struct.unpack_from("<5f", data, 20 + i * 20))
                for i in range(struct.unpack_from("<I", data, 16)[0])
            ],
            "inline_payload_sha256": hashlib.sha256(data[16:16 + 0x144]).hexdigest(),
        },
        "instructions": result["instructions"],
        "dispose": "not part of default producer; ownership transfers to AE host",
        "mac": "canonical pointer-free payload and selector ownership are implemented",
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"PASS_OLMKIRAKIRA_RAMP_DEFAULT_HANDLE_ACTUAL_AEX_20260805 size={size} events=5 sha256={report['handle_data_sha256']}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
