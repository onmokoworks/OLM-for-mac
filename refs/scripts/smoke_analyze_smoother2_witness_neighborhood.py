#!/usr/bin/env python3
"""Smoke-test scripts/analyze_smoother2_witness_neighborhood.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="olmsmoother2_witness_neighborhood_") as tmp:
        tmp_path = Path(tmp)
        output_json = tmp_path / "neighborhood.json"
        output_md = tmp_path / "neighborhood.md"
        proc = subprocess.run(
            [
                sys.executable,
                "scripts/analyze_smoother2_witness_neighborhood.py",
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
        if report.get("kind") != "olmsmoother2_witness_neighborhood":
            raise AssertionError(report.get("kind"))
        cases = {row["case_id"]: row for row in report["cases"]}
        case_0004 = cases["legacy_case_0004_current_aex"]
        case_0012 = cases["legacy_case_0012_gamma5_red_blue_current_aex"]
        if case_0004["classification"]["kind"] != "windows-adds-semitransparent-output-where-local-passthrough-is-transparent":
            raise AssertionError(case_0004["classification"])
        if case_0012["classification"]["kind"] != "local-adds-semitransparent-output-where-windows-stays-transparent":
            raise AssertionError(case_0012["classification"])
        if case_0004["center"]["reference_rgba"] != [103, 103, 103, 113]:
            raise AssertionError(case_0004["center"])
        if case_0012["center"]["candidate_rgba"] != [90, 90, 90, 91]:
            raise AssertionError(case_0012["center"])
        if case_0004["classification"]["strongest_neighbor_deltas"][0]["xy"] != [1903, 518]:
            raise AssertionError(case_0004["classification"]["strongest_neighbor_deltas"])
        if case_0012["classification"]["strongest_neighbor_deltas"][0]["xy"] != [91, 840]:
            raise AssertionError(case_0012["classification"]["strongest_neighbor_deltas"])
        for case in (case_0004, case_0012):
            if not case["classification"].get("trace_focus"):
                raise AssertionError(case["classification"])
        markdown = output_md.read_text(encoding="utf-8")
        for needle in (
            "narrow-witness-neighborhoods-only",
            "## Trace Focus",
            "strongest non-center cells",
            "Trace whether Windows c280",
            "Trace whether Windows suppresses",
        ):
            if needle not in markdown:
                raise AssertionError(f"missing markdown needle: {needle}")
    print("[OK] Smoother2 witness neighborhood smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
