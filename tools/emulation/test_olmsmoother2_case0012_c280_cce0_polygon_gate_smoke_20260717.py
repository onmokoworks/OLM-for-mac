#!/usr/bin/env python3
"""Smoke test for the fail-closed c280/cce0 polygon gate."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROBE = ROOT / "tools/emulation/test_olmsmoother2_case0012_c280_cce0_polygon_gate_20260717.py"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olmsmoother2_polygon_gate_") as temp:
        out_json, out_md = Path(temp) / "result.json", Path(temp) / "result.md"
        run = subprocess.run([sys.executable, str(PROBE), "--output-json", str(out_json), "--output-md", str(out_md)], cwd=ROOT, text=True, capture_output=True)
        assert run.returncode == 0, run.stdout + run.stderr
        result = json.loads(out_json.read_text(encoding="utf-8"))
    assert result["verdict"] == "PASS_ACTUAL_C280_CCE0_WITH_FAIL_CLOSED_PORTABLE_POLYGON_BOUNDARY"
    assert len(result["actual_cases"]) == 30
    assert result["first_missing_semantic"]["case"]["classifier_index"] == 0
    exact = [row for row in result["portable_checks"] if row["status"] == "exact"]
    assert len(exact) == 18
    assert all(row["status"] == "exact" for row in exact)
    print("PASS: 30 actual c280/cce0 cases; 18 grounded empty-polygon cases; stopped at first non-empty owner")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
