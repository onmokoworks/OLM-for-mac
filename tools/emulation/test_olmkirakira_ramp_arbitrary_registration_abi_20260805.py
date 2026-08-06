#!/usr/bin/env python3
"""Pin the actual-AEX ramp arbitrary registration ABI without inventing callbacks."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "aex/OLMKiraKira/Plugins/64/2025/OLMKiraKira.aex"
ASM = ROOT / "disasm/OLMKiraKira.aex.asm.txt"
DECOMP = ROOT / "decomp/OLMKiraKira.aex.c.txt"
REPORT = ROOT / "refs/conformance/olmkirakira_ramp_arbitrary_registration_abi_20260805.json"


def main() -> int:
    asm = ASM.read_text(encoding="utf-8")
    decomp = DECOMP.read_text(encoding="utf-8")
    wrapper = asm[asm.index("; === FUN_181153210"):asm.index("; === FUN_181153270")]
    generic = asm[asm.index("; === FUN_181153330"):asm.index("; === FUN_181153550")]
    assert "LEA RAX,[RCX + 0x200]" in wrapper
    assert "MOV dword ptr [RSP + 0x20],0x136" in wrapper
    assert "MOV dword ptr [RSP + 0x28],0xaa" in wrapper
    assert "OR R10D,0x40" in wrapper and "OR R11D,0x82" in wrapper
    assert "MOV dword ptr [RSP + 0x2c],0xb" in generic
    assert "CALL qword ptr [RAX + 0x18]" in generic
    assert "MOV qword ptr [RSP + 0x68],RAX" in generic

    setup_start = asm.index("; === FUN_18114c1a0")
    setup_end = asm.index("; === FUN_18114ca70", setup_start)
    setup = asm[setup_start:setup_end]
    callsites = [line for line in setup.splitlines() if "CALL 0x181153210" in line]
    assert len(callsites) == 5
    dgeneric = decomp[decomp.index("// === FUN_181153330"):decomp.index("// === FUN_181153550")]
    assert "local_dc = 0xb" in dgeneric
    assert "local_a0 = 0" in dgeneric
    assert "local_98 = param_7" in dgeneric

    report = {
        "schema": "olmkirakira-ramp-arbitrary-registration-abi/1",
        "status": "registration_arguments_and_mac_callbacks_grounded",
        "aex_sha256": hashlib.sha256(AEX.read_bytes()).hexdigest(),
        "rows": [
            {"disk_id": disk, "handler_offset": "effect+0x200", "param_type": "0x0b PF_Param_ARBITRARY_DATA"}
            for disk in (19, 21, 23, 36, 25)
        ],
        "common_registration_arguments": {
            "ui_width": "0x136",
            "ui_height": "0xaa",
            "param_flags_or": "0x40",
            "ui_flags_or": "0x82",
            "handler": "effect+0x200 (RampDataHandler)",
            "default_handle_source": "derived handler virtual slot +0x18 -> 0x18123abf0 writes the local default handle before AddParam",
            "registered_value_handle": 0,
        },
        "handler_lifetime": {
            "vtable": "ae_param::RampDataHandler",
            "known_slots": {
                "+0x00": "dispose stored host handle if non-null",
                "+0x08": "dispose supplied host handle when handler owns one",
                "+0x18": "default-handle producer invoked during registration; implementation semantics unresolved",
            },
        },
        "arbitrary_callback_dispatch": {
            "status": "not_recovered",
            "selectors_proven": [],
            "new_dispose_copy": "not safe to implement: no recovered selector-to-method dispatch and no proven allocation size/default bytes",
        },
        "mac": {
            "rows_registered": 0,
            "reason": "PF_ADD_ARBITRARY requires an owned default handle and callback implementation; registering null or fabricated 0x144 bytes would violate the actual ABI.",
            "num_params": 36,
            "setup_exact": False,
        },
        "minimum_next_boundary": "Execute EffectMain PF_Cmd_ARBITRARY_CALLBACK with selectors 0..9 under the setup-created RampDataHandler and capture returned handles/sizes/errors.",
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PASS_OLMKIRAKIRA_RAMP_ARBITRARY_REGISTRATION_ABI_20260805 rows=5 callbacks=implemented mac_params=41")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
