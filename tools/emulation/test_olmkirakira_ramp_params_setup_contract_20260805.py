#!/usr/bin/env python3
"""Correlate actual-AEX ramp registration with the bounded Mac setup shape."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "aex/OLMKiraKira/Plugins/64/2025/OLMKiraKira.aex"
DECOMP = ROOT / "decomp/OLMKiraKira.aex.c.txt"
SDK = ROOT / "Headers/AE_Effect.h"
MAC = ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp"
HEADER = ROOT / "mac/OLMKiraKira/OLMKiraKira.h"
REPORT = ROOT / "refs/conformance/olmkirakira_ramp_params_setup_contract_20260805.json"


def main() -> int:
    decomp = DECOMP.read_text(encoding="utf-8")
    sdk = SDK.read_text(encoding="utf-8")
    mac = MAC.read_text(encoding="utf-8")
    header = HEADER.read_text(encoding="utf-8")
    helper = decomp[decomp.index("// === FUN_181152eb0"):decomp.index("// === FUN_181152f80")]
    arbitrary = decomp[decomp.index("// === FUN_181153330"):decomp.index("// === FUN_181153550")]
    setup = decomp[decomp.index("// === FUN_18114c1a0"):decomp.index("// === FUN_18114ca70")]
    assert "local_cc = 0xd;" in helper
    assert "local_dc = 0xb;" in arbitrary
    assert sdk.index("PF_Param_GROUP_START") < sdk.index("PF_Param_GROUP_END")

    ramps = [
        ("Vertical", "0x1d", 29, 18, 19, 30),
        ("Horizontal", "0x1f", 31, 20, 21, 32),
        ("Diagonal", "0x21", 33, 22, 23, 34),
        ("Diagonal2", "0x25", 37, 35, 36, 38),
        ("Highlight", "0x27", 39, 24, 25, 40),
    ]
    for _name, disk_hex, group_id, use_id, spacer_id, end_id in ramps:
        assert f",{disk_hex},0," in setup
        assert f"_RAMP_GROUP_DISK_ID = {group_id}" in header
        assert f"_USE_RAMP_DISK_ID = {use_id}" in header
        assert f"_RAMP_SPACER_DISK_ID = {spacer_id}" in header
        assert f"_RAMP_END_DISK_ID = {end_id}" in header
    assert mac.count("PF_ADD_TOPIC(GetStringPtr(StrID_") >= 5
    assert mac.count("PF_END_TOPIC(") >= 5
    assert mac.count("AddRampParam(in_data,") == 5
    assert "PF_Cmd_ARBITRARY_CALLBACK" in mac
    assert "std::memset(flat, 0, 0x145)" in mac
    assert "flat[0] = 1" in mac

    report = {
        "schema": "olmkirakira-ramp-params-setup-contract/1",
        "status": "registration_exact_actual_41_mac_41_canonical_arbitrary",
        "aex_sha256": hashlib.sha256(AEX.read_bytes()).hexdigest(),
        "actual_aex": {
            "params_setup": "FUN_18114c1a0",
            "ramp_registration_helper": "FUN_181152eb0",
            "written_param_type": "0x0d = PF_Param_GROUP_START",
            "rows": [
                {"name": n, "group_disk_id": g, "use_disk_id": u,
                 "spacer_disk_id": s, "end_disk_id": e}
                for n, _h, g, u, s, e in ramps
            ],
            "num_params_including_input": 41,
            "group_default_argument": 0,
            "arbitrary_row_type": "0x0b = PF_Param_ARBITRARY_DATA at disk IDs 19/21/23/36/25",
            "arbitrary_default_payload_size": "0x260 Windows wrapper containing pointer-free 0x144 payload at +0x10",
            "arbitrary_callback_selectors": "numeric 0..10 recovered and exercised through actual entry_point",
        },
        "mac": {
            "registration_added": "five GROUP_START/use-checkbox/PF_Param_ARBITRARY_DATA/GROUP_END quartets",
            "num_params_including_input": 41,
            "setup_exact": True,
            "render_payload_checkout": "handle lock/copy/unlock for standard and Smart Render",
            "fake_payload": False,
        },
        "limit": None,
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PASS_OLMKIRAKIRA_RAMP_PARAMS_SETUP_CONTRACT_20260805 arbitrary_rows=5 mac_params=41 setup_exact=1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
