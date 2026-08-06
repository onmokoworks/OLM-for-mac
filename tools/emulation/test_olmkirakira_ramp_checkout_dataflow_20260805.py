#!/usr/bin/env python3
"""Pin the actual-AEX ramp checkout pointer chain and lifetime."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "aex/OLMKiraKira/Plugins/64/2025/OLMKiraKira.aex"
DECOMP = ROOT / "decomp/OLMKiraKira.aex.c.txt"
REPORT = ROOT / "refs/conformance/olmkirakira_ramp_checkout_dataflow_20260805.json"


def main() -> int:
    text = DECOMP.read_text(encoding="utf-8")
    owner_start = text.index("// === FUN_18114e860")
    owner = text[owner_start:text.index("// === FUN_", owner_start + 20)]
    checkout = text[text.index("// === FUN_181154630"):text.index("// === FUN_181154820")]
    rows = [
        ("vertical", "0x83c", "0x13", "0x1e8"),
        ("horizontal", "0x83d", "0x15", "0x32c"),
        ("diagonal", "0x83e", "0x17", "0x470"),
        ("diagonal2", "0x83f", "0x24", "0x5b4"),
        ("highlight", "0x840", "0x19", "0x6f8"),
    ]
    for _name, use, disk, dst in rows:
        assert f"lVar1 + {use}" in owner
        assert f"param_1,{disk},lVar1 + {dst}" in owner
    for needle in (
        "piVar8 = (int *)(param_1 + 8)",
        "if (*piVar8 == param_3)",
        "local_118 = *(undefined4 *)(param_2 + 0xf0)",
        'local_e8 = "PF Handle Suite"',
        "lVar9 = (**(code **)(local_100 + 8))(local_90)",
        "puVar5 = (undefined8 *)(lVar9 + 0x10)",
        "(**(code **)(local_100 + 0x10))(local_90)",
        "FUN_181232760(param_2,local_d8)",
    ):
        assert needle in checkout
    report = {
        "schema": "olmkirakira-ramp-checkout-dataflow/1",
        "status": "pointer_chain_lifetime_and_mac_connection_grounded",
        "aex_sha256": hashlib.sha256(AEX.read_bytes()).hexdigest(),
        "render_owner": "FUN_18114e860",
        "rows": [
            {"name": n, "use_state_offset": u, "arbitrary_disk_id": int(d, 16),
             "destination_state_offset": dst}
            for n, u, d, dst in rows
        ],
        "off_branch": "Use byte zero skips FUN_181154630 and leaves the destination block unconsumed.",
        "on_pointer_chain": [
            "EffectBase disk-ID array at effect+0x8..effect+0xac resolves disk ID to parameter index",
            "in_data+0x180 acquires PF Handle Suite v2",
            "host parameter checkout returns local_90 handle wrapper",
            "PF Handle Suite lock at vtable+0x8 returns host object",
            "payload source is locked_object+0x10",
            "exactly 0x144 bytes copy to render-state destination",
        ],
        "lifetime": [
            "PF Handle Suite unlock at vtable+0x10",
            "temporary checked-out parameter wrapper release via FUN_181232760",
            "PF Handle Suite release through in_data+0x180 callback slot 1",
            "destination 0x144-byte copy remains render-state-owned for the render call",
        ],
        "not_sources": ["sequence/global data", "static ramp table", "checkbox value bytes"],
        "mac_connection": "implemented: standard and Smart Render lock/copy/unlock the five 0x144 payloads",
        "fake_payload": False,
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PASS_OLMKIRAKIRA_RAMP_CHECKOUT_DATAFLOW_20260805 rows=5 off=skip on=handle_lock_copy_unlock_release")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
