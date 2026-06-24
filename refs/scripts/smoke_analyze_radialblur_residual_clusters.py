#!/usr/bin/env python3
"""Smoke-test OLMRadialBlur residual cluster audit."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main() -> int:
    root = repo_root()
    py = sys.executable
    for smoke in ("refs/scripts/smoke_olmradialblur_cpp_zoom_cli.py", "refs/scripts/smoke_olmradialblur_cpp_tiny_rotation_cli.py"):
        proc = subprocess.run([py, smoke], cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if proc.returncode != 0:
            print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
            return proc.returncode
    with tempfile.TemporaryDirectory(prefix="olmradialblur_residual_clusters_") as tmp:
        out_dir = Path(tmp) / "report"
        proc = subprocess.run(
            [py, "scripts/analyze_radialblur_residual_clusters.py", "--output-dir", str(out_dir)],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
        if proc.returncode != 0:
            return proc.returncode
        data = json.loads((out_dir / "residual_clusters.json").read_text(encoding="utf-8"))
        cases = {case["name"]: case for case in data.get("cases", [])}
        if cases["zoom_case_0009"]["max_diff"] != 1:
            raise AssertionError("expected Zoom residual to remain max=1")
        if cases["zoom_case_0009"]["classification"]["residual_kind"] != "rgba-off-by-one":
            raise AssertionError("expected Zoom residual to classify as low-amplitude off-by-one")
        if "pre-round/pre-clamp" not in cases["zoom_case_0009"]["recommended_next_evidence"]:
            raise AssertionError("expected Zoom residual to request writeback/rounding evidence")
        if cases["tiny_rotation_case_0010"]["max_diff"] != 255:
            raise AssertionError("expected tiny Rotation residual to expose high-max witness")
        if (
            cases["tiny_rotation_case_0010"]["classification"]["residual_kind"]
            != "high-rgb-border-sampler-or-validity"
        ):
            raise AssertionError("expected tiny Rotation residual to classify as border sampler/validity")
        if "border validity branch" not in cases["tiny_rotation_case_0010"]["recommended_next_evidence"]:
            raise AssertionError("expected tiny Rotation residual to request sampler/validity evidence")
        if cases["tiny_rotation_case_0010"]["largest_components"][0]["size"] < 10:
            raise AssertionError("expected non-trivial tiny Rotation residual component")
        markdown = (out_dir / "residual_clusters.md").read_text(encoding="utf-8")
        if "Recommended next evidence" not in markdown:
            raise AssertionError("expected markdown to include next-evidence guidance")
        shutil.rmtree(out_dir, ignore_errors=True)
    print("[OK] RadialBlur residual cluster audit smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
