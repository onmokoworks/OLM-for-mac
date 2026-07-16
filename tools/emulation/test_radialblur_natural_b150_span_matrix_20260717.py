#!/usr/bin/env python3
"""Regression test for natural B150 span generalization evidence."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROBE = HERE / "probe_radialblur_natural_b150_span_matrix_20260717.py"


def main() -> int:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        output, markdown = root / "matrix.json", root / "matrix.md"
        result = subprocess.run([sys.executable, str(PROBE), "--output-json", str(output), "--output-md", str(markdown)], check=False)
        assert result.returncode == 0, result.returncode
        report = json.loads(output.read_text(encoding="utf-8"))
        assert report["status"] == "pass"
        assert report["gates"] == {"inner_span_1": True, "outer_matrix_generalizes": True, "outer_span_2": True, "outer_span_3": True}
        assert report["inner_reachability"]["status"] == "reachable"
        assert all(len(s["outputs"]) == 196 for s in report["scenarios"])
        assert "no Windows or AE-exact claim" in markdown.read_text(encoding="utf-8")
    print("[OK] natural B150 spans 2/3 and inner span 1 match independent oracle")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
