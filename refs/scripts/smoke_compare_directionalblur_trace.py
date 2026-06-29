#!/usr/bin/env python3
"""Smoke-test scripts/compare_directionalblur_trace.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


DENSE_REQUEST_ID = "olmdirectionalblur_dense_sampler_trace_20260620"
RESIDUAL_REQUEST_ID = "olmdirectionalblur_helper_coverage_witness_20260630"


def run_compare(repo: Path, py: str, summary: Path, output_json: Path, output_md: Path) -> dict:
    proc = subprocess.run(
        [
            py,
            "scripts/compare_directionalblur_trace.py",
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
    with tempfile.TemporaryDirectory(prefix="olmdirectionalblur_compare_smoke_") as tmp:
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
        comparison = run_compare(repo, py, summary, output_json, output_md)
        assert_request(comparison, DENSE_REQUEST_ID)
        assert_focus(comparison, "sampler-or-writeback-values")
        if "concrete sampler" not in comparison.get("recommended_next_evidence", ""):
            print("[FAIL] dense trace missing sampler next-evidence recommendation")
            return 1
        markdown = output_md.read_text(encoding="utf-8")
        for needle in (
            "OLMDirectionalBlur Trace Comparison",
            "Windows Observations",
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
        comparison = run_compare(repo, py, summary, output_json, output_md)
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
        comparison = run_compare(repo, py, summary, output_json, output_md)
        assert_request(comparison, RESIDUAL_REQUEST_ID)
        assert_focus(comparison, "angle0:rowdriver-or-group-membership; diagonal:rotate-sampler")
        recommendation = comparison.get("recommended_next_evidence", "")
        if "angle-0" not in recommendation or "diagonal" not in recommendation:
            print("[FAIL] focused residual trace missing paired recommendation")
            return 1
    print("[OK] DirectionalBlur trace comparison smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
