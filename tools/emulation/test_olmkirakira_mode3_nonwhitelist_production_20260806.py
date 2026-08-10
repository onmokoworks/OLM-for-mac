#!/usr/bin/env python3
"""Fail closed outside complete actual-AEX Mode-3 geometry/length fixtures."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp"
CPP = ROOT / "tools/emulation/test_kirakira_mode3_nonwhitelist_geometry.cpp"
REPORT = ROOT / "refs/conformance/olmkirakira_mode3_admission_boundary_20260810.json"


def main() -> int:
    production = SOURCE.read_text(encoding="utf-8")
    assert "mode3_gaussian_admitted(rw, rh, length)" in production
    assert "if (blur_mode == 3 && !mode3_admitted) return input;" in production
    assert "if (blur_mode == 3)" in production
    assert "exact_mode3_fixture" not in production
    assert "return RotatedAxisBoxBlur(seed, work_width, work_height, len, angle, passes, info.blur_mode);" in production
    assert "if (bitdepth == 8) return RenderTyped<PF_Pixel8>" in production
    assert "if (bitdepth == 16) return RenderTyped<PF_Pixel16>" in production
    assert "if (bitdepth == 32) return RenderTyped<PF_PixelFloat>" in production
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["status"] == "bounded_geometry_general_contract"
    assert [(row["width"], row["height"], row["length"]) for row in report["admitted_rotated_leaf_tuples"]] == [
        (11, 6, 3), (9, 7, 3), (9, 7, 5), (9, 7, 7), (9, 7, 9),
        (9, 7, 50), (9, 9, 50), (13, 5, 7), (15, 6, 9)
    ]
    assert report["unsupported_tuple_behavior"] == "return the unblurred input ray; never substitute Mode 2"
    with tempfile.TemporaryDirectory(prefix="olmkira-mode3-general-") as td:
        exe = Path(td) / "mode3"
        subprocess.run([
            "c++", "-std=c++20", "-O2", "-ffp-contract=off",
            str(CPP), "-o", str(exe),
        ], cwd=ROOT, check=True)
        subprocess.run([str(exe)], cwd=ROOT, check=True)
    assert report["geometry_general_contract"] == {
        "minimum_width": 9,
        "minimum_height": 7,
        "lengths": [3, 50],
        "result": "raw_float32_exact_across_representative_geometry_and_dispatch_classes",
        "evidence": "refs/conformance/olmkirakira_mode3_geometry_generalization_actual_aex_20260810.json",
        "focused_regression": "tools/emulation/test_olmkirakira_mode3_geometry_generalization_actual_aex_20260810.py",
    }
    print("PASS_OLMKIRAKIRA_MODE3_NONWHITELIST_PRODUCTION_20260806 general=length3,50 exceptions=9 unsupported=fail_closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
