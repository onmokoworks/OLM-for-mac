#!/usr/bin/env python3
"""Smoke-test scripts/analyze_olmradialblur_tiny_rotation_source_candidates.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="olmrb_tiny_rotation_source_candidates_") as tmp:
        out_json = Path(tmp) / "report.json"
        out_md = Path(tmp) / "report.md"
        subprocess.run(
            [
                sys.executable,
                str(root / "scripts" / "analyze_olmradialblur_tiny_rotation_source_candidates.py"),
                "--output-json",
                str(out_json),
                "--output-md",
                str(out_md),
            ],
            cwd=root,
            check=True,
        )
        report = json.loads(out_json.read_text(encoding="utf-8"))
        assert report["kind"] == "olmradialblur_tiny_rotation_source_candidates_audit"
        assert report["lane_summary"]["direct_source_cells_all_black"] is True
        assert report["lane_summary"]["witness_direct_cluster_visibility"] is False
        assert report["lane_summary"]["reference_bright_count"] == 17
        assert report["source_candidates"][0]["site"] == "rotation_polar_population_and_validity_capture"
        assert report["source_candidates"][1]["site"] == "rotation_scatter_and_neighboring_row_ownership"
        assert report["source_candidates"][2]["site"] == "rotation_final_inverse_sample_and_u8_writeback"
        assert report["source_candidates"][0]["line"] == 934
        assert report["source_candidates"][1]["line"] == 952
        assert report["source_candidates"][2]["line"] == 1074
        assert report["pending_windows_followup"]["request_id"] == "olmradialblur_tiny_rotation_anchor_context_watch_followup_20260702"
        assert "+0x4eb9/+0x4ec8" in report["windows_requirement"]
        md = out_md.read_text(encoding="utf-8")
        for needle in (
            "OLMRadialBlur tiny Rotation Source-Candidates Audit",
            "rotation_polar_population_and_validity_capture",
            "rotation_scatter_and_neighboring_row_ownership",
            "rotation_final_inverse_sample_and_u8_writeback",
            "Requirement:",
        ):
            if needle not in md:
                raise AssertionError(f"markdown missing {needle}")
    print("[OK] OLMRadialBlur tiny Rotation source-candidates smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
