#!/usr/bin/env python3
"""Smoke-test scripts/compare_distancegradation_trace.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


REQUEST_ID = "olmdistancegradation_field_prep_runtime_trace_20260619"


def main() -> int:
    repo = Path(__file__).resolve().parents[2]
    py = sys.executable
    with tempfile.TemporaryDirectory(prefix="olmdistancegradation_compare_smoke_") as tmp:
        tmp_path = Path(tmp)
        summary = tmp_path / "runtime_summary.json"
        output_json = tmp_path / "comparison.json"
        output_md = tmp_path / "comparison.md"
        summary.write_text(
            json.dumps(
                {
                    "kind": "olm_runtime_trace_return_summary",
                    "results": [
                        {
                            "request_id": REQUEST_ID,
                            "status": "answered",
                            "summary": "synthetic DistanceGradation field prep trace",
                            "source_file": "synthetic.zip",
                            "observations": {
                                "cases": ["case_0020", "case_0022", "case_0029"],
                                "requested_for_each_pixel": {
                                    "source_input_rgba_8bit": [
                                        {"case_id": "case_0020", "x": 64, "y": 32, "rgba": [0, 0, 0, 255]}
                                    ],
                                    "distance_field_before_constant_rgba_or_mat_values": [
                                        {"case_id": "case_0020", "x": 64, "y": 32, "value": 0.0}
                                    ],
                                    "distance_field_after_constant_rgba_or_mat_values": [
                                        {"case_id": "case_0020", "x": 64, "y": 32, "value": 255.0}
                                    ],
                                    "distance_transform_call": "not reached in this synthetic branch",
                                    "threshold_and_normalization": None,
                                    "gaussian_blur_call_if_case_0029": None,
                                    "fun_181170870_field_pixel_bytes": [
                                        {"case_id": "case_0020", "x": 64, "y": 32, "g": 255}
                                    ],
                                    "final_rgba_8bit": [
                                        {"case_id": "case_0020", "x": 64, "y": 32, "rgba": [255, 255, 255, 255]}
                                    ],
                                },
                            },
                        }
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        proc = subprocess.run(
            [
                py,
                "scripts/compare_distancegradation_trace.py",
                "--runtime-summary-json",
                str(summary),
                "--output-json",
                str(output_json),
                "--output-md",
                str(output_md),
            ],
            cwd=repo,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
        if proc.returncode != 0:
            return proc.returncode
        comparison = json.loads(output_json.read_text(encoding="utf-8"))
        if comparison.get("request_id") != REQUEST_ID:
            print("[FAIL] comparison request_id mismatch")
            return 1
        if comparison.get("likely_next_focus") != "constant-field-prep":
            print("[FAIL] comparison did not choose expected next focus")
            return 1
        markdown = output_md.read_text(encoding="utf-8")
        for needle in ("OLMDistanceGradation Trace Comparison", "Local Assumptions", "Field values"):
            if needle not in markdown:
                print(f"[FAIL] comparison Markdown missing: {needle}")
                return 1
    print("[OK] DistanceGradation trace comparison smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
