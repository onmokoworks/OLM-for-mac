#!/usr/bin/env python3
"""Smoke-test the DG case_0010 (901,394) source-only return classifier."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


REQUEST_ID = "olmdistancegradation_0010_compose_source_901_394_tile_retry_20260710"


def run_case(root: Path, tmp: Path, site_run: dict[str, object], expected_focus: str) -> None:
    summary = tmp / "summary.json"
    output = tmp / "comparison.json"
    markdown = tmp / "comparison.md"
    summary.write_text(
        json.dumps(
            {
                "kind": "olm_runtime_trace_return_summary",
                "results": [
                    {
                        "request_id": REQUEST_ID,
                        "status": "answered_partial",
                        "summary": "synthetic tile-aware source witness",
                        "observations": {
                            "case_id": "olmdistancegradation_extended__case_0010",
                            "target_xy": [901, 394],
                            "gating_relation": "RDI == output_base + 394*0x3c00 + 901*8",
                            "site_runs": {"source": site_run},
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
            sys.executable,
            "scripts/compare_distancegradation_trace.py",
            "--runtime-summary-json",
            str(summary),
            "--request-id",
            REQUEST_ID,
            "--output-json",
            str(output),
            "--output-md",
            str(markdown),
        ],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
    if proc.returncode:
        raise AssertionError(f"comparator failed: {proc.returncode}")
    result = json.loads(output.read_text(encoding="utf-8"))
    if result.get("likely_next_focus") != expected_focus:
        raise AssertionError(f"unexpected focus: {result.get('likely_next_focus')}")
    windows = result.get("windows", {})
    if windows.get("target_xy") != [901, 394]:
        raise AssertionError(f"target was not preserved: {windows.get('target_xy')}")


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="dg_901_394_compare_") as tmp_name:
        tmp = Path(tmp_name)
        run_case(
            root,
            tmp,
            {
                "site": "source",
                "downstream_address": "DistanceGradation+0x11705f1",
                "status": "missed",
                "rdi_equals_target_output": False,
                "failed_gate_or_breakpoint_reason": "target callback was not visited",
            },
            "single-site-witness-missing",
        )
        run_case(
            root,
            tmp,
            {
                "site": "source",
                "downstream_address": "DistanceGradation+0x11705f1",
                "status": "hit",
                "rdi_equals_target_output": True,
                "rdx_source_addr": "0x0000010000000000",
                "rdx_source_words_u16": [65535, 0, 0, 65535, 0, 0, 0, 0],
                "console_log": "artifacts/source_cdb_stdout.txt",
            },
            "single-site-input-bound",
        )
    print("[OK] DG (901,394) tile retry comparison smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
