#!/usr/bin/env python3
"""Regression test for the fail-closed full-size witness boundary."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROBE = HERE / "probe_radialblur_natural_fullsize_precollapse_witness_20260717.py"


def main() -> int:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        result = subprocess.run(
            [sys.executable, str(PROBE), "--output-json", str(root / "witness.json"), "--output-md", str(root / "witness.md")],
            check=False,
        )
        assert result.returncode == 2
        report = json.loads((root / "witness.json").read_text(encoding="utf-8"))
        assert report["status"] == "blocked"
        assert report["classification"] == "blocked-fail-closed-no-resumable-full-size-checkpoint"
        assert report["target"]["stop_before_collapse"] == "0x180005c9f"
        assert report["target"]["rgba_plane"] == "work+0x4210"
        assert report["target"]["scalar_plane"] == "work+0x4218"
        assert report["required_observation"]["cells"] == [[1047, 1095], [1047, 1096], [1048, 1095], [1048, 1096]]
        assert "250M" in report["blocker"]
    print("[OK] full-size natural pre-collapse witness fails closed without resumable state")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
