#!/usr/bin/env python3
"""Focused tests for the case0009 local sampler/prepass analyzer."""

import json
import subprocess
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

    def capture(rgba_word: str, scalar_word: str, rgba_value: float) -> dict:
        return {
            "row_range": [0, 1],
            "nonzero_cells": [{
                "row": 0, "column": 0,
                "rgba_f32": [rgba_value, 0.0, 0.0, 1.0],
                "scalar_f32": 1.0,
                "rgba_f32_words": [rgba_word, "0x00000000", "0x00000000", "0x3f800000"],
                "scalar_f32_word": scalar_word,
            }],
            "rgba_sha256": rgba_word,
            "scalar_sha256": scalar_word,
        }

    def report(detoured: bool, before: dict, after: dict) -> dict:
        return {
            "status": "blocked" if detoured else "ok",
            "worker_execution": {
                "prepass": "detoured" if detoured else "actual-aex",
                "prepass_calls": 1, "prepass_detour_calls": 1 if detoured else 0,
                "b150_returns": 1,
            },
            "b150_input_capture": [{
                "abi": {"width": 1, "row_limit": 1, "row_start": 0, "row_end": 1},
                "rows": [{"source_rgba_f32": [0.0, 0.0, 0.0, 1.0], "scalar_a_f32": 0.0, "scalar_b_f32": 1.0}],
                "context_fields": {"left_span_i32": 0, "right_span_i32": 0},
                "worker_owned_before_return": before,
                "worker_owned_after_return": after,
            }],
        }

    live = report(False, capture("0x3f800000", "0x3f800000", 1.0), capture("0x40000000", "0x3f800000", 2.0))
    noop = report(True, capture("0x3f800000", "0x3f800000", 1.0), capture("0x3f800000", "0x3f800000", 1.0))
    differential = analyzer.analyze({"differential": {"live": live, "noop": noop}})
    assert differential["status"] == "pass", differential
    broken_diff = json.loads(json.dumps({"differential": {"live": live, "noop": noop}}))
    broken_diff["differential"]["live"]["b150_input_capture"][0]["worker_owned_after_return"]["nonzero_cells"][0]["rgba_f32_words"][0] = "0x00000000"
    assert analyzer.analyze(broken_diff)["status"] == "fail"

    with tempfile.TemporaryDirectory(prefix="radialblur_b150_runner_test_") as temp:
        root = Path(temp)
        runner = HERE / "run_radialblur_case0009_b150_differential.py"
        completed = subprocess.run([
            sys.executable, str(runner),
            "--combined-json", str(root / "combined.json"),
            "--output-json", str(root / "analysis.json"),
            "--output-md", str(root / "analysis.md"),
        ], check=False, capture_output=True, text=True)
        assert completed.returncode == 0, completed.stdout + completed.stderr
        result = json.loads((root / "analysis.json").read_text(encoding="utf-8"))
        assert result["evidence_class"] == "bounded_actual_aex_differential"
        assert result["status"] == "pass", result
        assert "differential" in json.loads((root / "combined.json").read_text(encoding="utf-8"))
        assert "bounded differential" in (root / "analysis.md").read_text(encoding="utf-8")
    print("[OK] case0009 sampler/prepass/writeback analyzer invariants")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
