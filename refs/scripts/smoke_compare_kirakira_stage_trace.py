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
FORWARD_REQUEST_ID = "kirakira_forward_warp_box_input_20260621"
MICROPROBE_REQUEST_ID = "kirakira_boxfilter_pass1_microprobe_20260622"
AGG_REQUEST_ID = "kirakira_aggregation_compose_bt709_20260624"


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
        if "pass-by-pass boxFilter values" not in comparison.get("recommended_next_evidence", ""):
            print("[FAIL] comparison missing useful next-evidence recommendation")
            return 1
        markdown = output_md.read_text(encoding="utf-8")
        for needle in (
            "OLMKiraKira Stage Trace Comparison",
            "Ray Helper",
            "BoxFilter calls",
            "Recommended next evidence",
        ):
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
        if "Do not tune" not in sparse_comparison.get("recommended_next_evidence", ""):
            print("[FAIL] sparse trace did not get a stop/tune warning")
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
        matched_deep_summary = tmp_path / "runtime_summary_deep_matched.json"
        matched_deep_output_json = tmp_path / "comparison_deep_matched.json"
        matched_deep_summary.write_text(
            json.dumps(
                {
                    "kind": "olm_runtime_trace_return_summary",
                    "results": [
                        {
                            "request_id": DEEP_REQUEST_ID,
                            "status": "answered_partial",
                            "summary": "synthetic deep stage trace matched within float print precision",
                            "observations": {
                                "stage_values": {
                                    "after_box_filter_pass_3_ret_115121a": {
                                        "center_temp_962_962": {"float": 0.25000006, "hex": "3e800002"},
                                        "ray_length_up_temp_962_912": {"float": 0.12500006, "hex": "3e000004"},
                                    }
                                }
                            },
                        }
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        matched_deep_proc = subprocess.run(
            [
                py,
                "scripts/compare_kirakira_stage_trace.py",
                "--runtime-summary-json",
                str(matched_deep_summary),
                "--local-trace-json",
                str(local_trace),
                "--output-json",
                str(matched_deep_output_json),
            ],
            cwd=repo,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(matched_deep_proc.stdout, end="" if matched_deep_proc.stdout.endswith("\n") else "\n")
        if matched_deep_proc.returncode != 0:
            return matched_deep_proc.returncode
        matched_deep_comparison = json.loads(matched_deep_output_json.read_text(encoding="utf-8"))
        if matched_deep_comparison.get("likely_next_focus") != "ray-helper-stages-match-aggregation-or-compose":
            print("[FAIL] matched deep stage trace did not move downstream")
            return 1
        if matched_deep_comparison.get("first_divergence") is not None:
            print("[FAIL] matched deep stage trace reported a float-print divergence")
            return 1
        forward_summary = tmp_path / "runtime_summary_forward.json"
        forward_output_json = tmp_path / "comparison_forward.json"
        forward_output_md = tmp_path / "comparison_forward.md"
        forward_summary.write_text(
            json.dumps(
                {
                    "kind": "olm_runtime_trace_return_summary",
                    "results": [
                        {
                            "request_id": FORWARD_REQUEST_ID,
                            "status": "answered",
                            "summary": "synthetic forward warp and box input trace",
                            "observations": {
                                "first_divergence_classification": "center-copy",
                                "forward_warp": {
                                    "copy_origin": [2, 422],
                                    "source_roi_rect": [2, 422, 1920, 1080],
                                    "dsize": [1924, 1924],
                                    "matrix": [0.0, 1.0, 0.0, -1.0, 0.0, 1924.0],
                                },
                                "boxfilter_pass_1": {
                                    "selected_branch": "FUN_1812e39d0 / AVX2",
                                    "ksize": [50, 1],
                                    "anchor": [-1, -1],
                                    "normalize": True,
                                    "border_type": 4,
                                },
                                "witnesses": [
                                    {
                                        "label": "ray_length_up",
                                        "windows_observed": {
                                            "after_center_copy": 0.79773343,
                                            "after_forward_warp": 0.11764707,
                                            "before_box_1": 0.11764707,
                                            "after_box_1": 0.77863592,
                                        },
                                    }
                                ],
                            },
                        }
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        forward_proc = subprocess.run(
            [
                py,
                "scripts/compare_kirakira_stage_trace.py",
                "--runtime-summary-json",
                str(forward_summary),
                "--local-trace-json",
                str(local_trace),
                "--output-json",
                str(forward_output_json),
                "--output-md",
                str(forward_output_md),
            ],
            cwd=repo,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(forward_proc.stdout, end="" if forward_proc.stdout.endswith("\n") else "\n")
        if forward_proc.returncode != 0:
            return forward_proc.returncode
        forward_comparison = json.loads(forward_output_json.read_text(encoding="utf-8"))
        if forward_comparison.get("request_id") != FORWARD_REQUEST_ID:
            print("[FAIL] forward comparison request_id mismatch")
            return 1
        if forward_comparison.get("likely_next_focus") != "center-copy-or-boxfilter-input":
            print("[FAIL] forward trace did not choose expected next focus")
            return 1
        forward_markdown = forward_output_md.read_text(encoding="utf-8")
        for needle in ("Forward warp", "BoxFilter pass 1", "Forward-warp witnesses"):
            if needle not in forward_markdown:
                print(f"[FAIL] forward comparison Markdown missing: {needle}")
                return 1
        microprobe_summary = tmp_path / "runtime_summary_microprobe.json"
        microprobe_output_json = tmp_path / "comparison_microprobe.json"
        microprobe_output_md = tmp_path / "comparison_microprobe.md"
        microprobe_summary.write_text(
            json.dumps(
                {
                    "kind": "olm_runtime_trace_return_summary",
                    "results": [
                        {
                            "request_id": MICROPROBE_REQUEST_ID,
                            "status": "answered",
                            "summary": "synthetic pass-1 boxFilter microprobe",
                            "observations": {
                                "case_id": "kk_vertical_len50_brightness1_strength100",
                                "classification": "different-window | border-reflect101 | accumulator-precision | store-rounding | different-mat-stage | failed-to-isolate",
                                "boxfilter_pass_1": {
                                    "breakpoint_or_probe_site": "FUN_1812e39d0",
                                    "selected_path_or_nearest_offset": "avx2-row-sum",
                                    "accumulator_precision": "SIMD-lane",
                                },
                                "witnesses": [
                                    {
                                        "label": "center",
                                        "temp_xy": [962, 962],
                                        "local_after_box_1": 0.7871310114860535,
                                        "local_input_window": {
                                            "anchor_x": 25,
                                            "x_range_unbordered": [937, 986],
                                            "mean": 0.7871310114860535,
                                        },
                                        "resolved_source_x_range_after_border": [937, 986],
                                        "sample_summary": {
                                            "count": 50,
                                            "sum": 39.356550574302675,
                                            "min": 0.0,
                                            "max": 1.0,
                                            "hash": "synthetic",
                                        },
                                        "normalized_sum_before_store": 0.79479009,
                                        "stored_float_after_pass_1": 0.79479009,
                                    }
                                ],
                            },
                        }
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        microprobe_proc = subprocess.run(
            [
                py,
                "scripts/compare_kirakira_stage_trace.py",
                "--runtime-summary-json",
                str(microprobe_summary),
                "--local-trace-json",
                str(local_trace),
                "--output-json",
                str(microprobe_output_json),
                "--output-md",
                str(microprobe_output_md),
            ],
            cwd=repo,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(microprobe_proc.stdout, end="" if microprobe_proc.stdout.endswith("\n") else "\n")
        if microprobe_proc.returncode != 0:
            return microprobe_proc.returncode
        microprobe_comparison = json.loads(microprobe_output_json.read_text(encoding="utf-8"))
        if microprobe_comparison.get("request_id") != MICROPROBE_REQUEST_ID:
            print("[FAIL] microprobe comparison request_id mismatch")
            return 1
        if microprobe_comparison.get("likely_next_focus") != "boxfilter-pass1-accumulator-precision-or-store":
            print("[FAIL] microprobe trace did not choose expected next focus")
            return 1
        if "accumulator precision" not in microprobe_comparison.get("recommended_next_evidence", ""):
            print("[FAIL] microprobe trace missing accumulator/store recommendation")
            return 1
        microprobe_markdown = microprobe_output_md.read_text(encoding="utf-8")
        for needle in ("Microprobe witnesses", "Microprobe classification", "BoxFilter pass 1"):
            if needle not in microprobe_markdown:
                print(f"[FAIL] microprobe comparison Markdown missing: {needle}")
                return 1
        upstream_summary = tmp_path / "runtime_summary_microprobe_upstream.json"
        upstream_output_json = tmp_path / "comparison_microprobe_upstream.json"
        upstream_output_md = tmp_path / "comparison_microprobe_upstream.md"
        upstream_summary.write_text(
            json.dumps(
                {
                    "kind": "olm_runtime_trace_return_summary",
                    "results": [
                        {
                            "request_id": MICROPROBE_REQUEST_ID,
                            "status": "answered",
                            "summary": "synthetic pass-1 source window proves upstream difference",
                            "observations": {
                                "witness_decision": {
                                    "different_contributing_window": False,
                                    "different_border_reflection": False,
                                    "different_accumulator_or_store": False,
                                    "different_mat_or_address_stage": False,
                                },
                                "witness_proofs": [
                                    {
                                        "label": "center",
                                        "temp_xy": [962, 962],
                                        "x_range_unbordered": [937, 986],
                                        "source_window_mean_delta_vs_local": 0.007659090063365903,
                                        "after_pass_1_delta_vs_local": 0.007659078513946538,
                                        "mean_delta_matches_output_delta": True,
                                    }
                                ],
                                "upstream_signal": {
                                    "recommended_next_trace": "Move earlier than boxFilter toward pre-pass fill."
                                },
                            },
                        }
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        upstream_proc = subprocess.run(
            [
                py,
                "scripts/compare_kirakira_stage_trace.py",
                "--runtime-summary-json",
                str(upstream_summary),
                "--local-trace-json",
                str(local_trace),
                "--output-json",
                str(upstream_output_json),
                "--output-md",
                str(upstream_output_md),
            ],
            cwd=repo,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(upstream_proc.stdout, end="" if upstream_proc.stdout.endswith("\n") else "\n")
        if upstream_proc.returncode != 0:
            return upstream_proc.returncode
        upstream_comparison = json.loads(upstream_output_json.read_text(encoding="utf-8"))
        if upstream_comparison.get("likely_next_focus") != "boxfilter-pass1-upstream-source-buffer-content":
            print("[FAIL] upstream microprobe did not choose expected next focus")
            return 1
        if "pre-boxFilter source fill" not in upstream_comparison.get("recommended_next_evidence", ""):
            print("[FAIL] upstream microprobe missing pre-boxFilter recommendation")
            return 1
        upstream_markdown = upstream_output_md.read_text(encoding="utf-8")
        for needle in ("Witness decision", "Upstream signal"):
            if needle not in upstream_markdown:
                print(f"[FAIL] upstream microprobe Markdown missing: {needle}")
                return 1
        agg_summary = tmp_path / "runtime_summary_aggregation.json"
        agg_output_json = tmp_path / "comparison_aggregation.json"
        agg_output_md = tmp_path / "comparison_aggregation.md"
        agg_summary.write_text(
            json.dumps(
                {
                    "kind": "olm_runtime_trace_return_summary",
                    "results": [
                        {
                            "request_id": AGG_REQUEST_ID,
                            "status": "answered",
                            "source_file": "return/request_package/RETURN_RUNTIME_TRACE_TEMPLATE.json",
                            "summary": "template row that should not win",
                            "observations": {"fun_18114fd90_aggregation": {"entry": {"brightness_or_param_10": None}}},
                        },
                        {
                            "request_id": AGG_REQUEST_ID,
                            "status": "answered_partial",
                            "source_file": "return/RETURN_RUNTIME_TRACE_RESULT.json",
                            "summary": "synthetic fd90 aggregation trace",
                            "observations": {
                                "case_id": "kk_vertical_len50_brightness1_strength100",
                                "fun_18114fd90_aggregation": {
                                    "entry": {"brightness_or_param_10": 1, "width": 1920, "height": 1080},
                                    "sample_outputs": [
                                        {
                                            "label": "center",
                                            "source_xy": [960, 540],
                                            "ray_inputs": [0.71891218, 0, 0, 0, 0],
                                            "post_normalize_glow_rgba": [1, 1, 1, 0.71891218],
                                        }
                                    ],
                                },
                                "merge_mode_1_compose": {
                                    "internal_compose_float_status": "not isolated by this breakpoint set",
                                    "sample_inputs_outputs": [
                                        {
                                            "label": "center",
                                            "source_xy": [960, 540],
                                            "source_rgba_u8": [30, 30, 30, 255],
                                            "final_writeback_or_png_rgba": [124, 124, 124, 255],
                                        }
                                    ],
                                },
                            },
                        },
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        agg_proc = subprocess.run(
            [
                py,
                "scripts/compare_kirakira_stage_trace.py",
                "--runtime-summary-json",
                str(agg_summary),
                "--local-trace-json",
                str(local_trace),
                "--output-json",
                str(agg_output_json),
                "--output-md",
                str(agg_output_md),
            ],
            cwd=repo,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(agg_proc.stdout, end="" if agg_proc.stdout.endswith("\n") else "\n")
        if agg_proc.returncode != 0:
            return agg_proc.returncode
        agg_comparison = json.loads(agg_output_json.read_text(encoding="utf-8"))
        if agg_comparison.get("request_id") != AGG_REQUEST_ID:
            print("[FAIL] aggregation comparison request_id mismatch")
            return 1
        if agg_comparison.get("likely_next_focus") != "fd90-aggregation-grounded-compose-scale":
            print("[FAIL] aggregation comparison did not choose expected next focus")
            return 1
        agg_markdown = agg_output_md.read_text(encoding="utf-8")
        for needle in ("FUN_18114fd90 aggregation", "Merge mode 1 compose", "0.71891218"):
            if needle not in agg_markdown:
                print(f"[FAIL] aggregation comparison Markdown missing: {needle}")
                return 1
    print("[OK] KiraKira stage trace comparison smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
