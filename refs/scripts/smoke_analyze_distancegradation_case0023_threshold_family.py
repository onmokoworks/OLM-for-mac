#!/usr/bin/env python3
"""Smoke-test scripts/analyze_distancegradation_case0023_threshold_family.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="olmdg_case0023_threshold_") as tmp:
        out_json = Path(tmp) / "report.json"
        out_md = Path(tmp) / "report.md"
        subprocess.run(
            [
                sys.executable,
                str(root / "scripts" / "analyze_distancegradation_case0023_threshold_family.py"),
                "--output-json",
                str(out_json),
                "--output-md",
                str(out_md),
            ],
            cwd=root,
            check=True,
        )
        report = json.loads(out_json.read_text(encoding="utf-8"))
        assert report["kind"] == "olmdistancegradation_case0023_threshold_family_audit"
        assert report["residual"]["total_px"] == 73
        assert report["residual"]["edge_bucket"]["count"] == 65
        assert report["residual"]["threshold_bucket"]["count"] == 8
        assert report["plateau_probe"]["plateau_residual_px"] == 182793
        assert report["plateau_probe"]["threshold_bucket_invariant_under_plateau_probe"] is True
        roles = {row["role"]: row for row in report["threshold_triplet_roles"]}
        assert roles["below_threshold_same_row"]["x"] == 414 and roles["below_threshold_same_row"]["field_x"] == 0.0
        assert roles["first_above_threshold_same_row"]["x"] == 415 and roles["first_above_threshold_same_row"]["field_x"] == 1.0
        assert roles["deeper_plateau_same_row"]["x"] == 416 and roles["deeper_plateau_same_row"]["field_x"] == 1.0
        assert report["pending_windows_followup"]["request_id"] == "olmdistancegradation_case0023_refcon_stack_wordmap_followup_20260702"
        assert report["decision"]["status"] == "threshold-family-historical-bounded-context"
        assert "output-word address" in report["decision"]["next_windows_requirement"]
        md = out_md.read_text(encoding="utf-8")
        for needle in (
            "OLMDistanceGradation case_0023 Threshold-Family Audit",
            "182793",
            "first_above_threshold_same_row",
            "(415,393)",
            "Next Windows requirement",
        ):
            if needle not in md:
                raise AssertionError(f"markdown missing {needle}")
    print("[OK] DistanceGradation case_0023 threshold-family smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
