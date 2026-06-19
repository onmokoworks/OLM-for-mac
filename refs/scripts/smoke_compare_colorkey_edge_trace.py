#!/usr/bin/env python3
"""Smoke-test scripts/compare_colorkey_edge_trace.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


REQUEST_ID = "colorkey_edge_runtime_trace_20260619"


def main() -> int:
    repo = Path(__file__).resolve().parents[2]
    py = sys.executable
    with tempfile.TemporaryDirectory(prefix="olmcolorkey_edge_compare_smoke_") as tmp:
        tmp_path = Path(tmp)
        summary = tmp_path / "runtime_summary.json"
        baseline = tmp_path / "baseline"
        baseline.mkdir()
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
                            "summary": "synthetic ColorKey Edge trace",
                            "observations": {
                                "ctx_0x44_distance_type": 2,
                                "edge_thin_erode_cases": [
                                    {
                                        "case_id": "case_0005",
                                        "distance_after_transform": 17,
                                        "branch_condition_observed": "dist > adjusted_limit",
                                    }
                                ],
                                "edge_blur_samples": [
                                    {
                                        "case_id": "case_0009",
                                        "x": 1116,
                                        "y": 136,
                                        "boundary_seed_after_FUN_180008c90": 0,
                                        "edge_blur_weight": 1.0,
                                    }
                                ],
                                "edge_blur_distance_dispatch_observed": "1->FUN_180006e20,2->FUN_180005d60,3->FUN_180007ec0",
                            },
                        }
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        (baseline / "case_0005_trace.log").write_text(
            "OLMCOLORKEY_TRACE x=34 y=0 matched0=1 matched1=0 keep=0 "
            "edge_thin_amount=-16 edge_thin_limit=17 edge_thin_dist=17 "
            "edge_blur_amount=0 edge_blur_dir=2 edge_blur_dist_type=1 "
            "final_rgba=(0,0,0,0)\n",
            encoding="utf-8",
        )
        (baseline / "case_0009_trace.log").write_text(
            "OLMCOLORKEY_TRACE x=1116 y=136 matched0=0 matched1=0 keep=1 "
            "edge_thin_amount=16 edge_thin_limit=16 edge_thin_dist=35.227829 "
            "edge_blur_amount=25 edge_blur_dir=3 edge_blur_dist_type=2 "
            "boundary=0 edge_blur_dist=25 edge_blur_weight=1 final_rgba=(0,0,0,255)\n",
            encoding="utf-8",
        )
        (baseline / "diff.json").write_text(
            json.dumps(
                {
                    "cases": [
                        {
                            "id": "case_0005",
                            "max_diff": 255,
                            "mean_diff": 0.3031,
                            "nonzero_px_percent": 0.4755,
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        proc = subprocess.run(
            [
                py,
                "scripts/compare_colorkey_edge_trace.py",
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
        if comparison.get("likely_next_focus") != "edge-thin-border-threshold":
            print("[FAIL] comparison did not choose expected next focus")
            return 1
        markdown = output_md.read_text(encoding="utf-8")
        for needle in ("OLMColorKey Edge Trace Comparison", "Local Baseline", "Edge Blur samples"):
            if needle not in markdown:
                print(f"[FAIL] comparison Markdown missing: {needle}")
                return 1
    print("[OK] ColorKey Edge trace comparison smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
