#!/usr/bin/env python3
"""Smoke-test scripts/compare_kirakira_stage_trace.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


REQUEST_ID = "kirakira_fun_181150790_stage_values_20260620"
DEEP_REQUEST_ID = "kirakira_fun_181150790_deep_stage_values_20260621"


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
        sparse_summary = tmp_path / "runtime_summary_sparse.json"
        sparse_output_json = tmp_path / "comparison_sparse.json"
        sparse_summary.write_text(
            json.dumps(
                {
                    "kind": "olm_runtime_trace_return_summary",
                    "results": [
                        {
                            "request_id": REQUEST_ID,
                            "status": "answered",
                            "summary": "function entry did not isolate stage values",
                            "observations": {
                                "case_id": "kk_vertical_len50_brightness1_strength100",
                                "fun_181150790_entry": {
                                    "ray_length": None,
                                    "affine_forward_matrix": "not isolated",
                                    "affine_back_matrix": "not isolated",
                                    "forward_dsize": [1924, 1924],
                                },
                                "witness_pixels": ["not isolated"],
                                "boxfilter_calls": [
                                    {
                                        "index": 1,
                                        "selected_branch": "not fully decoded",
                                        "sample_values": "not isolated",
                                    }
                                ],
                                "aggregation_and_compose": {"sample_outputs": "not isolated"},
                            },
                        }
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        sparse_proc = subprocess.run(
            [
                py,
                "scripts/compare_kirakira_stage_trace.py",
                "--runtime-summary-json",
                str(sparse_summary),
                "--local-trace-json",
                str(local_trace),
                "--output-json",
                str(sparse_output_json),
            ],
            cwd=repo,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(sparse_proc.stdout, end="" if sparse_proc.stdout.endswith("\n") else "\n")
        if sparse_proc.returncode != 0:
            return sparse_proc.returncode
        sparse_comparison = json.loads(sparse_output_json.read_text(encoding="utf-8"))
        if sparse_comparison.get("likely_next_focus") != "trace-too-sparse":
            print("[FAIL] sparse placeholder trace was treated as concrete evidence")
            return 1
        deep_summary = tmp_path / "runtime_summary_deep.json"
        deep_output_json = tmp_path / "comparison_deep.json"
        deep_summary.write_text(
            json.dumps(
                {
                    "kind": "olm_runtime_trace_return_summary",
                    "results": [
                        {
                            "request_id": DEEP_REQUEST_ID,
                            "status": "answered_partial",
                            "summary": "synthetic deep stage trace",
                            "observations": {
                                "case_id": "kk_vertical_len50_brightness1_strength100",
                                "stage_values": {
                                    "after_box_filter_pass_1_ret_1151174": {
                                        "center_temp_962_962": {"float": 0.30, "hex": "0x1.333334p-2"},
                                        "ray_length_up_temp_962_912": {"float": 0.20, "hex": "0x1.99999ap-3"},
                                        "ray_length_right_temp_1012_962": {"float": 0.10, "hex": "0x1.99999ap-4"},
                                    },
                                    "after_box_filter_pass_2_ret_11511c7": {
                                        "center_temp_962_962": {"float": 0.28, "hex": "0x1.1eb852p-2"},
                                    },
                                    "after_box_filter_pass_3_ret_115121a": {
                                        "center_temp_962_962": {"float": 0.27, "hex": "0x1.147ae2p-2"},
                                    },
                                },
                            },
                        }
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        deep_proc = subprocess.run(
            [
                py,
                "scripts/compare_kirakira_stage_trace.py",
                "--runtime-summary-json",
                str(deep_summary),
                "--local-trace-json",
                str(local_trace),
                "--output-json",
                str(deep_output_json),
            ],
            cwd=repo,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(deep_proc.stdout, end="" if deep_proc.stdout.endswith("\n") else "\n")
        if deep_proc.returncode != 0:
            return deep_proc.returncode
        deep_comparison = json.loads(deep_output_json.read_text(encoding="utf-8"))
        if deep_comparison.get("request_id") != DEEP_REQUEST_ID:
            print("[FAIL] deep comparison request_id mismatch")
            return 1
        if deep_comparison.get("likely_next_focus") != "forward-warp-or-boxfilter-input":
            print("[FAIL] deep stage trace did not choose expected next focus")
            return 1
        if not deep_comparison.get("deep_stage_deltas"):
            print("[FAIL] deep stage trace did not compute deltas")
            return 1
    print("[OK] KiraKira stage trace comparison smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
