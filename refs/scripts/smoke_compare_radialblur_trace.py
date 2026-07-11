#!/usr/bin/env python3
"""Smoke-test scripts/compare_radialblur_trace.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


DENSE_REQUEST_ID = "olmradialblur_dense_sampler_trace_20260620"
RESIDUAL_REQUEST_ID = "olmradialblur_caller_collapse_witness_20260630"
TINY_REQUEST_ID = "olmradialblur_tiny_rotation_substitute_path_followup_20260701"
TINY_BACKSTEP_REQUEST_ID = "olmradialblur_tiny_rotation_inverse_sampler_backstep_followup_20260701"
TINY_CONTEXT_REQUEST_ID = "olmradialblur_tiny_rotation_anchor_context_watch_followup_20260702"
CASE0010_FINAL_WRITEBACK_REQUEST_ID = "olmradialblur_case0010_final_writeback_20260708"
ZOOM_CASE0009_FINAL_PLANE_CELLS_REQUEST_ID = "olmradialblur_zoom_case0009_final_plane_cells_20260709"
ZOOM_CASE0009_FINAL_PLANE_TYPED_REQUEST_ID = "olmradialblur_zoom_case0009_final_plane_typed_20260710"


def run_compare(repo: Path, py: str, summary: Path, output_json: Path, output_md: Path) -> dict:
    proc = subprocess.run(
        [
            py,
            "scripts/compare_radialblur_trace.py",
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
    with tempfile.TemporaryDirectory(prefix="olmradialblur_compare_smoke_") as tmp:
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
                            "request_id": DENSE_REQUEST_ID,
                            "status": "answered",
                            "summary": "synthetic RadialBlur dense trace",
                            "observations": {
                                "cases": [
                                    {
                                        "case_id": "case_0011",
                                        "witness_pixels": [
                                            {
                                                "x": 510,
                                                "y": 512,
                                                "loop_bounds_or_sample_count": 31,
                                                "intermediate_values": {"scatter_span": 31, "denom": 0.75},
                                                "pre_writeback_rgba_float_hex": [
                                                    "0x1.0p+0",
                                                    "0x0p+0",
                                                    "0x0p+0",
                                                    "0x1.0p+0",
                                                ],
                                                "final_rgba": [255, 0, 0, 255],
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
        comparison = run_compare(repo, py, summary, output_json, output_md)
        assert_request(comparison, DENSE_REQUEST_ID)
        assert_focus(comparison, "sampler-scatter-or-writeback-values")
        if "concrete sampler/scatter" not in comparison.get("recommended_next_evidence", ""):
            print("[FAIL] dense trace missing sampler/scatter next-evidence recommendation")
            return 1
        markdown = output_md.read_text(encoding="utf-8")
        for needle in (
            "OLMRadialBlur Trace Comparison",
            "Windows Observations",
            "sampler-scatter-or-writeback",
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
                            "status": "partial_live_trace_captured",
                            "summary": (
                                "radialblur_inner_20260605 rb_inner_only_strength_small was rerun. "
                                "OLMRadialBlur+0x26e5 and +0x1d18 hit; captured r8d=0, edx=1, "
                                "r9d=0, ctx+0x3a9ec=0x1f, r14d=0x1f, eax=0xbb8."
                            ),
                            "observations": {},
                        }
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        comparison = run_compare(repo, py, summary, output_json, output_md)
        assert_request(comparison, DENSE_REQUEST_ID)
        assert_focus(comparison, "inner-span-31-registers-only")
        if "span-31 fact" not in comparison.get("recommended_next_evidence", ""):
            print("[FAIL] inner span trace missing next-evidence warning")
            return 1

        summary.write_text(
            json.dumps(
                {
                    "kind": "olm_runtime_trace_return_summary",
                    "results": [
                        {
                            "request_id": DENSE_REQUEST_ID,
                            "status": "answered",
                            "summary": "synthetic sparse RadialBlur trace",
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
        comparison = run_compare(repo, py, summary, output_json, output_md)
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
                            "request_id": RESIDUAL_REQUEST_ID,
                            "status": "answered",
                            "summary": "synthetic focused RadialBlur caller-collapse witness trace",
                            "observations": {
                                "cases": [
                                    {
                                        "case_id": "case_0009",
                                        "aex_normalization_denominator": 0.99609375,
                                        "aex_pre_writeback_rgba_float_or_hex": [
                                            "0x1.4p+4",
                                            "0x1.8p+1",
                                            "0x1.8p+1",
                                            "0x1.fcp+7",
                                        ],
                                        "aex_writeback_operation": "floor(x+0.5)",
                                        "aex_final_rgba_u8": [20, 3, 3, 254],
                                    },
                                    {
                                        "case_id": "case_0010",
                                        "aex_polar_or_source_xy": [1613.5, 6.0],
                                        "aex_validity_or_border_decision": "valid",
                                        "aex_source_or_polar_rgba_float": [1.0, 1.0, 1.0, 1.0],
                                        "aex_pre_writeback_rgba_float_or_hex": [
                                            "0x1.fep+7",
                                            "0x1.fep+7",
                                            "0x1.fep+7",
                                            "0x1.fep+7",
                                        ],
                                        "aex_final_rgba_u8": [255, 255, 255, 255],
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
        comparison = run_compare(repo, py, summary, output_json, output_md)
        assert_request(comparison, RESIDUAL_REQUEST_ID)
        assert_focus(
            comparison,
            "zoom:alpha-normalization-or-writeback; tiny_rotation:substitute-or-upstream-rgb",
        )
        recommendation = comparison.get("recommended_next_evidence", "")
        if "case_0009" not in recommendation or "case_0010" not in recommendation:
            print("[FAIL] focused residual trace missing case-specific recommendation")
            return 1

        summary.write_text(
            json.dumps(
                {
                    "kind": "olm_runtime_trace_return_summary",
                    "results": [
                        {
                            "request_id": TINY_REQUEST_ID,
                            "status": "answered_partial",
                            "summary": "synthetic tiny Rotation upstream substitute-path witness",
                            "observations": {
                                "cases": [
                                    {
                                        "case_id": "case_0010",
                                        "aex_inverse_sampler_input_xy": [1613.75, 6.25],
                                        "aex_polar_or_source_xy": [1601.0, 843.0],
                                        "aex_validity_or_border_decision": "valid",
                                        "aex_fallback_or_substitute_path": "substitute promoted bright source cluster from previous polar row",
                                        "aex_source_or_polar_rgba_float": [0.168253, 0.168253, 0.168253, 1.0],
                                        "aex_preserved_validity_f252": 1.0,
                                        "aex_accumulated_f250_rgba_float": [0.95, 0.95, 0.95, 1.0],
                                        "aex_normalized_final_e_rgba_float": [1.0, 1.0, 1.0, 1.0],
                                        "aex_pre_writeback_rgba_float_or_hex": [
                                            "0x1.fep+7",
                                            "0x1.fep+7",
                                            "0x1.fep+7",
                                            "0x1.fep+7",
                                        ],
                                        "aex_final_rgba_u8": [255, 255, 255, 255],
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
        comparison = run_compare(repo, py, summary, output_json, output_md)
        assert_request(comparison, TINY_REQUEST_ID)
        assert_focus(comparison, "tiny_rotation:upstream-branch-not-isolated")
        recommendation = comparison.get("recommended_next_evidence", "")
        if "first upstream promotion/substitute branch" not in recommendation:
            print("[FAIL] tiny followup missing branch-isolation recommendation")
            return 1
        if "local_tiny_rotation_context" not in comparison:
            print("[FAIL] tiny followup should include local tiny Rotation context")
            return 1
        markdown = output_md.read_text(encoding="utf-8")
        for needle in ("Local tiny Rotation Context", "Source-polar structure", "tiny_rotation:substitute-or-upstream-rgb"):
            if needle not in markdown:
                print(f"[FAIL] tiny followup Markdown missing: {needle}")
                return 1

        summary.write_text(
            json.dumps(
                {
                    "kind": "olm_runtime_trace_return_summary",
                    "results": [
                        {
                            "request_id": TINY_REQUEST_ID,
                            "status": "failed_partial",
                            "summary": "synthetic failed-partial tiny Rotation return with final byte plus upstream hints only",
                            "observations": {
                                "cases": [
                                    {
                                        "case_id": "case_0010",
                                        "aex_fallback_or_substitute_path": "not isolated",
                                        "aex_final_rgba_u8": [255, 255, 255, 255],
                                        "aex_inverse_sampler_input_xy": [1603.8, 844.3],
                                        "aex_normalized_final_e_rgba_float": [1.0, 1.0, 1.0, 1.0],
                                        "aex_polar_or_source_xy": [1603.8, 844.3],
                                        "aex_pre_writeback_rgba_float_or_hex": [None, None, None, None],
                                        "aex_preserved_validity_f252": None,
                                        "aex_source_or_polar_rgba_float": [-0.004, -0.004, -0.004, 1.0],
                                        "aex_validity_or_border_decision": "not isolated",
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
        comparison = run_compare(repo, py, summary, output_json, output_md)
        assert_request(comparison, TINY_REQUEST_ID)
        assert_focus(comparison, "tiny_rotation:upstream-branch-not-isolated")

        summary.write_text(
            json.dumps(
                {
                    "kind": "olm_runtime_trace_return_summary",
                    "results": [
                        {
                            "request_id": TINY_BACKSTEP_REQUEST_ID,
                            "status": "failed_partial",
                            "summary": "synthetic backstep followup still only reaches inverse-sampler anchor and not the upstream branch",
                            "observations": {
                                "cases": [
                                    {
                                        "case_id": "case_0010",
                                        "aex_fallback_or_substitute_path": "not isolated",
                                        "aex_final_rgba_u8": [255, 255, 255, 255],
                                        "aex_inverse_sampler_input_xy": [1603.8, 844.3],
                                        "aex_normalized_final_e_rgba_float": [1.0, 1.0, 1.0, 1.0],
                                        "aex_polar_or_source_xy": [1603.8, 844.3],
                                        "aex_pre_writeback_rgba_float_or_hex": [None, None, None, None],
                                        "aex_preserved_validity_f252": None,
                                        "aex_source_or_polar_rgba_float": [-0.004, -0.004, -0.004, 1.0],
                                        "aex_validity_or_border_decision": "not isolated",
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
        comparison = run_compare(repo, py, summary, output_json, output_md)
        assert_request(comparison, TINY_BACKSTEP_REQUEST_ID)
        assert_focus(comparison, "tiny_rotation:upstream-branch-not-isolated")

        summary.write_text(
            json.dumps(
                {
                    "kind": "olm_runtime_trace_return_summary",
                    "results": [
                        {
                            "request_id": TINY_CONTEXT_REQUEST_ID,
                            "status": "failed_partial",
                            "summary": "synthetic anchor-context followup still needs first upstream promotion branch",
                            "observations": {
                                "cases": [
                                    {
                                        "case_id": "case_0010",
                                        "aex_fallback_or_substitute_path": "captured branch neighborhood",
                                        "aex_final_rgba_u8": [255, 255, 255, 255],
                                        "aex_inverse_sampler_input_xy": [1603.8, 844.3],
                                        "aex_normalized_final_e_rgba_float": [1.0, 1.0, 1.0, 1.0],
                                        "aex_polar_or_source_xy": [1603.8, 844.3],
                                        "aex_pre_writeback_rgba_float_or_hex": [None, None, None, None],
                                        "aex_preserved_validity_f252": 1.0,
                                        "aex_source_or_polar_rgba_float": [-0.004, -0.004, -0.004, 1.0],
                                        "aex_validity_or_border_decision": "not isolated",
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
        comparison = run_compare(repo, py, summary, output_json, output_md)
        assert_request(comparison, TINY_CONTEXT_REQUEST_ID)
        assert_focus(comparison, "tiny_rotation:anchor-context-upstream-branch")
        recommendation = comparison.get("recommended_next_evidence", "")
        if "first upstream promotion branch" not in recommendation:
            print("[FAIL] anchor-context followup missing branch-specific recommendation")
            return 1
        if "local_tiny_rotation_lane_state" not in comparison:
            print("[FAIL] anchor-context followup should include lane-state context")
            return 1

        summary.write_text(
            json.dumps(
                {
                    "kind": "olm_runtime_trace_return_summary",
                    "results": [
                        {
                            "request_id": DENSE_REQUEST_ID,
                            "status": "answered",
                            "summary": "older dense result that must not win over the final-writeback request",
                            "observations": {},
                        },
                        {
                            "request_id": CASE0010_FINAL_WRITEBACK_REQUEST_ID,
                            "status": "answered",
                            "summary": "synthetic case_0010 final-writeback chain",
                            "observations": {
                                "cases": [
                                    {
                                        "case_id": "case_0010",
                                        "module_base_or_aex_version": "OLMRadialBlur.aex+synthetic",
                                        "inverse_sampler_input_xy": [1603.8, 844.3],
                                        "contributing_polar_cells": [[1603, 844], [1604, 844], [1603, 845], [1604, 845]],
                                        "accumulated_f250_rgba": [1.0, 1.0, 1.0, 1.0],
                                        "preserved_validity_f252": 1.0,
                                        "collapsed_e_rgba": [1.0, 1.0, 1.0, 1.0],
                                        "direct_inverse_sampler_result_from_e": [1.0, 1.0, 1.0, 1.0],
                                        "output_buffer_rgba_after_writeback": [255, 255, 255, 255],
                                        "exported_rgba8_or_png_byte": [255, 255, 255, 255],
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
        comparison = run_compare(repo, py, summary, output_json, output_md)
        assert_request(comparison, CASE0010_FINAL_WRITEBACK_REQUEST_ID)
        assert_focus(comparison, "tiny_rotation:case0010-final-writeback-provenance")
        windows = comparison.get("windows", {})
        final = windows.get("case0010_final_writeback", {})
        if final.get("collapsed_e_rgba") != [1.0, 1.0, 1.0, 1.0]:
            print("[FAIL] case0010 final-writeback fields were not surfaced")
            return 1
        if final.get("direct_inverse_sampler_result_from_e") != [1.0, 1.0, 1.0, 1.0]:
            print("[FAIL] case0010 direct +0xe sampler field was not surfaced")
            return 1
        if "classify the returned" not in comparison.get("recommended_next_evidence", ""):
            print("[FAIL] case0010 final-writeback recommendation missing")
            return 1

        summary.write_text(
            json.dumps(
                {
                    "kind": "olm_runtime_trace_return_summary",
                    "results": [
                        {
                            "request_id": CASE0010_FINAL_WRITEBACK_REQUEST_ID,
                            "status": "answered_partial",
                            "summary": "synthetic case_0010 final-writeback chain missing same-run export only",
                            "observations": {
                                "cases": [
                                    {
                                        "case_id": "case_0010",
                                        "accumulated_f250_rgba": [1.0, 1.0, 1.0, 1.0],
                                        "preserved_validity_f252": 1.0,
                                        "collapsed_e_rgba": [1.0, 1.0, 1.0, 1.0],
                                        "direct_inverse_sampler_result_from_e": [1.0, 1.0, 1.0, 1.0],
                                        "output_buffer_rgba_after_writeback": [255, 255, 255, 255],
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
        comparison = run_compare(repo, py, summary, output_json, output_md)
        assert_request(comparison, CASE0010_FINAL_WRITEBACK_REQUEST_ID)
        assert_focus(comparison, "tiny_rotation:case0010-final-writeback-partial-missing-export")
        if "same-run export byte" not in comparison.get("recommended_next_evidence", ""):
            print("[FAIL] case0010 partial missing-export recommendation was not narrowed")
            return 1

        summary.write_text(
            json.dumps(
                {
                    "kind": "olm_runtime_trace_return_summary",
                    "results": [
                        {
                            "request_id": CASE0010_FINAL_WRITEBACK_REQUEST_ID,
                            "status": "answered_partial",
                            "summary": "No fresh same-run Windows debugger stop was captured in this return.",
                            "observations": {
                                "case_id": "case_0010",
                                "classification": "final-writeback-export-split | stale-reference-or-aex-drift",
                                "aex_path_or_version": "Not freshly re-hooked in this return.",
                                "same_run_values": {
                                    "final_inverse_sampler_xy": [1603.839558785, 844.317504883],
                                    "polar_cells": [
                                        {
                                            "cell_xy": [1603, 844],
                                            "f250_rgba_float": [-0.025, -0.025, -0.025, 1.7],
                                            "f252_validity_or_alpha": [0.0, 0.0, 0.0, 1.0],
                                            "collapsed_e_rgba_float": [-0.014, -0.014, -0.014, 1.0],
                                        }
                                    ],
                                    "direct_inverse_sampler_result_rgba_float": [-0.004, -0.004, -0.004, 1.0],
                                    "output_buffer_rgba_after_writeback": [0, 0, 0, 0],
                                    "exported_rgba8_or_png_byte": [237, 237, 237, 255],
                                },
                            },
                        }
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        comparison = run_compare(repo, py, summary, output_json, output_md)
        assert_request(comparison, CASE0010_FINAL_WRITEBACK_REQUEST_ID)
        assert_focus(comparison, "tiny_rotation:case0010-final-writeback-partial-missing-same-run-debugger-stop")
        if "same-run Windows debugger stop" not in comparison.get("recommended_next_evidence", ""):
            print("[FAIL] case0010 no-fresh-debugger recommendation was not preserved")
            return 1

        final_plane_pixels = []
        for xy in ([6, 0], [7, 0], [12, 0], [3, 0], [4, 0], [8, 0], [10, 0]):
            final_plane_pixels.append(
                {
                    "xy": xy,
                    "windows_final_rgba8": [20, 3, 3, 254] if xy in ([6, 0], [7, 0], [12, 0]) else [20, 3, 3, 255],
                    "final_inverse_sampler_xy": [100.25 + xy[0], 0.75],
                    "four_bilinear_source_cells": [
                        {"cell_xy": [100 + xy[0], 0], "rgba_float": [0.1, 0.01, 0.01, 1.0]},
                        {"cell_xy": [101 + xy[0], 0], "rgba_float": [0.1, 0.01, 0.01, 0.999]},
                        {"cell_xy": [100 + xy[0], 1], "rgba_float": [0.1, 0.01, 0.01, 1.0]},
                        {"cell_xy": [101 + xy[0], 1], "rgba_float": [0.1, 0.01, 0.01, 1.0]},
                    ],
                    "bilinear_weights": [0.1875, 0.0625, 0.5625, 0.1875],
                    "final_sample_alpha_sum": 0.99999994,
                    "conversion_rule": "truncate",
                }
            )
        summary.write_text(
            json.dumps(
                {
                    "kind": "olm_runtime_trace_return_summary",
                    "results": [
                        {
                            "request_id": DENSE_REQUEST_ID,
                            "status": "answered",
                            "summary": "older dense result that must not win over final-plane cells",
                            "observations": {},
                        },
                        {
                            "request_id": ZOOM_CASE0009_FINAL_PLANE_CELLS_REQUEST_ID,
                            "status": "answered",
                            "summary": "synthetic Zoom case_0009 final-plane cell witness",
                            "observations": {
                                "cases": [
                                    {
                                        "case_id": "case_0009",
                                        "final_plane_pixels": final_plane_pixels,
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
        comparison = run_compare(repo, py, summary, output_json, output_md)
        assert_request(comparison, ZOOM_CASE0009_FINAL_PLANE_CELLS_REQUEST_ID)
        assert_focus(comparison, "zoom_case0009:final-plane-cells-answered")
        if "cell ids/alphas/weights" not in comparison.get("recommended_next_evidence", ""):
            print("[FAIL] final-plane complete recommendation missing")
            return 1

        summary.write_text(
            json.dumps(
                {
                    "kind": "olm_runtime_trace_return_summary",
                    "results": [
                        {
                            "request_id": ZOOM_CASE0009_FINAL_PLANE_CELLS_REQUEST_ID,
                            "status": "failed_partial",
                            "summary": "Only final RGBA PNG bytes and wrapper hit counts were captured.",
                            "observations": {
                                "cases": [
                                    {
                                        "case_id": "case_0009",
                                        "witness_pixels": [
                                            {"xy": [6, 0], "windows_final_rgba8": [20, 3, 3, 254]},
                                            {"xy": [7, 0], "windows_final_rgba8": [20, 3, 3, 254]},
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
        comparison = run_compare(repo, py, summary, output_json, output_md)
        assert_request(comparison, ZOOM_CASE0009_FINAL_PLANE_CELLS_REQUEST_ID)
        assert_focus(comparison, "zoom_case0009:final-plane-witness-missing")
        if "Do not tune" not in comparison.get("recommended_next_evidence", ""):
            print("[FAIL] final-plane missing recommendation should forbid tuning")
            return 1

        def typed_point(xy: list[int], complete: bool = True) -> dict:
            point = {
                "role": "primary" if xy == [7, 0] else "control",
                "xy": xy,
                "observed_rgba8": [21, 3, 3, 254 if xy == [7, 0] else 255],
                "inverse_sample_xy": [100.25 + xy[0], 0.75],
                "cells": [
                    {
                        "slot": slot,
                        "cell_id": f"angle{slot}:radius{xy[0]}",
                        "plus_0xe_rgba_float": [0.1, 0.01, 0.01, 1.0],
                        "plus_0xf252": {"raw_word": "0xffff", "alpha": 1.0},
                        "bilinear_weight": weight,
                    }
                    for slot, weight in zip(("00", "10", "01", "11"), (0.1875, 0.0625, 0.5625, 0.1875))
                ],
                "final_alpha_sum": 0.99999994,
                "pre_byte_alpha": 0.99999994,
                "failed_reason": None,
            }
            if not complete:
                point["cells"][0]["cell_id"] = None
            return point

        typed_base = {
            "kind": "olm_runtime_trace_return_summary",
            "results": [
                {
                    "request_id": ZOOM_CASE0009_FINAL_PLANE_TYPED_REQUEST_ID,
                    "status": "answered",
                    "observations": {
                        "run_id": "run-0009-a",
                        "hook_or_watchpoint": "OLMRadialBlur+0x7b4a",
                        "console_artifact": "debugger/run-0009-a.log",
                        "points": [typed_point([7, 0]), typed_point([8, 0]), typed_point([24, 0])],
                    },
                }
            ],
        }
        summary.write_text(json.dumps(typed_base, indent=2), encoding="utf-8")
        comparison = run_compare(repo, py, summary, output_json, output_md)
        assert_request(comparison, ZOOM_CASE0009_FINAL_PLANE_TYPED_REQUEST_ID)
        assert_focus(comparison, "zoom_case0009:final-plane-typed-complete")
        typed_windows = comparison["windows"]["case0009_final_plane_typed"]
        if typed_windows["points"][0]["cells"][0]["plus_0xf252"]["raw_word"] != "0xffff":
            print("[FAIL] typed +0xf252 cell witness was not surfaced")
            return 1

        partial = typed_base.copy()
        partial["results"] = [dict(typed_base["results"][0])]
        partial["results"][0]["status"] = "answered_partial"
        partial["results"][0]["observations"] = dict(typed_base["results"][0]["observations"])
        partial["results"][0]["observations"]["points"] = [typed_point([7, 0]), {"xy": [8, 0]}, {"xy": [24, 0]}]
        partial["results"][0]["observations"]["failed_reason"] = "control watchpoints were not isolated in the same run"
        summary.write_text(json.dumps(partial, indent=2), encoding="utf-8")
        comparison = run_compare(repo, py, summary, output_json, output_md)
        assert_focus(comparison, "zoom_case0009:final-plane-typed-partial")
        if comparison["classification"] != "partial":
            print("[FAIL] typed partial classification missing")
            return 1

        missing = typed_base.copy()
        missing["results"] = [dict(typed_base["results"][0])]
        missing["results"][0]["observations"] = {"points": [{"xy": [7, 0], "observed_rgba8": [21, 3, 3, 254]}]}
        summary.write_text(json.dumps(missing, indent=2), encoding="utf-8")
        comparison = run_compare(repo, py, summary, output_json, output_md)
        assert_focus(comparison, "zoom_case0009:final-plane-typed-missing")
    print("[OK] RadialBlur trace comparison smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
