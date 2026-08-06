#!/usr/bin/env python3
"""Lock actual numeric signed-zero COMPARE semantics to production."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENTRY = ROOT / "tools/emulation/test_olmkirakira_ramp_arbitrary_entrypoint_20260805.py"
ENTRY_REPORT = ROOT / "refs/conformance/olmkirakira_ramp_arbitrary_entrypoint_20260805.json"
CPP = ROOT / "tools/emulation/test_kirakira_ramp_compare_signed_zero.cpp"
MAC = ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp"
REPORT = ROOT / "refs/conformance/olmkirakira_ramp_compare_signed_zero_20260805.json"


def main() -> int:
    subprocess.run(["python3", str(ENTRY)], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
    actual = json.loads(ENTRY_REPORT.read_text(encoding="utf-8"))["signed_zero_compare"]
    assert actual == {
        "left_position_bits": "0x00000000",
        "right_position_bits": "0x80000000",
        "result": 0,
    }
    with tempfile.TemporaryDirectory(prefix="kk_compare_zero_") as td:
        exe = Path(td) / "compare_zero"
        subprocess.run(["c++", "-std=c++17", "-O2", str(CPP), "-o", str(exe)], check=True)
        subprocess.run([str(exe)], check=True)
    assert "equal_merge2_ramps(" in MAC.read_text(encoding="utf-8")
    report = {
        "schema": "olmkirakira-ramp-compare-signed-zero/1",
        "status": "actual_entrypoint_to_shared_core_to_production_exact",
        "selector": "PF_Arbitrary_COMPARE_FUNC",
        "boundary": actual,
        "rule": "active float fields use numeric equality, so +0.0 equals -0.0; count and changed numeric values still differ",
        "live_ae_claimed": False,
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PASS_OLMKIRAKIRA_RAMP_COMPARE_SIGNED_ZERO_20260805 result=equal")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
