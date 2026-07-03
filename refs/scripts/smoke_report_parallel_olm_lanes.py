#!/usr/bin/env python3
"""Smoke-test the parallel lane report generator."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        out_json = tmp / "parallel_lane_report.json"
        out_md = tmp / "parallel_lane_report.md"
        proc = subprocess.run(
            [
                "python3",
                "scripts/report_parallel_olm_lanes.py",
                "--output-json",
                str(out_json),
                "--output-md",
                str(out_md),
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        if proc.returncode != 0:
            print(proc.stdout, file=sys.stderr, end="")
            return proc.returncode
        data = json.loads(out_json.read_text(encoding="utf-8"))
        if data.get("kind") != "olm_parallel_lane_report":
            print("unexpected report kind", file=sys.stderr)
            return 1
        if len(data.get("bitdepth_lanes", [])) < 3:
            print("missing bitdepth lanes", file=sys.stderr)
            return 1
        if len(data.get("provenance_lanes", [])) < 3:
            print("missing provenance lanes", file=sys.stderr)
            return 1
        if not out_md.exists():
            print("missing markdown output", file=sys.stderr)
            return 1
    print("[OK] parallel lane report smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
