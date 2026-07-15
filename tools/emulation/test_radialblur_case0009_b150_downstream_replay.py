#!/usr/bin/env python3
"""Focused tests for the bounded B150 downstream replay gate."""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_radialblur_case0009_b150_downstream_replay as replay  # noqa: E402


def sample(alpha: float) -> dict:
    output = [0.25, 0.5, 0.75, alpha] if alpha else [0.0, 0.0, 0.0, 0.0]
    return {
        "weights": [0.25, 0.25, 0.25, 0.25],
        "cells": {key: [0.25, 0.5, 0.75, alpha] for key in ("a0_r0", "a0_r1", "a1_r0", "a1_r1")},
        "sample_float": output,
        "trunc_u8": [max(0, min(255, int(value * 255))) for value in output],
    }


def side(alpha: float, detoured: bool) -> dict:
    return {
        "status": "blocked" if detoured else "ok",
        "plane_stats": {"informative_cell_count": 0 if detoured else 1},
        "plane_sha256": {"final_rgba_f32": "noop" if detoured else "live"},
        "bounded_output_samples": [{"xy": [7, 0], "status": "sampled", "sample": sample(alpha)}],
        "worker_execution": {"prepass": "detoured" if detoured else "actual-aex", "b150_returns": 1,
                              "prepass_detour_calls": 1 if detoured else 0},
    }


def main() -> int:
    document = {"differential": {"live": side(1.0, False), "noop": side(0.0, True)}}
    result = replay.analyze(document)
    assert result["status"] == "pass", result
    broken = json.loads(json.dumps(document))
    broken["differential"]["live"]["bounded_output_samples"][0]["sample"]["sample_float"][0] = 0.0
    assert replay.analyze(broken)["status"] == "fail"
    print("[OK] B150 downstream portable replay gate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
