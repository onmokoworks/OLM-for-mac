#!/usr/bin/env python3
"""Smoke-test scripts/analyze_olmradialblur_zoom_source_candidates.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="olmrb_zoom_source_candidates_") as tmp:
        out_json = Path(tmp) / "report.json"
        out_md = Path(tmp) / "report.md"
        subprocess.run(
            [
                sys.executable,
                str(root / "scripts" / "analyze_olmradialblur_zoom_source_candidates.py"),
                "--output-json",
                str(out_json),
                "--output-md",
                str(out_md),
            ],
            cwd=root,
            check=True,
        )
        report = json.loads(out_json.read_text(encoding="utf-8"))
        assert report["kind"] == "olmradialblur_zoom_source_candidates_audit"
        assert report["lane_summary"]["center_gap"] == 143
        assert report["lane_summary"]["largest_gap_x"] == 8
        assert report["lane_summary"]["largest_gap"] == 208
        assert report["source_candidates"][0]["site"] == "zoom_polar_population_and_validity_capture"
        assert report["source_candidates"][1]["site"] == "zoom_alpha_accumulation_and_denominator_state"
        assert report["source_candidates"][2]["site"] == "zoom_final_inverse_sample_and_u8_writeback"
        assert report["source_candidates"][0]["line"] == 709
        assert report["source_candidates"][1]["line"] == 732
        assert report["source_candidates"][2]["line"] == 805
        md = out_md.read_text(encoding="utf-8")
        for needle in (
            "OLMRadialBlur Zoom Source-Candidates Audit",
            "zoom_polar_population_and_validity_capture",
            "zoom_alpha_accumulation_and_denominator_state",
            "zoom_final_inverse_sample_and_u8_writeback",
        ):
            if needle not in md:
                raise AssertionError(f"markdown missing {needle}")
    print("[OK] OLMRadialBlur Zoom source-candidates smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
