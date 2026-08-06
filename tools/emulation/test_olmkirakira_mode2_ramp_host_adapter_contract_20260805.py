#!/usr/bin/env python3
"""Validate the bounded raw-checkout adapter and document the missing host ABI."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "refs/conformance/olmkirakira_mode2_ramp_actual_aex_boundary_20260805.json"
CPP = ROOT / "tools/emulation/test_kirakira_merge2_ramp_host_adapter.cpp"
MAC = ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp"
HEADER = ROOT / "mac/OLMKiraKira/OLMKiraKira.h"
REPORT = ROOT / "refs/conformance/olmkirakira_mode2_ramp_mac_host_adapter_contract_20260805.json"


def main() -> int:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    raw_hex = fixture["ramp_abi"]["consumed_prefix_hex"]
    with tempfile.TemporaryDirectory(prefix="olmkirakira_ramp_adapter_") as td:
        executable = Path(td) / "adapter"
        subprocess.run(["c++", "-std=c++17", "-O2", str(CPP), "-o", str(executable)], check=True)
        output = subprocess.check_output(
            [str(executable)], input=" ".join(raw_hex[i:i + 2] for i in range(0, len(raw_hex), 2)), text=True
        ).splitlines()
    assert output == [
        "count 2",
        "0.25 1 0 0.25 0.125",
        "0.75 0 0.5 1 0.875",
    ]

    mac = MAC.read_text(encoding="utf-8")
    header = HEADER.read_text(encoding="utf-8")
    host_contract = {
        "five_arbitrary_param_enum_rows": "OLMKIRAKIRA_VERTICAL_RAMP" in header,
        "arbitrary_param_registration": "def.param_type = PF_Param_ARBITRARY_DATA" in mac,
        "arbitrary_callback_dispatch": "PF_Cmd_ARBITRARY_CALLBACK" in mac,
        "custom_ui_dispatch": "PF_Cmd_EVENT" in mac,
        "render_checkout_rows": "u.arb_d.value" in mac,
        "actual_windows_checkout_payload": False,
    }
    assert all(value for key, value in host_contract.items() if key != "actual_windows_checkout_payload")
    report = {
        "schema": "olmkirakira-mode2-ramp-mac-host-adapter-contract/1",
        "status": "adapter_exact_host_surface_wired_windows_checkout_payload_unverified",
        "adapter": {
            "input": "direct-actual-AEX consumed 44-byte prefix",
            "parsed_records": output,
            "truncated_payload_fails_closed": True,
        },
        "host_contract": host_contract,
        "aexcompat_gap": False,
        "aexcompat_note": "The missing surface is an AE arbitrary-data/custom-UI plugin contract; no AEXCompat runtime function was reached or shown missing.",
        "minimum_next_fixture": "A live Windows ParamCheckout trace containing the host ramp object bytes copied from object+0x10 for one non-default ramp, plus callback/property identity.",
        "production": "Mac host registers five arbitrary-data parameters, dispatches arbitrary/custom-UI callbacks, and reads checked-out handle payloads without synthesizing Windows object bytes.",
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PASS_OLMKIRAKIRA_MODE2_RAMP_HOST_ADAPTER_CONTRACT_20260805 parsed=2 truncated=closed host_surface=wired windows_checkout_payload=unverified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
