#!/usr/bin/env python3
"""Regression test for the natural B150 replay/oracle evidence."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROBE = HERE / "probe_radialblur_natural_b150_replay_oracle_20260717.py"


def main() -> int:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        output = root / "report.json"
        markdown = root / "report.md"
        result = subprocess.run([sys.executable, str(PROBE), "--output-json", str(output), "--output-md", str(markdown)], check=False)
        assert result.returncode == 0, result.returncode
        report = json.loads(output.read_text(encoding="utf-8"))
        assert report["status"] == "pass"
        assert report["classification"] == "bounded-natural-b150-f32-oracle-match"
        assert all(report["gates"].values()), report["gates"]
        assert len(report["run"]["comparisons"]) == 196
        assert report["run"]["record"]["spans"] == [1, 0]
        assert "no Windows or AE-exact claim" in markdown.read_text(encoding="utf-8")
    print("[OK] natural B150 replay matches independent float32 oracle")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
