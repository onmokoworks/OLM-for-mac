#!/usr/bin/env python3
"""Regression gate for the 2026-07-18 KiraKira parameter audit."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "tools/emulation/audit_olmkirakira_unconsumed_parameters_20260718.py"
REPORT = ROOT / "refs/conformance/olmkirakira_unconsumed_parameters_20260718.json"


def main() -> int:
    subprocess.run(["python3", str(AUDIT)], cwd=ROOT, check=True)
    result = json.loads(REPORT.read_text(encoding="utf-8"))
    assert result["status"] == "pass_binary_grounded_partial_wiring"
    assert result["ae_exact_claim"] is False
    params = result["parameters"]
    assert params["Fade Out"]["normalization"]["value"] == 0.20000000298023224
    assert "wired" in params["Fade Out"]["mac"]
    assert "wired" in params["Highlight Radius"]["mac"]
    approx = params["Approximated Input"]
    assert "source-wired" in approx["mac"]
    assert "binary-shaped" in approx["mac"]
    assert "behaviorally unvalidated" in approx["mac"]
    assert approx["behavioral_validation"]
    assert "blocked_boundary" not in approx
    print("PASS_OLMKIRAKIRA_UNCONSUMED_PARAMETER_REGRESSION")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
