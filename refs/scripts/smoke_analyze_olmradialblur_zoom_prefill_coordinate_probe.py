#!/usr/bin/env python3
"""Smoke-test the RadialBlur Zoom prefill coordinate probe."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="olmradialblur_prefillcoord_smoke_") as tmp:
        tmp_path = Path(tmp)
        locus_json = tmp_path / "locus.json"
        locus_md = tmp_path / "locus.md"
        report_json = tmp_path / "prefill.json"
        report_md = tmp_path / "prefill.md"
        locus = subprocess.run(
            [
                sys.executable,
                "scripts/analyze_olmradialblur_zoom_quantize_locus.py",
                "--output-json",
                str(locus_json),
                "--output-md",
                str(locus_md),
            ],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(locus.stdout, end="" if locus.stdout.endswith("\n") else "\n")
        if locus.returncode != 0:
            return locus.returncode
        proc = subprocess.run(
            [
                sys.executable,
                "scripts/analyze_olmradialblur_zoom_prefill_coordinate_probe.py",
                "--locus-json",
                str(locus_json),
                "--output-json",
                str(report_json),
                "--output-md",
                str(report_md),
            ],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
        if proc.returncode != 0:
            return proc.returncode
        report = json.loads(report_json.read_text(encoding="utf-8"))
        if report.get("kind") != "olmradialblur_zoom_case0009_prefill_coordinate_probe":
            raise AssertionError("unexpected report kind")
        by_x = {point["x"]: point for point in report["points"]}
        if by_x[7]["current_cell_alpha"] != [1, 1, 1, 1]:
            raise AssertionError("x=7 must remain the all-one current-cell spoiler")
        if not by_x[7]["nearby_subone_python_prefill_cells"]:
            raise AssertionError("x=7 should expose a nearby sub-one repeat-sampler cell")
        if not by_x[6]["nearby_subone_python_prefill_cells"]:
            raise AssertionError("x=6 should expose the known sub-one repeat-sampler cell")
        if "sampled cell-set/coordinate difference" not in report["interpretation"]:
            raise AssertionError("interpretation should preserve cell-set/coordinate route")
    print("[OK] RadialBlur Zoom prefill-coordinate smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
