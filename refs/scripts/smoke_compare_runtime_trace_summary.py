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
            "olmdistancegradation_field_prep": "constant-field-prep",
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
