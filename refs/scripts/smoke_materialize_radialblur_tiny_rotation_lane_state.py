#!/usr/bin/env python3
"""Smoke test for materialize_radialblur_tiny_rotation_lane_state.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "materialize_radialblur_tiny_rotation_lane_state.py"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olmrb_tiny_lane_state_") as tmp:
        tmp_path = Path(tmp)
        out_json = tmp_path / "out.json"
        out_md = tmp_path / "out.md"
        subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--stamp",
                "20990101",
                "--output-json",
                str(out_json),
                "--output-md",
                str(out_md),
            ],
            cwd=ROOT,
            check=True,
        )
        data = json.loads(out_json.read_text(encoding="utf-8"))
        assert data["kind"] == "olmradialblur_tiny_rotation_lane_state"
        assert data["status"] == "tiny-rotation-pending-upstream-rgb-or-substitute-proof"
        assert data["same_row_boundary"]["direct_source_cells_all_black"] is True
        assert data["row_coupling_boundary"]["reference_bright_count"] == 17
        assert data["pending_windows_followup"]["request_id"] == "olmradialblur_tiny_rotation_anchor_context_watch_followup_20260702"
        text = out_md.read_text(encoding="utf-8")
        assert "OLMRadialBlur tiny Rotation Lane State" in text
        assert "Pending Windows Follow-up" in text
    print("[OK] materialize_radialblur_tiny_rotation_lane_state smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
