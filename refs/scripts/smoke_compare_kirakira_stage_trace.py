#!/usr/bin/env python3
"""Smoke-test scripts/compare_kirakira_stage_trace.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


REQUEST_ID = "kirakira_fun_181150790_stage_values_20260620"


def main() -> int:
    repo = Path(__file__).resolve().parents[2]
    py = sys.executable
    with tempfile.TemporaryDirectory(prefix="olmkirakira_stage_compare_smoke_") as tmp:
        tmp_path = Path(tmp)
        summary = tmp_path / "runtime_summary.json"
        local_trace = tmp_path / "trace.json"
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
                            "summary": "synthetic stage trace",
                            "observations": {
                                "case_id": "kk_vertical_len50_brightness1_strength100",
                                "fun_181150790_entry": {
                                    "ray_length": 50,
                                    "angle_degrees_or_radians": 90.0,
                                    "affine_forward_matrix": [1.0, 0.0, 0.0, 0.0, 1.0, 0.0],
                                    "affine_back_matrix": [1.0, -0.0, 0.0, -0.0, 1.0, 0.0],
                                    "forward_dsize": [1924, 1924],
                                    "back_dsize": [1924, 1924],
                                    "source_roi_rect": [2, 422, 1920, 1080],
                                    "final_copy_rect": [2, 422, 1920, 1080],
                                },
                                "witness_pixels": [{"label": "center", "after_box_3_float": 0.25}],
                                "boxfilter_calls": [{"index": 1, "selected_branch": "FUN_1812e39d0"}],
                                "aggregation_and_compose": {
                                    "fun_18114fd90_sample_outputs": [{"xy": [960, 540], "rgba": [0.1, 0.1, 0.1, 1.0]}]
                                },
                            },
                        }
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        local_trace.write_text(
            json.dumps(
                {
                    "kind": "olmkirakira_opencv_two_temp_stage_trace",
                    "rays": [
                        {
                            "ray": "vertical",
                            "length": 50,
                            "angle": 90.0,
                            "source_size": [1920, 1080],
                            "temp_size": [1924, 1924],
                            "center": [962.0, 962.0],
                            "copy_origin": [2, 422],
                            "forward_matrix": [1.0, 0.0, 0.0, 0.0, 1.0, 0.0],
                            "back_matrix": [1.0, -0.0, 0.0, -0.0, 1.0, 0.0],
                            "sample_points": [
                                {"label": "center", "values": {"after_box_3": 0.25}},
                                {"label": "ray_length_up", "values": {"after_box_3": 0.125}},
                            ],
                        },
                        {
                            "stage": "aggregation_and_compose",
                            "compose_mode": "aex-screen-over",
                            "scale": 0.62,
                            "sample_points": [
                                {
                                    "label": "center",
                                    "values": {
                                        "source_rgba": [0.0, 0.0, 0.0, 1.0],
                                        "glow_rgba": [0.1, 0.1, 0.1, 1.0],
                                        "out_rgba_float": [0.1, 0.1, 0.1, 1.0],
                                        "out_rgba_u8": [26, 26, 26, 255],
                                    },
                                }
                            ],
                        },
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        proc = subprocess.run(
            [
                py,
                "scripts/compare_kirakira_stage_trace.py",
                "--runtime-summary-json",
                str(summary),
                "--local-trace-json",
                str(local_trace),
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
        if comparison.get("likely_next_focus") != "boxfilter-stage-values":
            print("[FAIL] comparison did not choose expected next focus")
            return 1
        markdown = output_md.read_text(encoding="utf-8")
        for needle in ("OLMKiraKira Stage Trace Comparison", "Ray Helper", "BoxFilter calls"):
            if needle not in markdown:
                print(f"[FAIL] comparison Markdown missing: {needle}")
                return 1
    print("[OK] KiraKira stage trace comparison smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
