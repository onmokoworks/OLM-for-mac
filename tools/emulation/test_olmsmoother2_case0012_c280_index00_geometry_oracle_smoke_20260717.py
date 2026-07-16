#!/usr/bin/env python3
"""Smoke test for classifier 0x00 c280 geometry grounding."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROBE = ROOT / "tools/emulation/test_olmsmoother2_case0012_c280_index00_geometry_oracle_20260717.py"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olmsmoother2_c280_00_") as temp:
        out_json, out_md = Path(temp) / "result.json", Path(temp) / "result.md"
        run = subprocess.run([sys.executable, str(PROBE), "--output-json", str(out_json), "--output-md", str(out_md)], cwd=ROOT, text=True, capture_output=True)
        assert run.returncode == 0, run.stdout + run.stderr
        result = json.loads(out_json.read_text(encoding="utf-8"))
    assert result["verdict"] == "PASS_EXACT_C280_INDEX00_INDEPENDENT_GEOMETRY_ORACLE"
    assert result["actual"]["c280"]["count"] == 12
    assert result["comparison"]["vertices_equal_raw_float_bits"] is True
    assert result["grounding"]["order"] == [
        "FUN_1800134c0(&local_188,DAT_180022dd4)",
        "FUN_180013570(&local_188,fVar1)",
        "FUN_180012ce0(&local_188,fVar1)",
        "FUN_180012c20(&local_188,fVar1)",
    ]
    print("PASS: classifier 0x00 c280 count/order/vertices match independent raw-bit oracle")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
