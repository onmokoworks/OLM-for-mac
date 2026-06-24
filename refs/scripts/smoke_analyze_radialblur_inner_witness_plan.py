#!/usr/bin/env python3
"""Smoke-test scripts/analyze_radialblur_inner_witness_plan.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="olmradialblur_inner_witness_plan_") as tmp:
        tmp_path = Path(tmp)
        output_json = tmp_path / "witness_plan.json"
        output_md = tmp_path / "witness_plan.md"
        proc = subprocess.run(
            [
                sys.executable,
                "scripts/analyze_radialblur_inner_witness_plan.py",
                "--output-json",
                str(output_json),
                "--output-md",
                str(output_md),
            ],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(proc.stdout, end="")
        if proc.returncode != 0:
            return proc.returncode
        report = json.loads(output_json.read_text(encoding="utf-8"))
        if report.get("kind") != "olmradialblur_inner_witness_plan":
            raise AssertionError(report.get("kind"))
        families = {row["family"]: row for row in report["families"]}
        if families["low-span"]["representative"]["case_id"] != "rb_inner_only_strength_large":
            raise AssertionError(families["low-span"]["representative"])
        if families["quality-strong"]["representative"]["case_id"] != "rb_inner_quality_1":
            raise AssertionError(families["quality-strong"]["representative"])
        if families["edge-prepass"]["representative"]["case_id"] != "rb_inner_edgefade_only":
            raise AssertionError(families["edge-prepass"]["representative"])
        markdown = output_md.read_text(encoding="utf-8")
        for needle in (
            "typed-inner-cell-witnesses-only",
            "rb_inner_only_strength_large",
            "rb_inner_quality_1",
            "FUN_180001c90",
        ):
            if needle not in markdown:
                raise AssertionError(f"missing markdown needle: {needle}")
    print("[OK] RadialBlur Inner witness plan smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
