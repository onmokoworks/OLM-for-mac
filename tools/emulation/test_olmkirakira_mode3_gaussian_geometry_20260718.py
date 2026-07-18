#!/usr/bin/env python3
"""Regression gate for the bounded Mode 3 Gaussian geometry audit."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "tools/emulation/audit_olmkirakira_mode3_gaussian_geometry_20260718.py"
REPORT = ROOT / "refs/conformance/olmkirakira_mode3_gaussian_geometry_20260718.json"


def main() -> int:
    subprocess.run(["python3", str(AUDIT)], cwd=ROOT, check=True)
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["status"] == "bounded_geometry_shape_proven"
    assert report["ae_exact_claim"] is False
    assert report["production_edit"] is False
    static = report["static"]
    assert static["decomp_mode3_call_present"]
    assert static["asm_sigma_load_present"]
    assert static["asm_size_load_present"]
    assert static["asm_call_present"]
    assert static["asm_return_jump_present"]
    actual = report["actual_aex"]
    assert actual["all_sweep_points_captured"]
    assert actual["all_sigma_matches"]
    assert actual["all_sizes_are_0x100000000"]
    assert actual["return_shape_preserved"]
    assert actual["return_output_type"] == {"channels": 1, "depth_code": 5, "word_count": 63}
    print("PASS_OLMKIRAKIRA_MODE3_GAUSSIAN_GEOMETRY_REGRESSION")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
