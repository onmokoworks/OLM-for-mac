#!/usr/bin/env python3
"""Focused tests for the case0009 local sampler/prepass analyzer."""

import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import analyze_radialblur_case0009_sampler_prepass_writeback as analyzer  # noqa: E402


def point(x: int, y: int, radius: float, angle: float, final_alpha: float = 0.75) -> dict:
    fr, fa = radius % 1, angle % 1
    cells = {}
    for slot in analyzer.SLOTS:
        accum = [0.2, 0.4, 0.6, 2.0]
        cells[slot] = {
            "accum_rgba_f32": accum,
            "denom_f32": final_alpha,
            "valid_f32": 1.0,
            "final_rgba_f32": [0.1, 0.2, 0.3, final_alpha],
        }
    return {
        "xy": [x, y],
        "radius_index": radius,
        "angle_index": angle,
        "bilinear_weights": [(1-fr)*(1-fa), fr*(1-fa), (1-fr)*fa, fr*fa],
        "cells": cells,
    }


def main() -> int:
    document = {"points": [point(7, 0, 40.25, 3.75), point(8, 0, 39.5, 3.125), point(24, 0, 25.875, 1.25)]}
    result = analyzer.analyze(document)
    assert result["status"] == "pass", result

    fixture = json.loads(Path(
        HERE.parent.parent / "refs/conformance/olmradialblur_nonzero_typed_cell_20260713.json"
    ).read_text(encoding="utf-8"))
    fixture_result = analyzer.analyze(fixture)
    assert fixture_result["evidence_class"] == "local_fixture"
    assert fixture_result["status"] == "pass", fixture_result

    broken = json.loads(json.dumps(document))
    broken["points"][0]["bilinear_weights"][0] += 0.1
    assert analyzer.analyze(broken)["status"] == "fail"
    print("[OK] case0009 sampler/prepass/writeback analyzer invariants")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
