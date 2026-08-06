#!/usr/bin/env python3
"""Lock actual 3-stop/2-stop arbitrary interpolation to Mac production."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENTRY = ROOT / "tools/emulation/test_olmkirakira_ramp_arbitrary_entrypoint_20260805.py"
ENTRY_REPORT = ROOT / "refs/conformance/olmkirakira_ramp_arbitrary_entrypoint_20260805.json"
CPP = ROOT / "tools/emulation/test_kirakira_ramp_interpolate.cpp"
MAC = ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp"
REPORT = ROOT / "refs/conformance/olmkirakira_ramp_mismatched_interpolation_20260805.json"


def main() -> int:
    subprocess.run(["python3", str(ENTRY)], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
    actual = json.loads(ENTRY_REPORT.read_text(encoding="utf-8"))["mismatched_count_interpolation"]
    assert set(actual) == {"0.25", "0.5", "0.75"}
    assert all(case["count"] == 3 for case in actual.values())
    assert all(case["compare_source"] == 3 and case["compare_two_stop"] == 3 for case in actual.values())
    with tempfile.TemporaryDirectory(prefix="kk_ramp_interp_") as td:
        exe = Path(td) / "interp"
        subprocess.run(["c++", "-std=c++17", "-O2", str(CPP), "-o", str(exe)], check=True)
        subprocess.run([str(exe)], check=True)
    mac = MAC.read_text(encoding="utf-8")
    assert "interpolate_merge2_ramps(" in mac
    report = {
        "schema": "olmkirakira-ramp-mismatched-interpolation/1",
        "status": "actual_entrypoint_to_mac_production_exact",
        "public_entrypoint": "PF_Cmd_ARBITRARY_CALLBACK / PF_Arbitrary_INTERP_FUNC",
        "left_count": 3,
        "right_count": 2,
        "rule": "output count is max; missing right record repeats its last stop; all five float fields interpolate",
        "cases": actual,
        "max_ulp": 0,
        "host_gate": "AE restart and live keyframe interpolation are not claimed.",
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PASS_OLMKIRAKIRA_RAMP_MISMATCHED_INTERPOLATION_20260805 cases=3 max_ulp=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
