#!/usr/bin/env python3
"""Smoke-test scripts/analyze_directionalblur_witness_contract.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="olmdirectionalblur_witness_contract_") as tmp:
        tmp_path = Path(tmp)
        output_json = tmp_path / "witness_contract.json"
        output_md = tmp_path / "witness_contract.md"
        proc = subprocess.run(
            [
                sys.executable,
                "scripts/analyze_directionalblur_witness_contract.py",
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
        if report.get("kind") != "olmdirectionalblur_witness_contract":
            raise AssertionError(report.get("kind"))
        if report.get("decision") != "blocked-await-runtime-or-asm-proof":
            raise AssertionError(report.get("decision"))
        if report["runtime_trace"].get("has_per_pixel_values") is not False:
            raise AssertionError(report["runtime_trace"])
        cases = {row["case_id"]: row for row in report["residuals"]}
        if cases["case_0001"]["kind"] != "angle0-rgb-only-rowdriver-or-valid-alpha":
            raise AssertionError(cases)
        if cases["case_0001"]["alpha_max"] != 0:
            raise AssertionError(cases["case_0001"])
        if cases["case_0005"]["kind"] != "diagonal-rgb-alpha-rotate-validity":
            raise AssertionError(cases)
        if "measurement baselines only" not in "\n".join(report["keep"]):
            raise AssertionError(report["keep"])
        md = output_md.read_text(encoding="utf-8")
        if "angle-0 rowdriver" not in md or "diagonal rotate" not in md:
            raise AssertionError("markdown missing witness proof text")
    print("[OK] DirectionalBlur witness contract smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
