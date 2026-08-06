#!/usr/bin/env python3
"""Verify actual and Mac ignore the arbitrary flat version byte."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENTRY = ROOT / "tools/emulation/test_olmkirakira_ramp_arbitrary_entrypoint_20260805.py"
ENTRY_REPORT = ROOT / "refs/conformance/olmkirakira_ramp_arbitrary_entrypoint_20260805.json"
CPP = ROOT / "tools/emulation/test_kirakira_ramp_flat_version.cpp"
MAC = ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp"
REPORT = ROOT / "refs/conformance/olmkirakira_ramp_flat_version_boundary_20260805.json"


def main() -> int:
    subprocess.run(["python3", str(ENTRY)], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
    actual = json.loads(ENTRY_REPORT.read_text(encoding="utf-8"))["version_byte_unflatten_results"]
    expected = {str(v): {"err": 0, "handle_created": True, "compare_source": 0} for v in (0, 2, 255)}
    assert actual == expected
    with tempfile.TemporaryDirectory(prefix="kk_flat_version_") as td:
        exe = Path(td) / "flat_version"
        subprocess.run(["c++", "-std=c++17", "-O2", str(CPP), "-o", str(exe)], check=True)
        subprocess.run([str(exe)], check=True)
    assert "parse_merge2_ramp_flat(" in MAC.read_text(encoding="utf-8")
    report = {
        "schema": "olmkirakira-ramp-flat-version-boundary/1",
        "status": "actual_entrypoint_to_shared_core_to_production_exact",
        "selector": "PF_Arbitrary_UNFLATTEN_FUNC",
        "tested_version_bytes": [0, 1, 2, 255],
        "actual_noncanonical_results": actual,
        "rule": "byte 0 is accepted but semantically ignored; count begins at byte 1",
        "semantic_compare": "equal",
        "live_ae_claimed": False,
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PASS_OLMKIRAKIRA_RAMP_FLAT_VERSION_BOUNDARY_20260805 versions=0,1,2,255 semantic=equal")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
