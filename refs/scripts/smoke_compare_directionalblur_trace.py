#!/usr/bin/env python3
"""Smoke-test scripts/compare_directionalblur_trace.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


DENSE_REQUEST_ID = "olmdirectionalblur_dense_sampler_trace_20260620"
HELPER_GATE_REQUEST_ID = "olmdirectionalblur_angle0_helper_gate_retry_20260702"
SINGLE_SHOT_REQUEST_ID = "olmdirectionalblur_angle0_single_shot_witness_20260708"
RESIDUAL_REQUEST_ID = "olmdirectionalblur_helper_coverage_witness_20260630"


def run_compare(
    repo: Path,
    py: str,
    output_json: Path,
    output_md: Path,
    *,
    summary: Path | None = None,
    witness: Path | None = None,
) -> dict:
    cmd = [
        py,
        "scripts/compare_directionalblur_trace.py",
    ]
    if summary is not None:
        cmd.extend(["--runtime-summary-json", str(summary)])
    if witness is not None:
        cmd.extend(["--witness-json", str(witness)])
    cmd.extend(
        [
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
        ]
    )
    proc = subprocess.run(
        cmd,
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)
    return json.loads(output_json.read_text(encoding="utf-8"))


def assert_focus(comparison: dict, expected: str) -> None:
    if comparison.get("likely_next_focus") != expected:
        print(f"[FAIL] expected focus {expected}, got {comparison.get('likely_next_focus')}")
        raise SystemExit(1)


def assert_request(comparison: dict, expected: str) -> None:
    if comparison.get("request_id") != expected:
        print(f"[FAIL] expected request_id {expected}, got {comparison.get('request_id')}")
        raise SystemExit(1)


def main() -> int:
    repo = Path(__file__).resolve().parents[2]
    py = sys.executable
    with tempfile.TemporaryDirectory(prefix="olmdirectionalblur_compare_smoke_") as tmp:
        tmp_path = Path(tmp)
        summary = tmp_path / "runtime_summary.json"
        witness = tmp_path / "witness.json"
        output_json = tmp_path / "comparison.json"
        output_md = tmp_path / "comparison.md"

        summary.write_text(
            json.dumps(
                {
                    "kind": "olm_runtime_trace_return_summary",
                    "results": [
                        {
                            "request_id": DENSE_REQUEST_ID,
                            "status": "answered",
                            "summary": "synthetic DirectionalBlur dense trace",
                            "observations": {
                                "cases": [
                                    {
                                        "case_id": "db_diagonal_alpha_ramp",
                                        "witness_pixels": [
                                            {
                                                "x": 320,
                                                "y": 240,
                                                "loop_bounds_or_sample_count": 17,
                                                "intermediate_values": {"denom": 0.625, "weight": 0.8125},
                                                "pre_writeback_rgba_float_hex": [
                                                    "0x1.0p-1",
                                                    "0x1.0p-2",
                                                    "0x0p+0",
                                                    "0x1.0p+0",
                                                ],
                                                "final_rgba": [128, 64, 0, 255],
                                            }
                                        ],
                                    }
                                ]
                            },
                        }
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        witness.write_text(
            json.dumps(
                {
                    "kind": "olmdirectionalblur_cli_witness",
                    "algorithm_family": "render_rotated",
                    "width": 640,
                    "height": 480,
                    "pad_width": 1024,
                    "pad_height": 512,
                    "crop_x": 128,
                    "crop_y": 16,
                    "front_strength_scaled": 17,
                    "back_strength_scaled": 0,
                    "strength_scale": 1.0,
                    "front_strength_rgb_denom": False,
                    "aex_two_stage_output": False,
                    "points": [
                        {
                            "x": 320,
                            "y": 240,
                            "pad_x": 448,
                            "pad_y": 256,
                            "source_alpha": 1.0,
                            "accum_sum_denominator": 17.0,
                            "effective_rgb_denominator": 17.0,
                            "accum_alpha": 1.0,
                            "source_rgb": [0.5, 0.25, 0.0],
                            "accum_rgb": [8.5, 4.25, 0.0],
                            "blurred_rgba_pre_rotateback": [0.5, 0.25, 0.0, 1.0],
                            "final_sample_rgba_pre_quant": [0.5, 0.25, 0.0, 1.0],
                            "final_rgba8": [128, 64, 0, 255],
                        },
                        {
                            "x": 99,
                            "y": 77,
                            "pad_x": 227,
                            "pad_y": 93,
                            "source_alpha": 0.5,
                            "accum_sum_denominator": 9.0,
                            "effective_rgb_denominator": 9.0,
                            "accum_alpha": 0.5,
                            "source_rgb": [0.1, 0.2, 0.3],
                            "accum_rgb": [0.9, 1.8, 2.7],
                            "blurred_rgba_pre_rotateback": [0.1, 0.2, 0.3, 0.5],
                            "final_sample_rgba_pre_quant": [0.1, 0.2, 0.3, 0.5],
                            "final_rgba8": [26, 51, 77, 128],
                        },
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        comparison = run_compare(repo, py, output_json, output_md, summary=summary, witness=witness)
        assert_request(comparison, DENSE_REQUEST_ID)
        assert_focus(comparison, "sampler-or-writeback-values")
        if "concrete sampler" not in comparison.get("recommended_next_evidence", ""):
            print("[FAIL] dense trace missing sampler next-evidence recommendation")
            return 1
        cross = comparison.get("local_vs_windows") or []
        if len(cross) != 2 or not cross[0].get("windows_match_present") or cross[1].get("windows_match_present"):
            print("[FAIL] dense trace local/windows coordinate matching did not behave as expected")
            return 1
        final_cmp = (((cross[0].get("field_comparison") or {}).get("final_rgba8")) or {}).get("windows")
        if final_cmp != [128, 64, 0, 255]:
            print(f"[FAIL] dense trace final RGBA cross-compare mismatch: {final_cmp}")
            return 1
        markdown = output_md.read_text(encoding="utf-8")
        for needle in (
            "OLMDirectionalBlur Trace Comparison",
            "Windows Observations",
            "Local CLI Witness",
            "Coordinate Cross-Compare",
            "sampler-or-writeback",
            "Recommended next evidence",
        ):
            if needle not in markdown:
                print(f"[FAIL] comparison Markdown missing: {needle}")
                return 1

        summary.write_text(
            json.dumps(
                {
                    "kind": "olm_runtime_trace_return_summary",
                    "results": [
                        {
                            "request_id": DENSE_REQUEST_ID,
                            "status": "answered",
                            "summary": "synthetic sparse DirectionalBlur trace",
                            "observations": {
                                "cases": [
                                    {
                                        "case_id": None,
                                        "witness_pixels": [
                                            {
                                                "x": "not traced / not isolated",
                                                "y": "not traced / not isolated",
                                                "pre_writeback_rgba_float_hex": [
                                                    "not traced / not isolated",
                                                    "not traced / not isolated",
                                                ],
                                                "final_rgba": ["not traced / not isolated"],
                                                "loop_bounds_or_sample_count": "not traced / not isolated",
                                            }
                                        ],
                                    }
                                ]
                            },
                        }
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        comparison = run_compare(repo, py, output_json, output_md, summary=summary)
        assert_request(comparison, DENSE_REQUEST_ID)
        assert_focus(comparison, "trace-structure-present-values-missing")
        if "typed numeric witness values" not in comparison.get("recommended_next_evidence", ""):
            print("[FAIL] sparse trace missing typed-value recommendation")
            return 1

        summary.write_text(
            json.dumps(
                {
                    "kind": "olm_runtime_trace_return_summary",
                    "results": [
                        {
                            "request_id": DENSE_REQUEST_ID,
                            "status": "live_attempt_failed_before_module_load",
                            "summary": "AE crashed before OLMDirectionalBlur module resolved",
                            "observations": {},
                        }
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        comparison = run_compare(repo, py, output_json, output_md, summary=summary)
        assert_request(comparison, DENSE_REQUEST_ID)
        assert_focus(comparison, "trace-failed-before-module-load")
        if "module loads" not in comparison.get("recommended_next_evidence", ""):
            print("[FAIL] failed load trace missing rerun recommendation")
            return 1

        summary.write_text(
            json.dumps(
                {
                    "kind": "olm_runtime_trace_return_summary",
                    "results": [
                        {
                            "request_id": HELPER_GATE_REQUEST_ID,
                            "status": "answered_partial",
                            "summary": "Loaded, hit helper/normalize/writeback breakpoints, but witness isolation failed due to gc auto-continue storm.",
                            "observations": {
                                "cases": [
                                    {
                                        "case_id": "db_existing_case_0001_software_pair",
                                        "witness_pixels": [
                                            {
                                                "x": 494,
                                                "y": 169,
                                                "branch_or_dispatch": "front-scatter-helper (offset +0x13e0)",
                                                "loop_bounds_or_sample_count": None,
                                                "sample_order": [],
                                                "pre_writeback_rgba_float_hex": [None, None, None, None],
                                                "final_rgba": None,
                                                "intermediate_values": {
                                                    "confirm_module_load": True,
                                                    "confirm_breakpoint_offsets": True,
                                                    "breakpoints_hit": ["+0x13e0", "+0x38d0", "+0x4a20", "+0x6b30", "+0x4880"],
                                                    "per_pixel_isolation": "not_achieved",
                                                    "hit_storm_note": "gc auto-continue caused excessive hits; need conditional breakpoints or single-shot approach per witness pixel",
                                                },
                                            },
                                            {
                                                "x": 579,
                                                "y": 169,
                                                "branch_or_dispatch": "front-scatter-helper (offset +0x13e0)",
                                                "loop_bounds_or_sample_count": None,
                                                "sample_order": [],
                                                "pre_writeback_rgba_float_hex": [None, None, None, None],
                                                "final_rgba": None,
                                                "intermediate_values": {
                                                    "confirm_module_load": True,
                                                    "confirm_breakpoint_offsets": True,
                                                    "per_pixel_isolation": "not_achieved",
                                                    "hit_storm_note": "same as (494,169); targeted single-shot followup still needed",
                                                },
                                            },
                                        ],
                                    }
                                ]
                            },
                        }
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        comparison = run_compare(repo, py, output_json, output_md, summary=summary)
        assert_request(comparison, HELPER_GATE_REQUEST_ID)
        assert_focus(comparison, "loader-breakpoints-answered-per-pixel-typed-witness-missing-hit-storm-followup")
        recommendation = comparison.get("recommended_next_evidence", "")
        if "(494,169)" not in recommendation or "(579,169)" not in recommendation or "conditional" not in recommendation:
            print("[FAIL] helper-gate partial trace missing targeted followup recommendation")
            return 1
        helper_md = output_md.read_text(encoding="utf-8")
        for needle in (
            "loader-breakpoints-answered-per-pixel-typed-witness-missing-hit-storm-followup",
            "answered_partial",
            "front-scatter-helper",
        ):
            if needle not in helper_md:
                print(f"[FAIL] helper-gate comparison Markdown missing: {needle}")
                return 1

        summary.write_text(
            json.dumps(
                {
                    "kind": "olm_runtime_trace_return_summary",
                    "results": [
                        {
                            "request_id": RESIDUAL_REQUEST_ID,
                            "status": "answered",
                            "summary": "synthetic focused DirectionalBlur residual witness trace",
                            "observations": {
                                "cases": [
                                    {
                                        "case_id": "case_0001",
                                        "aex_output_to_ab_buffer_xy": [494, 169],
                                        "aex_rowdriver_or_group_membership": {
                                            "group_id": 12,
                                            "row_span": [380, 959],
                                            "membership": True,
                                        },
                                        "aex_pre_writeback_rgba_float_or_hex": [
                                            "0x1.48p+7",
                                            "0x0p+0",
                                            "0x0p+0",
                                            "0x1.fep+7",
                                        ],
                                        "aex_final_rgba_u8": [164, 0, 0, 255],
                                    },
                                    {
                                        "case_id": "case_0005",
                                        "aex_output_to_ab_buffer_xy": [507, 367],
                                        "aex_rotate_sampler_source_coordinates_order": [
                                            {"source_xy": [507.25, 367.5], "weight": 0.5}
                                        ],
                                        "aex_border_or_validity_decision": "valid",
                                        "aex_final_rgba_u8": [1, 0, 0, 255],
                                    },
                                ]
                            },
                        }
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        comparison = run_compare(repo, py, output_json, output_md, summary=summary)
        assert_request(comparison, RESIDUAL_REQUEST_ID)
        assert_focus(comparison, "angle0:rowdriver-or-group-membership; diagonal:rotate-sampler")
        recommendation = comparison.get("recommended_next_evidence", "")
        if "angle-0" not in recommendation or "diagonal" not in recommendation:
            print("[FAIL] focused residual trace missing paired recommendation")
            return 1

        summary.write_text(
            json.dumps(
                {
                    "kind": "olm_runtime_trace_return_summary",
                    "results": [
                        {
                            "request_id": DENSE_REQUEST_ID,
                            "status": "answered",
                            "summary": "older dense result that must not win over the single-shot request",
                            "observations": {},
                        },
                        {
                            "request_id": SINGLE_SHOT_REQUEST_ID,
                            "status": "answered",
                            "summary": "synthetic angle-0 single-shot typed witness",
                            "observations": {
                                "cases": [
                                    {
                                        "case_id": "case_0001",
                                        "aex_output_to_ab_buffer_xy": [494, 169],
                                        "aex_helper_local_source_xy": [494, 169],
                                        "aex_touched_destination_x_range": [494, 579],
                                        "aex_rowdriver_or_group_membership": {
                                            "group_id": 12,
                                            "row": 169,
                                            "membership": True,
                                        },
                                        "aex_alpha_or_valid_side_channel": 1,
                                        "aex_accumulation_numerator_rgba": [164.0, 0.0, 0.0, 255.0],
                                        "aex_normalization_denominator": 1.0,
                                        "aex_pre_writeback_rgba_float_or_hex": [
                                            "0x1.48p+7",
                                            "0x0p+0",
                                            "0x0p+0",
                                            "0x1.fep+7",
                                        ],
                                        "aex_final_rgba_u8": [164, 0, 0, 255],
                                    }
                                ]
                            },
                        },
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        comparison = run_compare(repo, py, output_json, output_md, summary=summary)
        assert_request(comparison, SINGLE_SHOT_REQUEST_ID)
        assert_focus(comparison, "angle0:rowdriver-or-group-membership; diagonal:await-windows-trace")
        recommendation = comparison.get("recommended_next_evidence", "")
        if "angle-0" not in recommendation or "rowdriver/group membership" not in recommendation:
            print("[FAIL] single-shot trace missing angle-0 rowdriver recommendation")
            return 1

        comparison = run_compare(repo, py, output_json, output_md, witness=witness)
        assert_request(comparison, DENSE_REQUEST_ID)
        assert_focus(comparison, "await-windows-trace")
        local = comparison.get("local_witness") or {}
        if local.get("source_file") != "witness.json":
            print(f"[FAIL] standalone witness source file mismatch: {local.get('source_file')}")
            return 1
        standalone_md = output_md.read_text(encoding="utf-8")
        for needle in ("Local CLI Witness", "Coordinate Cross-Compare", "windows_match=`False`"):
            if needle not in standalone_md:
                print(f"[FAIL] standalone witness Markdown missing: {needle}")
                return 1
    print("[OK] DirectionalBlur trace comparison smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
