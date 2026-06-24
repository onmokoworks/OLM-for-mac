#!/usr/bin/env python3
"""Smoke-test scripts/analyze_radialblur_witness_contract.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="olmradialblur_witness_contract_") as tmp:
        tmp_path = Path(tmp)
        output_json = tmp_path / "witness_contract.json"
        output_md = tmp_path / "witness_contract.md"
        proc = subprocess.run(
            [
                sys.executable,
                "scripts/analyze_radialblur_witness_contract.py",
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
        if report.get("kind") != "olmradialblur_witness_contract":
            raise AssertionError(report.get("kind"))
        if report["zoom"].get("local_floor_minus_windows_u8") != [0, 0, 0, 1]:
            raise AssertionError(report["zoom"])
        if report["tiny_rotation"].get("closest_sampler_floor_u8") != [0, 0, 0, 255]:
            raise AssertionError(report["tiny_rotation"])
        if report["tiny_rotation"].get("windows_final_u8") != [255, 255, 255, 255]:
            raise AssertionError(report["tiny_rotation"])
        if report["inner"].get("best_by_mean_sum") != "loop-minus-one":
            raise AssertionError(report["inner"])
        facts = report["inner"].get("static_facts") or {}
        if "R14D" not in str(facts.get("effective_span")) or "30000" not in str(facts.get("table_step")):
            raise AssertionError(facts)
        md = output_md.read_text(encoding="utf-8")
        if "blocked-narrow-proof-only" not in md or "Do not change final byte packing" not in md:
            raise AssertionError("markdown missing expected contract text")
    print("[OK] RadialBlur witness contract smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
