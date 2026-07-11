#!/usr/bin/env python3
"""Smoke-test the RadialBlur Zoom final-sample float sequence probe."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="olmradialblur_floatseq_smoke_") as tmp:
        tmp_path = Path(tmp)
        locus_json = tmp_path / "locus.json"
        locus_md = tmp_path / "locus.md"
        report_json = tmp_path / "floatseq.json"
        report_md = tmp_path / "floatseq.md"
        proc_locus = subprocess.run(
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
        print(proc_locus.stdout, end="" if proc_locus.stdout.endswith("\n") else "\n")
        if proc_locus.returncode != 0:
            return proc_locus.returncode
        proc = subprocess.run(
            [
                sys.executable,
                "scripts/analyze_olmradialblur_zoom_final_sample_float_sequence.py",
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
        if report.get("kind") != "olmradialblur_zoom_case0009_final_sample_float_sequence":
            raise AssertionError("unexpected report kind")
        by_x = {point["x"]: point for point in report["points"]}
        if by_x[7]["cell_alpha"] != [1.0, 1.0, 1.0, 1.0]:
            raise AssertionError("x=7 should remain the all-one alpha spoiler")
        if by_x[7]["q_epsilon"]["f32_sequential_sum"] != 255:
            raise AssertionError("weight precision alone should not explain x=7 under epsilon quantization")
        epsilon = [
            item
            for item in report["classifications"]
            if item["sequence"] == "f32_sequential_sum" and item["quantizer"] == "epsilon"
        ][0]
        if 7 not in epsilon["fn"]:
            raise AssertionError("x=7 should remain a false negative for f32 sequential epsilon")
        if "coordinate generation" not in report["interpretation"]:
            raise AssertionError("interpretation should route next proof to coordinates/cell selection")
    print("[OK] RadialBlur Zoom final-sample float sequence smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
