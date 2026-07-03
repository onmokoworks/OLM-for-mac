#!/usr/bin/env python3
"""Smoke-test scripts/compare_distancegradation_trace.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


REQUEST_ID = "olmdistancegradation_field_prep_runtime_trace_20260619"
CONSTANT_REQUEST_ID = "olmdistancegradation_16bpc_constant_boundary_witness_20260630"
THRESHOLD_REQUEST_ID = "olmdistancegradation_case0023_threshold_family_followup_20260701"
TRIPLET_XY_REQUEST_ID = "olmdistancegradation_case0023_triplet_xy_compose_hook_followup_20260701"


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
        summary.write_text(
            json.dumps(
                {
                    "kind": "olm_runtime_trace_return_summary",
                    "results": [
                        {
                            "request_id": REQUEST_ID,
                            "status": "answered_partial",
                            "summary": "synthetic sparse DistanceGradation trace",
                            "observations": {
                                "requested_for_each_pixel": {
                                    "distance_field_before_constant_rgba_or_mat_values": [
                                        "not isolated; upstream pre-Constant field value still needs debugger trace"
                                    ],
                                    "distance_field_after_constant_rgba_or_mat_values": [
                                        "not isolated; current best guard says Constant mode binarizes upstream"
                                    ],
                                    "distance_transform_call": {
                                        "dist_type": "inferred OpenCV DIST_L2; Windows runtime arg still untraced",
                                    },
                                    "gaussian_blur_call_if_case_0029": {
                                        "border_type": "likely BORDER_REFLECT_101; runtime arg still untraced",
                                    },
                                    "fun_181170870_field_pixel_bytes": [
                                        "not isolated; decomp shows distance field is read from green byte"
                                    ],
                                }
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
        if comparison.get("likely_next_focus") != "trace-too-sparse":
            print("[FAIL] placeholder observations should stay trace-too-sparse")
            return 1
        summary.write_text(
            json.dumps(
                {
                    "kind": "olm_runtime_trace_return_summary",
                    "results": [
                        {
                            "request_id": CONSTANT_REQUEST_ID,
                            "status": "answered",
                            "summary": "synthetic constant-boundary witness",
                            "observations": {
                                "cases": [
                                    {"case_id": "olmdistancegradation_extended__case_0020"},
                                    {"case_id": "olmdistancegradation_extended__case_0022"},
                                ],
                                "requested_for_each_pixel": {
                                    "binary_mask_before_distance_transform": [
                                        {"case_id": "olmdistancegradation_extended__case_0020", "x": 434, "y": 676, "mask": 1}
                                    ],
                                    "inside_or_outside_distance_before_threshold": [
                                        {"case_id": "olmdistancegradation_extended__case_0020", "x": 434, "y": 676, "inside": 78.00641, "outside": 0.0}
                                    ],
                                    "comparison_rule": "<= inside threshold for In mode",
                                    "selected_side_inside_outside_or_both": "inside",
                                    "final_rgba16": [
                                        {"case_id": "olmdistancegradation_extended__case_0020", "x": 434, "y": 676, "rgba": [7195, 0, 61165, 65535]}
                                    ],
                                },
                                "case_level_contract": {
                                    "must_explain": [
                                        "threshold ownership at the boundary"
                                    ]
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
        if comparison.get("request_id") != CONSTANT_REQUEST_ID:
            print("[FAIL] constant-boundary comparison request_id mismatch")
            return 1
        if comparison.get("likely_next_focus") != "constant-boundary-threshold-ownership":
            print("[FAIL] constant-boundary witness should classify as threshold ownership")
            return 1
        summary.write_text(
            json.dumps(
                {
                    "kind": "olm_runtime_trace_return_summary",
                    "results": [
                        {
                            "request_id": THRESHOLD_REQUEST_ID,
                            "status": "answered_partial",
                            "summary": "synthetic threshold-family triplet witness",
                            "observations": {
                                "case": {
                                    "case_id": "olmdistancegradation_extended__case_0023",
                                    "params": {
                                        "in_out": 3,
                                        "inside_threshold": 36,
                                        "outside_threshold": 0,
                                        "interpolation_mode": 1,
                                        "render_mode": 1,
                                        "use_background_color": 1,
                                    },
                                },
                                "threshold_triplet": [
                                    {"role": "below_threshold_same_row", "x": 414, "y": 393},
                                    {"role": "first_above_threshold_same_row", "x": 415, "y": 393},
                                    {"role": "deeper_plateau_same_row", "x": 416, "y": 393},
                                ],
                                "requested_for_each_pixel": {
                                    "raw_inside_distance_before_threshold": [
                                        {"x": 414, "y": 393, "value": 35.0142822},
                                        {"x": 415, "y": 393, "value": 36.0138855},
                                        {"x": 416, "y": 393, "value": 37.0135117},
                                    ],
                                    "raw_outside_distance_before_threshold": [
                                        {"x": 414, "y": 393, "value": 0.0},
                                        {"x": 415, "y": 393, "value": 0.0},
                                        {"x": 416, "y": 393, "value": 0.0},
                                    ],
                                    "helper_stage_field_value_before_compose": [
                                        {"x": 414, "y": 393, "value": 0.0},
                                        {"x": 415, "y": 393, "value": 1.0},
                                        {"x": 416, "y": 393, "value": 1.0},
                                    ],
                                    "threshold_equality_or_plateau_decision": "ownership flips between 35.014 and 36.013 at helper stage",
                                    "constant_binary_fork_order": "binary fork observes field after ownership decision",
                                    "field_value_finally_consumed_by_FUN_181170480": [
                                        {"x": 414, "y": 393, "value": 0.0},
                                        {"x": 415, "y": 393, "value": 1.0},
                                        {"x": 416, "y": 393, "value": 1.0},
                                    ],
                                    "fun_181170480_output_rgba_before_word_store": [
                                        {"x": 414, "y": 393, "rgba": [7195.0, 0.0, 61165.0, 65535.0]},
                                        {"x": 415, "y": 393, "rgba": [65535.0, 0.0, 0.0, 65535.0]},
                                        {"x": 416, "y": 393, "rgba": [65535.0, 0.0, 0.0, 65535.0]},
                                    ],
                                    "final_rgba16": [
                                        {"x": 414, "y": 393, "rgba": [7195, 0, 61165, 65535]},
                                        {"x": 415, "y": 393, "rgba": [65535, 0, 0, 65535]},
                                        {"x": 416, "y": 393, "rgba": [65535, 0, 0, 65535]},
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
        if comparison.get("request_id") != THRESHOLD_REQUEST_ID:
            print("[FAIL] threshold-family comparison request_id mismatch")
            return 1
        if comparison.get("likely_next_focus") != "constant-boundary-threshold-ownership":
            print("[FAIL] threshold-family witness should classify as threshold ownership")
            return 1
        if "local_case0023_threshold_context" not in comparison:
            print("[FAIL] threshold-family comparison should include local case_0023 context")
            return 1
        markdown = output_md.read_text(encoding="utf-8")
        for needle in ("Local case_0023 Context", "Threshold triplet", "Live Mac triplet"):
            if needle not in markdown:
                print(f"[FAIL] threshold-family Markdown missing: {needle}")
                return 1
        summary.write_text(
            json.dumps(
                {
                    "kind": "olm_runtime_trace_return_summary",
                    "results": [
                        {
                            "request_id": TRIPLET_XY_REQUEST_ID,
                            "status": "failed_partial",
                            "summary": "synthetic triplet xy compose followup with endpoint flip confirmed but case-local compose hook still missing",
                            "observations": {
                                "case": {
                                    "case_id": "olmdistancegradation_extended__case_0023",
                                    "params": {
                                        "in_out": 3,
                                        "inside_threshold": 36,
                                        "outside_threshold": 0,
                                        "interpolation_mode": 1,
                                        "render_mode": 1,
                                        "use_background_color": 1,
                                    },
                                },
                                "requested_for_each_pixel": {
                                    "threshold_values": {"inside_threshold": 36, "outside_threshold": 0},
                                    "comparison_rule": "endpoint-observed only; direct helper ownership not isolated",
                                    "selected_side_for_both_mode": "blue_low_endpoint_observed",
                                    "field_value_finally_consumed_by_FUN_181170480": None,
                                    "fun_181170480_output_rgba_before_word_store": [None, None, None, None],
                                    "final_rgba16": [7195, 0, 61165, 65535],
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
        if comparison.get("request_id") != TRIPLET_XY_REQUEST_ID:
            print("[FAIL] triplet-xy comparison request_id mismatch")
            return 1
        if comparison.get("likely_next_focus") != "threshold-normalization":
            print("[FAIL] triplet-xy followup should stay on threshold-normalization")
            return 1
    print("[OK] DistanceGradation trace comparison smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
