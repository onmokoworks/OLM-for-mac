#!/usr/bin/env python3
"""Smoke-test scripts/analyze_olmblur_pending_final_word_proof.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="olmblur_pending_final_word_") as tmp:
        out_json = Path(tmp) / "pending_final_word.json"
        out_md = Path(tmp) / "pending_final_word.md"
        subprocess.run(
            [
                sys.executable,
                str(root / "scripts" / "analyze_olmblur_pending_final_word_proof.py"),
                "--output-json",
                str(out_json),
                "--output-md",
                str(out_md),
            ],
            cwd=root,
            check=True,
        )
        report = json.loads(out_json.read_text(encoding="utf-8"))
        assert report["kind"] == "olmblur_pending_final_word_proof"
        assert report["date"] == "2026-06-29"
        assert report["status"] == "historical-superseded-by-closeout-gate"
        assert report["superseded_by"]["report"].endswith("refs/conformance/olmblur_closeout_gate_audit_20260701.md")
        assert report["witness_families"][0]["case_id"] == "olmblur__case_0006"
        assert report["witness_families"][1]["case_id"] == "olmblur__case_0007"
        assert report["witness_families"][0]["latest_windows_runtime_note"]["windows_final_rgba"] == [185, 0, 0, 255]
        assert report["witness_families"][1]["latest_windows_runtime_note"]["windows_writeback_family"] == "OLMBlur+0x7FDF"
        assert "runtime_trace_summary_olmblur_repeat_threshold_20260629_235638.json" in report["latest_runtime_summary"]
        md = out_md.read_text(encoding="utf-8")
        for needle in (
            "Historical status",
            "Superseded by",
            "Latest Windows runtime note",
            "case_0006",
            "case_0007",
            "OLMBlur+0x7FDF",
        ):
            if needle not in md:
                raise AssertionError(f"markdown missing {needle}")
    print("[OK] OLMBlur pending final-word proof smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
