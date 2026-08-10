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
    assert report["status"] == "explicit_complete_actual_aex_fixture_boundary"
    assert report["admitted_rotated_leaf_tuples"] == [{
        "width": 9, "height": 7, "radius_or_length": 5, "angle_degrees": 5.0,
        "stages": ["forward_warp", "scalar_recurrence", "inverse_warp"],
        "raw_float32_words_per_stage": 63, "result": "exact",
    }]
    assert report["unsupported_tuple_behavior"] == (
        "return the unblurred input ray; no recurrence or alternate blur substitution"
    )
    print("PASS_OLMKIRAKIRA_MODE4_PRODUCTION_BOUNDARY_20260805")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
