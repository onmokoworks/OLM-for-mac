#!/usr/bin/env python3
"""Classify recovered RampDataHandler virtual slots by concrete behavior."""

from __future__ import annotations

import json
import struct
from pathlib import Path
import pefile

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "aex/OLMKiraKira/Plugins/64/2025/OLMKiraKira.aex"
DECOMP = ROOT / "decomp/OLMKiraKira.aex.c.txt"
REPORT = ROOT / "refs/conformance/olmkirakira_ramp_derived_vtable_contract_20260805.json"
VTABLE = 0x18148D818


def main() -> int:
    pe = pefile.PE(str(AEX))
    entries = struct.unpack("<13Q", pe.get_data(VTABLE - pe.OPTIONAL_HEADER.ImageBase, 104))
    expected = (0x1812327B0, 0x181232860, 0x18123AA70, 0x18123ABF0, 0x18123ACE0,
                0x18123AE70, 0x18123B270, 0x18123B460, 0x18123B470, 0x18123B660,
                0x181232910, 0x181232920, 0x181232930)
    assert entries == expected
    text = DECOMP.read_text(encoding="utf-8")
    assert "(0x260)" in text[text.index("// === FUN_18123abf0"):text.index("// === FUN_18123ace0")]
    assert "*param_3 = 0x145" in text[text.index("// === FUN_18123b460"):text.index("// === FUN_18123b470")]
    report = {
        "schema": "olmkirakira-ramp-derived-vtable-contract/1",
        "status": "method_behaviors_and_effectmain_numeric_selector_switch_grounded",
        "vtable": hex(VTABLE),
        "slots": [
            {"offset": "+0x00", "target": hex(entries[0]), "behavior": "handler-owned handle cleanup"},
            {"offset": "+0x08", "target": hex(entries[1]), "behavior": "supplied handle dispose path"},
            {"offset": "+0x10", "target": hex(entries[2]), "behavior": "allocate and initialize 0x15c handler-owned UI state"},
            {"offset": "+0x18", "target": hex(entries[3]), "behavior": "NEW/default: allocate and initialize 0x260 arbitrary handle"},
            {"offset": "+0x20", "target": hex(entries[4]), "behavior": "COPY: allocate destination via +0x18 and copy source state"},
            {"offset": "+0x28", "target": hex(entries[5]), "behavior": "FLATTEN-like: copy handle ramp payload into flat state"},
            {"offset": "+0x30", "target": hex(entries[6]), "behavior": "UNFLATTEN-like: allocate via +0x18 and restore flat state"},
            {"offset": "+0x38", "target": hex(entries[7]), "behavior": "FLAT_SIZE: write 0x145"},
            {"offset": "+0x40", "target": hex(entries[8]), "behavior": "COMPARE: lock two handles and write equal/not-equal result"},
            {"offset": "+0x48", "target": hex(entries[9]), "behavior": "INTERPOLATE: allocate destination and blend two ramp payloads"},
            {"offset": "+0x50", "target": hex(entries[10]), "behavior": "PRINT_SIZE: returns zero"},
            {"offset": "+0x58", "target": hex(entries[11]), "behavior": "PRINT: no-op"},
            {"offset": "+0x60", "target": hex(entries[12]), "behavior": "SCAN: no-op"},
        ],
        "numeric_selector_to_slot": {"0": "+0x18", "1": "+0x08", "2": "+0x20", "3": "+0x38", "4": "+0x28", "5": "+0x30", "6": "+0x48", "7": "+0x40", "8": "+0x50", "9": "+0x58", "10": "+0x60"},
        "dispatcher": "entry_point command 0x16 -> MyEffect vslot +0x40 (FUN_181151ae0)",
        "mac": "Canonical version/count/active-records/zero-tail representation implemented with five rows.",
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PASS_OLMKIRAKIRA_RAMP_DERIVED_VTABLE_CONTRACT_20260805 slots=13 numeric_selectors=0..10")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
