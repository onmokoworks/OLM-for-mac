#!/usr/bin/env python3
"""Resolve and execute the actual RampDataHandler default-handle vtable slot."""

from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path

import pefile

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "aex/OLMKiraKira/Plugins/64/2025/OLMKiraKira.aex"
REPORT = ROOT / "refs/conformance/olmkirakira_ramp_default_purecall_boundary_20260805.json"
VTABLE = 0x1814D66C8
SLOT = VTABLE + 0x18
THUNK = 0x18132D5E8
IAT = 0x181485518

sys.path.insert(0, str(ROOT / "tools/emulation"))
from aex_loader import AexLoader  # noqa: E402


def main() -> int:
    pe = pefile.PE(str(AEX))
    image_base = pe.OPTIONAL_HEADER.ImageBase
    slot_target = struct.unpack("<Q", pe.get_data(SLOT - image_base, 8))[0]
    thunk = pe.get_data(THUNK - image_base, 6)
    assert slot_target == THUNK
    assert thunk[:2] == b"\xff\x25"
    displacement = struct.unpack("<i", thunk[2:])[0]
    resolved_iat = THUNK + 6 + displacement
    assert resolved_iat == IAT
    imports = {
        item.address: (entry.dll.decode(), item.name.decode())
        for entry in pe.DIRECTORY_ENTRY_IMPORT for item in entry.imports if item.name
    }
    assert imports[IAT] == ("VCRUNTIME140.dll", "_purecall")

    loader = AexLoader(str(AEX), verbose=False, fast=True)
    result = loader.call_function(THUNK, [0, 0, 0], max_instructions=1000)
    calls = [{"dll": item.dll, "name": item.name, "args": [hex(v) for v in item.args], "ret": hex(item.ret)}
             for item in loader.import_log]
    assert [item["name"] for item in calls] == ["_purecall"]
    assert not any("Handle" in item["name"] for item in calls)
    report = {
        "schema": "olmkirakira-ramp-default-purecall-boundary/1",
        "status": "base_vtable_only_not_actual_caller",
        "aex_sha256": hashlib.sha256(AEX.read_bytes()).hexdigest(),
        "resolution": {
            "ramp_handler_vtable": hex(VTABLE),
            "default_handle_slot": hex(SLOT),
            "slot_target": hex(slot_target),
            "thunk_bytes": thunk.hex(),
            "iat": hex(resolved_iat),
            "import": "VCRUNTIME140.dll!_purecall",
        },
        "actual_aex_probe": {
            "instructions": result["instructions"],
            "imports": calls,
            "pf_handle_suite_callbacks": [],
            "requested_size": None,
            "handle_data_bytes": None,
            "handle_data_sha256": None,
        },
        "consequence": [
            "This is the base ArbitraryDataHandler vtable installed transiently by FUN_181232790.",
            "FUN_1811513a0 overwrites effect+0x200 with the derived RampDataHandler vtable 0x18148d818 before ParamsSetup.",
            "Therefore this purecall thunk is not reached by the actual ramp registration caller and is not an AEXCompat gap.",
        ],
        "arbitrary_selector_dispatch": {
            "new": "unresolved",
            "dispose": "unresolved",
            "copy": "unresolved",
            "mapping": [],
        },
        "aexcompat_gap": None,
        "mac_num_params": 36,
        "setup_exact": False,
        "fake_payload": False,
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PASS_OLMKIRAKIRA_RAMP_DEFAULT_PURECALL_BOUNDARY_20260805 base_only=true actual_caller=false")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
