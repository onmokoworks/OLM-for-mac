#!/usr/bin/env python3
"""Smoke-test scripts/compare_runtime_trace_summary.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    repo = Path(__file__).resolve().parents[2]
    py = sys.executable
    with tempfile.TemporaryDirectory(prefix="olm_runtime_compare_index_smoke_") as tmp:
        tmp_path = Path(tmp)
        summary = tmp_path / "runtime_summary.json"
        out_dir = tmp_path / "comparisons"
        summary.write_text(
            json.dumps(
                {
                    "kind": "olm_runtime_trace_return_summary",
                    "results": [
                        {
                            "request_id": "olmblur_repeat_threshold_runtime_trace_20260619",
                            "status": "answered",
                            "summary": "synthetic OLMBlur trace",
                            "observations": {
                                "cases": [
                                    {
                                        "case_id": "case_0006",
                                        "legacy": 0,
                                        "repeat": 10,
                                        "residual_pixels": [
                                            {
                                                "x": 498,
                                                "y": 940,
                                                "aex_pre_writeback_rgb_hex": [
                                                    "0x1.72ffffp+7",
                                                    "0x0p+0",
                                                    "0x0p+0",
                                                ],
                                                "aex_writeback_operation": "floorf(value + 0.5)",
                                                "aex_final_rgba": [185, 0, 0, 255],
                                            }
                                        ],
                                    }
                                ]
                            },
                        },
                        {
                            "request_id": "olmdirectionalblur_angle0_helper_gate_retry_20260702",
                            "status": "answered_partial",
                            "summary": "Loaded and broad breakpoints reached, but the targeted typed witness was not isolated because of a hit storm.",
                            "observations": {
                                "cases": [
                                    {
                                        "case_id": "db_existing_case_0001_software_pair",
                                        "witness_pixels": [
                                            {
                                                "x": 494,
                                                "y": 169,
                                                "branch_or_dispatch": "front-scatter-helper (offset +0x13e0)",
                                                "pre_writeback_rgba_float_hex": [None, None, None, None],
                                                "final_rgba": None,
                                                "intermediate_values": {
                                                    "confirm_module_load": True,
                                                    "confirm_breakpoint_offsets": True,
                                                    "per_pixel_isolation": "not_achieved",
                                                    "hit_storm_note": "need conditional breakpoints or single-shot per witness pixel",
                                                },
                                            }
                                        ],
                                    }
                                ]
                            },
                        },
                        {
                            "request_id": "olmdistancegradation_field_prep_runtime_trace_20260619",
                            "status": "answered",
                            "summary": "synthetic DistanceGradation trace",
                            "observations": {
                                "cases": ["case_0020"],
                                "requested_for_each_pixel": {
                                    "distance_field_after_constant_rgba_or_mat_values": [
                                        {"case_id": "case_0020", "x": 64, "y": 32, "value": 255.0}
                                    ]
                                },
                            },
                        },
                        {
                            "request_id": "olmdistancegradation_0010_compose_single_site_break_ignore_retry_20260710",
                            "status": "answered_partial",
                            "summary": "synthetic single-site retry with typed field words",
                            "observations": {
                                "case_id": "olmdistancegradation_extended__case_0010",
                                "xy": [6, 40],
                                "ignored_first_chance_80000003": True,
                                "site_runs": [
                                    {
                                        "site": "field",
                                        "site_address": "DistanceGradation+0x117057d",
                                        "exact_rdi_gate_hit": True,
                                        "rcx_field_words": [
                                            "0x0000",
                                            "0x8000",
                                            "0x0000",
                                            "0xffff",
                                        ],
                                    }
                                ],
                            },
                        },
                        {
                            "request_id": "olmsmoother2_current_aex_producer_path_diff_20260702",
                            "status": "answered",
                            "summary": "Loaded and broad breakpoints confirm the producer/writeback path is reachable.",
                            "observations": {
                                "cases": [{"case_id": "case_0001"}],
                                "requested_for_each_case": {"writer_anchor": {"reachable": True}},
                            },
                        },
                        {
                            "request_id": "olmradialblur_zoom_case0009_final_plane_typed_20260710",
                            "status": "answered_partial",
                            "observations": {
                                "run_id": "run-0009-smoke",
                                "hook_or_watchpoint": "OLMRadialBlur+0x7b4a",
                                "console_artifact": "debugger/run-0009-smoke.log",
                                "failed_reason": "control watchpoints were not isolated in the same run",
                                "points": [
                                    {
                                        "xy": [7, 0],
                                        "observed_rgba8": [21, 3, 3, 254],
                                        "inverse_sample_xy": [107.25, 0.75],
                                        "cells": [
                                            {"cell_id": "00", "plus_0xe_rgba_float": [0.1, 0.01, 0.01, 1.0], "plus_0xf252": "0xffff", "bilinear_weight": weight}
                                            for weight in (0.1875, 0.0625, 0.5625, 0.1875)
                                        ],
                                        "final_alpha_sum": 0.99999994,
                                        "pre_byte_alpha": 0.99999994,
                                    }
                                ],
                            },
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
                "scripts/compare_runtime_trace_summary.py",
                "--runtime-summary-json",
                str(summary),
                "--output-dir",
                str(out_dir),
            ],
            cwd=repo,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
        if proc.returncode != 0:
            return proc.returncode
        index = json.loads((out_dir / "index.json").read_text(encoding="utf-8"))
        comparisons = {row["slug"]: row for row in index.get("comparisons", [])}
        expected = {
            "olmblur_repeat_threshold": "nonlegacy-accumulation-or-writeback",
            "olmdirectionalblur_dense_sampler": "loader-breakpoints-answered-per-pixel-typed-witness-missing-hit-storm-followup",
            "olmdistancegradation_field_prep": "constant-field-prep",
            "olmdistancegradation_0010_compose_single_site_break_ignore_retry": "single-site-input-bound",
            "olmsmoother2_legacy_key_gamma": "producer-path-diff-writer-anchor-reached",
            "olmradialblur_zoom_case0009_final_plane_typed": "zoom_case0009:final-plane-typed-partial",
        }
        for slug, focus in expected.items():
            if comparisons.get(slug, {}).get("likely_next_focus") != focus:
                print(f"[FAIL] {slug} focus mismatch: {comparisons.get(slug)}")
                return 1
        if "olmkirakira_stage_values" in comparisons or "olmcolorkey_edge" in comparisons:
            print("[FAIL] absent request comparator unexpectedly ran")
            return 1
        if "OLM Runtime Trace Comparison Index" not in (out_dir / "index.md").read_text(encoding="utf-8"):
            print("[FAIL] missing comparison index markdown header")
            return 1
    print("[OK] runtime trace comparison index smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
