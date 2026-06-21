#!/usr/bin/env python3
"""Smoke-test scripts/compare_radialblur_trace.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


REQUEST_ID = "olmradialblur_dense_sampler_trace_20260620"


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
    if comparison.get("request_id") != REQUEST_ID:
        print("[FAIL] comparison request_id mismatch")
        raise SystemExit(1)
    if comparison.get("likely_next_focus") != expected:
        print(f"[FAIL] expected focus {expected}, got {comparison.get('likely_next_focus')}")
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
                            "request_id": REQUEST_ID,
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
        assert_focus(run_compare(repo, py, summary, output_json, output_md), "sampler-scatter-or-writeback-values")
        markdown = output_md.read_text(encoding="utf-8")
        for needle in ("OLMRadialBlur Trace Comparison", "Windows Observations", "sampler-scatter-or-writeback"):
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
        assert_focus(run_compare(repo, py, summary, output_json, output_md), "inner-span-31-registers-only")

        summary.write_text(
            json.dumps(
                {
                    "kind": "olm_runtime_trace_return_summary",
                    "results": [
                        {
                            "request_id": REQUEST_ID,
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
        assert_focus(run_compare(repo, py, summary, output_json, output_md), "trace-structure-present-values-missing")
    print("[OK] RadialBlur trace comparison smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
