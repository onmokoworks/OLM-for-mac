#!/usr/bin/env python3
"""Smoke-test scripts/summarize_runtime_trace_proof_lanes.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main() -> int:
    root = repo_root()
    script = root / "scripts" / "summarize_runtime_trace_proof_lanes.py"
    source = root / "refs" / "reports" / "runtime_trace_summary_20260624_combined.json"
    with tempfile.TemporaryDirectory(prefix="runtime_proof_lanes_") as tmp:
        out_json = Path(tmp) / "proof_lanes.json"
        out_md = Path(tmp) / "proof_lanes.md"
        proc = subprocess.run(
            [
                sys.executable,
                str(script),
                "--runtime-summary-json",
                str(source),
                "--output-json",
                str(out_json),
                "--output-md",
                str(out_md),
            ],
            cwd=root,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(proc.stdout, end="")
        report = json.loads(out_json.read_text(encoding="utf-8"))
        assert report["kind"] == "runtime_trace_proof_lane_summary"
        assert report["status_counts"]["answered_partial"] >= 1
        request_ids = {row["request_id"] for row in report["requests"]}
        assert "olmdirectionalblur_angle0_diagonal_residual_witness_20260622" in request_ids
        assert "olmsmoother2_current_aex_f270_witness_trace_20260621" in request_ids
        md = out_md.read_text(encoding="utf-8")
        for needle in (
            "Runtime Trace Proof-Lane Summary",
            "olmdirectionalblur_angle0_diagonal_residual_witness_20260622",
            "rowdriver/group-membership",
            "olmsmoother2_current_aex_f270_witness_trace_20260621",
        ):
            if needle not in md:
                raise AssertionError(f"markdown missing {needle!r}")
    print("[OK] summarize runtime trace proof lanes smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
