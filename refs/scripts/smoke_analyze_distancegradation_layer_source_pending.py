#!/usr/bin/env python3
"""Smoke-test scripts/analyze_distancegradation_layer_source_pending.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="olmdg_pending_layer_") as tmp:
        out_json = Path(tmp) / "pending_layer.json"
        out_md = Path(tmp) / "pending_layer.md"
        subprocess.run(
            [
                sys.executable,
                str(root / "scripts" / "analyze_distancegradation_layer_source_pending.py"),
                "--output-json",
                str(out_json),
                "--output-md",
                str(out_md),
            ],
            cwd=root,
            check=True,
        )
        report = json.loads(out_json.read_text(encoding="utf-8"))
        assert report["kind"] == "olmdistancegradation_layer_source_pending_proof"
        assert "runtime_trace_summary_distancegradation_layer_no_bg_source_ownership_20260629_235638.json" in report["latest_runtime_summary"]
        assert report["witness_cases"][0]["case_id"] == "olmdistancegradation_extended__case_0012"
        assert report["witness_cases"][1]["case_id"] == "olmdistancegradation_extended__case_0016"
        assert report["witness_cases"][0]["latest_windows_runtime_note"]["branch_decision"]["uses_straight_source_times_output_alpha"] is True
        md = out_md.read_text(encoding="utf-8")
        for needle in (
            "Latest runtime summary",
            "case_0012",
            "case_0016",
            "straight-source-times-output-alpha",
        ):
            if needle not in md:
                raise AssertionError(f"markdown missing {needle}")
    print("[OK] OLMDistanceGradation pending layer-source proof smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
