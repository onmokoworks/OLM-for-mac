#!/usr/bin/env python3
"""Smoke-test scripts/analyze_olmblur_source_candidates.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="olmblur_source_candidates_") as tmp:
        out_json = Path(tmp) / "report.json"
        out_md = Path(tmp) / "report.md"
        subprocess.run(
            [
                sys.executable,
                str(root / "scripts" / "analyze_olmblur_source_candidates.py"),
                "--output-json",
                str(out_json),
                "--output-md",
                str(out_md),
            ],
            cwd=root,
            check=True,
        )
        report = json.loads(out_json.read_text(encoding="utf-8"))
        assert report["kind"] == "olmblur_source_candidates_audit"
        assert report["lane_summary"]["case0006_status"] == "current-aex-export-missing"
        assert report["lane_summary"]["case0007_status"] == "16bpc-resolved-8bpc-still-open-prestore-family"
        assert report["source_candidates"][0]["site"] == "store16_nonlegacy_writer_boundary"
        assert report["source_candidates"][1]["site"] == "nonlegacy_helper_accumulation"
        assert report["source_candidates"][2]["site"] == "legacy_carry_prev_horizontal_vertical"
        assert report["source_candidates"][0]["line"] == 451
        assert report["source_candidates"][1]["line"] == 113
        assert report["source_candidates"][2]["line"] == 254
        md = out_md.read_text(encoding="utf-8")
        for needle in (
            "OLMBlur Source-Candidates Audit",
            "store16_nonlegacy_writer_boundary",
            "nonlegacy_helper_accumulation",
            "legacy_carry_prev_horizontal_vertical",
        ):
            if needle not in md:
                raise AssertionError(f"markdown missing {needle}")
    print("[OK] OLMBlur source-candidates smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
