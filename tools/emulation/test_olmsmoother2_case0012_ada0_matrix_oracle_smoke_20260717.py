#!/usr/bin/env python3
"""Smoke test for the actual-AEX versus portable class-plane matrix."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROBE = ROOT / "tools/emulation/test_olmsmoother2_case0012_ada0_matrix_oracle_20260717.py"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olmsmoother2_ada0_matrix_") as temp:
        out_json, out_md = Path(temp) / "result.json", Path(temp) / "result.md"
        run = subprocess.run([sys.executable, str(PROBE), "--output-json", str(out_json), "--output-md", str(out_md)], cwd=ROOT, text=True, capture_output=True)
        assert run.returncode == 0, run.stdout + run.stderr
        result = json.loads(out_json.read_text(encoding="utf-8"))
    assert result["verdict"] == "PASS_EXACT_AEX_AE10_PORTABLE_MATRIX_15_BOUNDARY_FIXTURES"
    assert result["coverage"]["fixtures"] == 30
    assert all(row["status"] == "exact" and row["differing_bytes"] == 0 for row in result["matrix"])
    print("PASS: 30-fixture actual-AEX ada0/ac00/ae10 matrix equals independent oracle")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
