#!/usr/bin/env python3
"""Smoke test for materialize_directionalblur_lane_state.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "materialize_directionalblur_lane_state.py"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olmdb_lane_state_") as tmp:
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
        assert data["kind"] == "olmdirectionalblur_lane_state"
        assert data["structural_base"] == "rotated-aex-full-choreo"
        assert data["runtime_status"] == "answered_partial"
        assert data["angle0_lane"]["classification"] == "angle0-rgb-only-rowdriver-or-valid-alpha"
        assert data["diagonal_lane"]["classification"] == "diagonal-rgb-alpha-rotate-validity"
        text = out_md.read_text(encoding="utf-8")
        assert "OLMDirectionalBlur Lane State" in text
        assert "Angle-0 lane" in text
        assert "Diagonal lane" in text
    print("[OK] materialize_directionalblur_lane_state smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
