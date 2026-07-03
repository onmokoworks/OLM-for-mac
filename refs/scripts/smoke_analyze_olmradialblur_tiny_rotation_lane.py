#!/usr/bin/env python3
"""Smoke-test scripts/analyze_olmradialblur_tiny_rotation_lane.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="olmrb_tiny_rotation_lane_") as tmp:
        out_json = Path(tmp) / "report.json"
        out_md = Path(tmp) / "report.md"
        subprocess.run(
            [
                sys.executable,
                str(root / "scripts" / "analyze_olmradialblur_tiny_rotation_lane.py"),
                "--output-json",
                str(out_json),
                "--output-md",
                str(out_md),
            ],
            cwd=root,
            check=True,
        )
        report = json.loads(out_json.read_text(encoding="utf-8"))
        assert report["kind"] == "olmradialblur_tiny_rotation_lane_audit"
        assert report["same_row_structure"]["direct_source_cells_all_black"] is True
        assert report["row_coupling_probe"]["reference_bright_count"] == 17
        assert report["row_coupling_probe"]["all_variants_keep_bright_count_zero"] is True
        assert report["pending_windows_followup"]["request_id"] == "olmradialblur_tiny_rotation_anchor_context_watch_followup_20260702"
        assert report["decision"]["status"] == "tiny-rotation-pending-upstream-rgb-or-substitute-proof"
        assert "+0x4eb9/+0x4ec8" in report["decision"]["next_windows_requirement"]
        md = out_md.read_text(encoding="utf-8")
        for needle in (
            "OLMRadialBlur tiny Rotation Lane Audit",
            "17",
            "(1614, 6)",
            "Next Windows requirement",
        ):
            if needle not in md:
                raise AssertionError(f"markdown missing {needle}")
    print("[OK] OLMRadialBlur tiny Rotation lane smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
