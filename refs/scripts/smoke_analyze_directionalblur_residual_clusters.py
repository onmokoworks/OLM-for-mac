#!/usr/bin/env python3
"""Smoke-test OLMDirectionalBlur residual cluster audit."""

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
    proc = subprocess.run(
        [py, "refs/scripts/smoke_olmdirectionalblur_cpp_rotated_aex_full_choreo_cli.py"],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if "[DIFF]" not in proc.stdout:
        print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
        raise AssertionError("expected full-choreo diagnostic to produce DIFF output")
    with tempfile.TemporaryDirectory(prefix="olmdirectionalblur_residual_clusters_") as tmp:
        out_dir = Path(tmp) / "report"
        proc = subprocess.run(
            [py, "scripts/analyze_directionalblur_residual_clusters.py", "--output-dir", str(out_dir)],
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
        if cases["angle0_case_0001"]["max_diff"] < 100:
            raise AssertionError("expected angle0 witness to remain a high residual")
        if (
            cases["angle0_case_0001"]["classification"]["residual_kind"]
            != "angle0-rgb-only-rowdriver-or-valid-alpha"
        ):
            raise AssertionError("expected angle0 residual to classify as RGB-only rowdriver/valid-alpha")
        if cases["diagonal_case_0005"]["max_diff"] < 200:
            raise AssertionError("expected diagonal witness to remain a high residual")
        if (
            cases["diagonal_case_0005"]["classification"]["residual_kind"]
            != "diagonal-rgb-alpha-rotate-validity"
        ):
            raise AssertionError("expected diagonal residual to classify as rotate/validity")
        if cases["angle0_case_0001"]["channel_max_rgba"][3] != 0:
            raise AssertionError("expected angle0 residual to be RGB-only in this probe")
        shutil.rmtree(out_dir, ignore_errors=True)
    print("[OK] DirectionalBlur residual cluster audit smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
