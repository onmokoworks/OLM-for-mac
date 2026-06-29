#!/usr/bin/env python3
"""Smoke-test scripts/analyze_directionalblur_witness_plan.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="olmdirectionalblur_witness_plan_") as tmp:
        tmp_path = Path(tmp)
        output_json = tmp_path / "witness_plan.json"
        output_md = tmp_path / "witness_plan.md"
        proc = subprocess.run(
            [
                sys.executable,
                "scripts/analyze_directionalblur_witness_plan.py",
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
        if report.get("kind") != "olmdirectionalblur_witness_plan":
            raise AssertionError(report.get("kind"))
        if report.get("decision") != "two-independent-witness-families":
            raise AssertionError(report.get("decision"))
        plans = {row["family"]: row for row in report["plans"]}
        angle0 = plans["angle0-rowdriver-valid-alpha"]
        diagonal = plans["diagonal-rotate-validity"]
        if angle0["primary_witness"]["xy"] != [494, 169]:
            raise AssertionError(angle0["primary_witness"])
        if angle0["scan_order_max_witness"]["xy"] != [465, 169]:
            raise AssertionError(angle0["scan_order_max_witness"])
        if diagonal["primary_witness"]["xy"] != [507, 367]:
            raise AssertionError(diagonal["primary_witness"])
        diagonal_companion_xys = [row["xy"] for row in diagonal["companion_witnesses"]]
        if [423, 187] not in diagonal_companion_xys:
            raise AssertionError(diagonal_companion_xys)
        md = output_md.read_text(encoding="utf-8")
        required = [
            "two-independent-witness-families",
            "rowdriver/group membership",
            "rotate sampler source coordinates",
            "Do not tune diagonal behavior from the angle-0 witness",
            "right-edge strip endpoint",
        ]
        for needle in required:
            if needle not in md:
                raise AssertionError(f"markdown missing {needle!r}")
    print("[OK] DirectionalBlur witness plan smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
