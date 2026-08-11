#!/usr/bin/env python3
"""Build and run the shared Mode4 scalar recurrence against actual-AEX bits."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "refs/conformance/olmkirakira_mode4_admission_boundary_20260810.json"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olmkirakira-mode4-") as tmp:
        binary = Path(tmp) / "mode4"
        subprocess.run([
            "c++", "-std=c++20", "-O2", "-ffp-contract=off",
            str(ROOT / "tools/emulation/test_kirakira_mode4.cpp"),
            "-o", str(binary),
        ], cwd=ROOT, check=True)
        subprocess.run([str(binary)], cwd=ROOT, check=True)
    source = (ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp").read_text(encoding="utf-8")
    assert '#include "../../core/kirakira_mode4.h"' in source
    assert "mode4_rotated_scalar_admitted(" in source
    assert "rw, rh, length, angle_deg))\n\t\t\treturn input;" in source
    assert "mode4_rotated_scalar_chain(" in source
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["status"] == "geometry_general_actual_aex_boundary"
    assert [(row["width"], row["height"], row["radius_or_length"], row["angle_degrees"])
            for row in report["admitted_rotated_leaf_tuples"]] == [
        (9, 7, 5, 0.0), (9, 7, 5, 5.0), (9, 9, 5, 45.0),
        (9, 9, 5, -45.0), (9, 9, 5, 90.0),
    ]
    assert all(row["stages"] == ["forward_warp", "scalar_recurrence", "inverse_warp"]
               and row["result"] == "exact" for row in report["admitted_rotated_leaf_tuples"])
    generalized = report["geometry_generalization"]
    assert generalized["complete_actual_aex_cases"] == 17
    assert generalized["radii"] == [1, 5, 50, 300, 301, 1000]
    assert generalized["angles_degrees"] == [-45, 0, 17, 45, 90]
    assert report["unsupported_tuple_behavior"] == (
        "sub-minimum geometry or radius outside the public 1..1000 range returns the unblurred input ray"
    )
    print("PASS_OLMKIRAKIRA_MODE4_PRODUCTION_BOUNDARY_20260805")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
