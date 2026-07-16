#!/usr/bin/env python3
"""Regression gates for the bounded reconstructed Zoom collapse witness."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROBE = HERE / "probe_radialblur_reconstructed_zoom_collapse_20260717.py"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="radialblur_zoom_collapse_test_") as directory:
        output_json = Path(directory) / "witness.json"
        output_md = Path(directory) / "witness.md"
        result = subprocess.run([sys.executable, str(PROBE), "--output-json", str(output_json),
                                 "--output-md", str(output_md)], capture_output=True, text=True)
        assert result.returncode == 0, result.stdout + result.stderr
        report = json.loads(output_json.read_text(encoding="utf-8"))
        assert report["status"] == "pass"
        assert report["classification"] == "bounded-actual-aex-collapse-proven"
        assert report["fixture"]["controls"] == [8, 24]
        assert report["gates"] == {
            "actual_collapse_entry_exit": True,
            "all_finite": True,
            "controls_present": True,
            "d80_matches_collapsed_x7": True,
            "discriminating_f250": True,
            "entry_counts": {"collapse_entry": 1, "collapse_exit": 1, "inverse_sampler": 1,
                              "scatter": 1, "worker": 1},
            "hashes": True,
            "oracle_matches_actual": True,
        }
        records = report["run"]["records"]
        assert [record["x"] for record in records] == [7, 8, 24]
        for record in records:
            assert "+0xf252_scalar" in record
            assert "+0xf250_rgba" in record
            assert "+0xe_collapsed_rgba" in record
        assert "FUN_180009D80" in records[0]

    print("[OK] reconstructed Zoom collapse x=7 with x=8/24 controls")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
