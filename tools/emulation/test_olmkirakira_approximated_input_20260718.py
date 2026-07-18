#!/usr/bin/env python3
"""Regression gate for the KiraKira Approximated Input audit."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "tools/emulation/audit_olmkirakira_approximated_input_20260718.py"
REPORT = ROOT / "refs/conformance/olmkirakira_approximated_input_20260718.json"


def main() -> int:
    subprocess.run(["python3", str(AUDIT)], cwd=ROOT, check=True)
    data = json.loads(REPORT.read_text(encoding="utf-8"))
    assert data["ae_exact_claim"] is False
    contract = data["static_contract"]
    assert contract["gate"] == "strict ratio > float32(0.5)"
    assert contract["interpolation"] == "OpenCV INTER_NEAREST (0), from both typed-owner calls' final literal 0"
    assert "explicit dsize" in contract["pre_resize"]
    assert "explicit dsize" in contract["post_resize"]
    assert "no border mode" in contract["border"]
    assert "no alpha" in contract["alpha"]
    assert data["runtime"]["production_files_modified"] is False
    print("PASS_OLMKIRAKIRA_APPROXIMATED_INPUT_CONTRACT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
