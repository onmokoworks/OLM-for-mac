#!/usr/bin/env python3
"""Smoke-test the RadialBlur full-frame typed comparator."""

from __future__ import annotations

import json
import copy
import subprocess
import sys
import tempfile
from pathlib import Path


def cell(slot: str, value: float) -> dict:
    return {"slot": slot, "cell_id": f"cell-{slot}", "bilinear_weight": 0.25, "accum_rgba_f32": [value] * 4, "denom_f32": value, "valid_f32": value, "final_rgba_f32": [value] * 4}


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="radialblur_typed_compare_") as tmp:
        tmp = Path(tmp)
        points = []
        for x in (7, 8, 24):
            points.append({"xy": [x, 0], "inverse_sample_xy": [float(x), 0.0], "cells": [cell(slot, 1.0) for slot in ("00", "10", "01", "11")], "observed_rgba8": [21, 3, 3, 255], "final_alpha_sum": 1.0, "pre_byte_alpha": 1.0})
        local = {"kind": "olmradialblur_case0009_fullframe_postnorm_typed_local_model", "schema": 1, "model": {"points": points}}
        returned = {"kind": "olm_runtime_trace_result", "schema": 1, "results": [{"request_id": "olmradialblur_case0009_fullframe_postnorm_typed_20260710", "observations": {"classification": "answered", "same_run": True, "run_id": "smoke", "hook_or_watchpoint": "0x180005d99", "console_artifact": "console.txt", "geometry": {"width": 1920, "height": 1080, "mode": "full-frame"}, "points": copy.deepcopy(points)}}]}
        returned["results"][0]["observations"]["points"][0]["cells"][0]["valid_f32"] = 0.5
        local_path, return_path = tmp / "local.json", tmp / "return.json"
        local_path.write_text(json.dumps(local), encoding="utf-8")
        return_path.write_text(json.dumps(returned), encoding="utf-8")
        out_json, out_md = tmp / "out.json", tmp / "out.md"
        proc = subprocess.run([sys.executable, str(root / "scripts/compare_olmradialblur_case0009_fullframe_postnorm_typed.py"), "--local-model", str(local_path), "--return-json", str(return_path), "--output-json", str(out_json), "--output-md", str(out_md)], cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print(proc.stdout, end="")
        if proc.returncode != 0:
            raise AssertionError("comparator should produce a report for a complete return")
        report = json.loads(out_json.read_text(encoding="utf-8"))
        assert report["classification"] == "first-difference-found"
        assert report["first_difference"] == {"xy": [7, 0], "boundary": "valid", "detail": {"slot": "00", "field": "valid_f32", "local": 1.0, "return": 0.5}}
        returned["results"][0]["observations"]["classification"] = "answered_partial"
        return_path.write_text(json.dumps(returned), encoding="utf-8")
        blocked = subprocess.run([sys.executable, str(root / "scripts/compare_olmradialblur_case0009_fullframe_postnorm_typed.py"), "--local-model", str(local_path), "--return-json", str(return_path), "--output-json", str(out_json), "--output-md", str(out_md)], cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if blocked.returncode != 2 or "FAIL-CLOSED" not in blocked.stdout:
            raise AssertionError("incomplete return must fail closed")
    print("[OK] RadialBlur case_0009 full-frame typed comparator smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
