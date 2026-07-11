#!/usr/bin/env python3
"""Smoke-test RadialBlur Zoom cell-set candidate probe."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="olmradialblur_cellset_smoke_") as tmp:
        tmp_path = Path(tmp)
        locus_json = tmp_path / "locus.json"
        locus_md = tmp_path / "locus.md"
        report_json = tmp_path / "cellset.json"
        report_md = tmp_path / "cellset.md"
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
                "scripts/analyze_olmradialblur_zoom_cellset_candidate.py",
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
        if report.get("kind") != "olmradialblur_zoom_case0009_cellset_candidate":
            raise AssertionError("unexpected report kind")
        if report.get("target_alpha254") != [6, 7, 12]:
            raise AssertionError("unexpected target alpha set")
        best = report["top_candidates"][0]
        best_cls = sorted(best["classifications"], key=lambda item: item["score_tuple"])[0]
        if len(best_cls["tp"]) < 2:
            raise AssertionError("expected at least a partial target hit from bounded candidates")
        if "witness request" not in report["interpretation"]:
            raise AssertionError("interpretation should avoid promoting candidate directly")
    print("[OK] RadialBlur Zoom cell-set candidate smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
