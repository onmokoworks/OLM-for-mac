#!/usr/bin/env python3
"""Smoke-test scripts/analyze_distancegradation_case0023_source_candidates.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="olmdg_case0023_source_candidates_") as tmp:
        out_json = Path(tmp) / "report.json"
        out_md = Path(tmp) / "report.md"
        subprocess.run(
            [
                sys.executable,
                str(root / "scripts" / "analyze_distancegradation_case0023_source_candidates.py"),
                "--output-json",
                str(out_json),
                "--output-md",
                str(out_md),
            ],
            cwd=root,
            check=True,
        )
        report = json.loads(out_json.read_text(encoding="utf-8"))
        assert report["kind"] == "olmdistancegradation_case0023_source_candidates_audit"
        assert report["residual_summary"]["total_px"] == 73
        assert report["family_status"]["threshold_family"]["status"] == "threshold-family-reference-generation-split-candidate"
        assert report["family_status"]["edge_family"]["status"] == "upstream-field-ownership-still-live"
        assert report["edge_family_candidates"][0]["site"] == "build_distance_field_both_ownership"
        assert report["edge_family_candidates"][1]["site"] == "dt_to_normalized_constant_threshold"
        assert report["edge_family_candidates"][2]["site"] == "compose_pixel_constant_endpoint"
        assert report["edge_family_candidates"][0]["line"] == 508
        assert report["edge_family_candidates"][1]["line"] == 440
        assert report["edge_family_candidates"][2]["line"] == 558
        assert report["threshold_family_candidates"][0]["site"] == "current_aex_export_provenance_gate"
        assert report["pending_windows_followup"]["request_id"] == "olmdistancegradation_case0023_refcon_stack_wordmap_followup_20260702"
        assert "output-word address" in report["windows_requirement"]
        assert report["provenance_reference_request"]["request_id"] == "olmdistancegradation_case0023_current_aex_recapture_20260702"
        md = out_md.read_text(encoding="utf-8")
        for needle in (
            "OLMDistanceGradation case_0023 Source-Candidates Audit",
            "Family Status",
            "Threshold Crossing Witness",
            "build_distance_field_both_ownership",
            "compose_pixel_constant_endpoint",
            "Provenance Export Follow-up",
            "Requirement:",
        ):
            if needle not in md:
                raise AssertionError(f"markdown missing {needle}")
    print("[OK] DistanceGradation case_0023 source-candidates smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
