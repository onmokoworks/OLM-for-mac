#!/usr/bin/env python3
"""Smoke test for materialize_smoother2_legacy_lane_state.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "materialize_smoother2_legacy_lane_state.py"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olmsm2_legacy_lane_state_") as tmp:
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
        assert data["kind"] == "olmsmoother2_legacy_lane_state"
        assert data["status"] == "writer-confirmed-internal-branch-unresolved"
        case_ids = {row["case_id"] for row in data["cases"]}
        assert "legacy_case_0004_current_aex" in case_ids
        assert "legacy_case_0012_gamma5_red_blue_current_aex" in case_ids
        text = out_md.read_text(encoding="utf-8")
        assert "OLMSmoother2 Legacy Lane State" in text
        assert "Required Windows Fields" in text
    print("[OK] materialize_smoother2_legacy_lane_state smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
