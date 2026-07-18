#!/usr/bin/env python3
"""Smoke-test the dated final PF output contract audit."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "tools/emulation/audit_olmdirectionalblur_final_pf_output_contract_20260718.py"
REPORT = ROOT / "refs/conformance/olmdirectionalblur_final_pf_output_contract_20260718.json"


def main() -> int:
    result = subprocess.run([sys.executable, str(AUDIT)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["status"] == "pass"
    assert all(report["checks"].values())
    assert report["boundary"]["full_frame_equivalence"] is False
    assert report["boundary"]["same_run_natural_full_frame"] is False
    assert report["fail_closed"]["ae_exact_claim"] is False
    print(json.dumps({"status": "pass", "samples": report["observed"]["sample_count"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
