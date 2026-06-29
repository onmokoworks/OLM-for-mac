#!/usr/bin/env python3
"""Smoke-test scripts/analyze_directionalblur_scatter_static_facts.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="olmdirectionalblur_scatter_static_") as tmp:
        tmp_path = Path(tmp)
        out_json = tmp_path / "scatter_static.json"
        out_md = tmp_path / "scatter_static.md"
        proc = subprocess.run(
            [
                sys.executable,
                "scripts/analyze_directionalblur_scatter_static_facts.py",
                "--output-json",
                str(out_json),
                "--output-md",
                str(out_md),
            ],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(proc.stdout, end="")
        if proc.returncode != 0:
            return proc.returncode
        report = json.loads(out_json.read_text(encoding="utf-8"))
        if report.get("kind") != "olmdirectionalblur_scatter_static_facts":
            raise AssertionError(report.get("kind"))
        conclusions = report["conclusions"]
        if conclusions["front_boundary_rule"] != "front call clips span to x and starts at destination x-1":
            raise AssertionError(conclusions["front_boundary_rule"])
        if conclusions["back_boundary_rule"] != "back call clips span to width-x and starts at destination x+1":
            raise AssertionError(conclusions["back_boundary_rule"])
        if conclusions["write_direction_rule"] != "front helper writes strictly left of the source x; back helper writes strictly right":
            raise AssertionError(conclusions["write_direction_rule"])
        md = out_md.read_text(encoding="utf-8")
        required = [
            "front call clips span to x and starts at destination x-1",
            "back call clips span to width-x and starts at destination x+1",
            "scatter is skipped when source A alpha is exactly zero before helper dispatch",
            "broad scatter toggles should not be promoted globally",
        ]
        for needle in required:
            if needle not in md:
                raise AssertionError(f"markdown missing {needle!r}")
    print("[OK] DirectionalBlur scatter static facts smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
