#!/usr/bin/env python3
"""Smoke-test RadialBlur Zoom final-plane index variant probe."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="olmradialblur_index_variants_smoke_") as tmp:
        tmp_path = Path(tmp)
        locus_json = tmp_path / "locus.json"
        locus_md = tmp_path / "locus.md"
        report_json = tmp_path / "index_variants.json"
        report_md = tmp_path / "index_variants.md"
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
                "scripts/analyze_olmradialblur_zoom_final_plane_index_variants.py",
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
        if report.get("kind") != "olmradialblur_zoom_case0009_final_plane_index_variants":
            raise AssertionError("unexpected report kind")
        if report.get("target_alpha254") != [6, 7, 12]:
            raise AssertionError("unexpected target alpha set")
        if report.get("all_candidate_count", 0) < 100:
            raise AssertionError("expected a bounded but nontrivial variant search")
        best = report["top_candidates"][0]
        best_cls = sorted(best["classifications"], key=lambda item: item["score_tuple"])[0]
        if len(best_cls["tp"]) < 2:
            raise AssertionError("expected at least a partial target hit from bounded variants")
        if "not a Mac source change" not in report["interpretation"]:
            raise AssertionError("interpretation should avoid promoting candidate directly")
        if "Final-Plane Index Variant" not in report_md.read_text(encoding="utf-8"):
            raise AssertionError("markdown report missing title")
    print("[OK] RadialBlur Zoom final-plane index variant smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
