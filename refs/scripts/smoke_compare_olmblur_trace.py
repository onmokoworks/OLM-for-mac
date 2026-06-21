#!/usr/bin/env python3
"""Smoke-test scripts/compare_olmblur_trace.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


REQUEST_ID = "olmblur_repeat_threshold_runtime_trace_20260619"


def main() -> int:
    repo = Path(__file__).resolve().parents[2]
    py = sys.executable
    baseline = repo / "refs" / "reports" / "olmblur_trace_baseline_20260619_030633_mac"
    with tempfile.TemporaryDirectory(prefix="olmblur_compare_smoke_") as tmp:
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
                            "summary": "synthetic OLMBlur repeat threshold trace",
                            "source_file": "synthetic.zip",
                            "observations": {
                                "effect": "OLM Blur",
                                "module_base": "0x180000000",
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
                                    },
                                    {
                                        "case_id": "case_0007",
                                        "legacy": 1,
                                        "repeat": 10,
                                        "residual_pixels": [
                                            {
                                                "x": 0,
                                                "y": 0,
                                                "legacy_border_sample_included": False,
                                                "legacy_all_same_state": True,
                                            }
                                        ],
                                    },
                                ],
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
                "scripts/compare_olmblur_trace.py",
                "--runtime-summary-json",
                str(summary),
                "--local-baseline-dir",
                str(baseline),
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
        if comparison.get("likely_next_focus") != "nonlegacy-accumulation-or-writeback":
            print("[FAIL] comparison did not choose expected next focus")
            return 1
        markdown = output_md.read_text(encoding="utf-8")
        for needle in ("OLMBlur Trace Comparison", "Local Baseline", "Case 0006"):
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
                            "summary": "synthetic sparse OLMBlur trace",
                            "source_file": "synthetic_sparse.zip",
                            "observations": {
                                "cases": [
                                    {
                                        "case_id": "case_0006",
                                        "residual_pixels": [
                                            {
                                                "x": 498,
                                                "y": 940,
                                                "aex_pre_writeback_rgb_hex": ["0x...", "0x...", "0x..."],
                                                "aex_writeback_operation": "floorf(value + 0.5) | cvt/trunc | other",
                                                "aex_final_rgba": "not isolated; runtime value still needs debugger trace",
                                            }
                                        ],
                                    },
                                    {
                                        "case_id": "case_0007",
                                        "residual_pixels": [
                                            {
                                                "x": 0,
                                                "y": 0,
                                                "legacy_border_sample_included": "not isolated",
                                                "legacy_all_same_state": "unknown",
                                            }
                                        ],
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
        proc = subprocess.run(
            [
                py,
                "scripts/compare_olmblur_trace.py",
                "--runtime-summary-json",
                str(summary),
                "--local-baseline-dir",
                str(baseline),
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
        if comparison.get("likely_next_focus") != "trace-structure-present-values-missing":
            print("[FAIL] placeholder observations should not select a concrete focus")
            return 1
    print("[OK] OLMBlur trace comparison smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
