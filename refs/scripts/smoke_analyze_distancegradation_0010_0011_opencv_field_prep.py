#!/usr/bin/env python3
"""Smoke test for the OLMDistanceGradation 0010/0011 field-prep audit."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olmdg_field_prep_audit_") as td:
        out = Path(td)
        json_path = out / "report.json"
        md_path = out / "report.md"
        proc = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/analyze_distancegradation_0010_0011_opencv_field_prep.py"),
                "--output-json",
                str(json_path),
                "--output-md",
                str(md_path),
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        print(proc.stdout, end="")
        if proc.returncode != 0:
            return proc.returncode
        report = json.loads(json_path.read_text(encoding="utf-8"))
        assert report["decision"] == "field-prep-structural-boundary-not-final-writer"
        assert all(row["marker_found"] for row in report["facts"])
        assert len(report["witnesses"]) == 3
        md = md_path.read_text(encoding="utf-8")
        assert "Next Proof" in md
        assert "FUN_181170480" in md
    print("smoke_analyze_distancegradation_0010_0011_opencv_field_prep OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
