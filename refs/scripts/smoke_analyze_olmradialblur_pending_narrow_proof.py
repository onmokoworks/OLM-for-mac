#!/usr/bin/env python3
"""Smoke-test scripts/analyze_olmradialblur_pending_narrow_proof.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="olmradial_pending_") as tmp:
        out_json = Path(tmp) / "pending_narrow.json"
        out_md = Path(tmp) / "pending_narrow.md"
        subprocess.run(
            [
                sys.executable,
                str(root / "scripts" / "analyze_olmradialblur_pending_narrow_proof.py"),
                "--output-json",
                str(out_json),
                "--output-md",
                str(out_md),
            ],
            cwd=root,
            check=True,
        )
        report = json.loads(out_json.read_text(encoding="utf-8"))
        assert report["kind"] == "olmradialblur_pending_narrow_proof"
        assert report["active_request"]["request_id"] == "olmradialblur_tiny_rotation_anchor_context_watch_followup_20260702"
        assert report["active_request"]["status"] == "superseded"
        lanes = {row["lane"]: row for row in report["lanes"]}
        assert lanes["zoom_context"]["witness"]["x"] == 6 and lanes["zoom_context"]["witness"]["y"] == 0
        assert lanes["tiny_rotation_active"]["witness"]["x"] == 1614 and lanes["tiny_rotation_active"]["witness"]["y"] == 6
        assert lanes["inner_context"]["status"] == "parked-typed-per-cell-witness-still-separate"
        assert lanes["zoom_context"]["windows_final_rgba_u8"] == [20, 3, 3, 254]
        assert lanes["tiny_rotation_active"]["lane_audit"]["reference_bright_count"] == 17
        assert lanes["tiny_rotation_active"]["lane_audit"]["all_variants_keep_bright_count_zero"] is True
        assert "+0x4eb9/+0x4ec8" in lanes["tiny_rotation_active"]["required_next_proof"]
        md = out_md.read_text(encoding="utf-8")
        for needle in (
            "zoom_context",
            "tiny_rotation_active",
            "inner_context",
            "1614,6",
            "olmradialblur_tiny_rotation_anchor_context_watch_followup_20260702",
            "17",
        ):
            if needle not in md:
                raise AssertionError(f"markdown missing {needle}")
    print("[OK] OLMRadialBlur pending narrow proof smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
