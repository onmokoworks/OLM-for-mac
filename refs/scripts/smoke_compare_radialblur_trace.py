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
        assert_focus(comparison, "tiny_rotation:substitute-or-upstream-rgb")
        recommendation = comparison.get("recommended_next_evidence", "")
        if "substitute/fallback branch state" not in recommendation:
            print("[FAIL] tiny followup missing substitute-path recommendation")
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
        assert_focus(comparison, "tiny_rotation:substitute-or-upstream-rgb")

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
        assert_focus(comparison, "tiny_rotation:substitute-or-upstream-rgb")
    print("[OK] RadialBlur trace comparison smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
