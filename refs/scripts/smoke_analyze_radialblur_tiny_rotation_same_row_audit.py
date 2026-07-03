#!/usr/bin/env python3
"""Smoke test for analyze_radialblur_tiny_rotation_same_row_audit.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="radialblur_same_row_smoke_") as tmp:
        tmp_path = Path(tmp)
        out_json = tmp_path / "report.json"
        out_md = tmp_path / "report.md"
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "analyze_radialblur_tiny_rotation_same_row_audit.py"),
                "--output-json",
                str(out_json),
                "--output-md",
                str(out_md),
            ],
            cwd=ROOT,
            check=True,
        )
        report = json.loads(out_json.read_text(encoding="utf-8"))
        assert report["kind"] == "olmradialblur_tiny_rotation_same_row_audit"
        assert report["row_length"] == 3
        assert report["rows"]
        witness = next(row for row in report["rows"] if row["xy"] == [1614, 6])
        assert witness["sample_u8"] == [0, 0, 0, 255]
        assert witness["cells"][0]["same_row_source_taps"] == [1603, 1602, 1601]
        assert "Same-Row Audit" in out_md.read_text(encoding="utf-8")
    print("[OK] analyze radialblur tiny rotation same-row audit smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
