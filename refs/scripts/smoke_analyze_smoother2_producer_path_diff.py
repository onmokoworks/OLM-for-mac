#!/usr/bin/env python3
"""Smoke-test scripts/analyze_smoother2_producer_path_diff.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="olmsmoother2_producer_path_diff_") as tmp:
        tmp_path = Path(tmp)
        output_json = tmp_path / "producer_path_diff.json"
        output_md = tmp_path / "producer_path_diff.md"
        proc = subprocess.run(
            [
                sys.executable,
                "scripts/analyze_smoother2_producer_path_diff.py",
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
        if report.get("kind") != "olmsmoother2_current_aex_producer_path_diff":
            raise AssertionError(report.get("kind"))
        if report.get("decision") != "writer-anchored-producer-trace-ready":
            raise AssertionError(report.get("decision"))
        cases = {row["case_id"]: row for row in report.get("cases", [])}
        case_0004 = cases["legacy_case_0004_current_aex"]
        case_0012 = cases["legacy_case_0012_gamma5_red_blue_current_aex"]
        if case_0004["static_dispatch"]["hex"] != "0xd0":
            raise AssertionError(case_0004["static_dispatch"])
        if case_0012["static_dispatch"]["hex"] != "0x69":
            raise AssertionError(case_0012["static_dispatch"])
        if case_0004["local_summary"]["producer_shape"] != "empty polygon -> transparent passthrough":
            raise AssertionError(case_0004["local_summary"])
        if case_0012["local_summary"]["producer_shape"] != "cardinal6 append -> nonzero cce0 blend":
            raise AssertionError(case_0012["local_summary"])
        if case_0004["first_unresolved_stage"] != "c280-polygon-or-cce0-fallback":
            raise AssertionError(case_0004["first_unresolved_stage"])
        if case_0012["first_unresolved_stage"] != "cardinal6-e170-f270-e3a0-emit-chain":
            raise AssertionError(case_0012["first_unresolved_stage"])
        if case_0004["windows_writer_anchor"]["writer_raw"] != "0xe8e8e871":
            raise AssertionError(case_0004["windows_writer_anchor"])
        if case_0012["windows_writer_anchor"]["writer_raw"] != "0xffffff00":
            raise AssertionError(case_0012["windows_writer_anchor"])
        stage_names_0004 = [row["stage"] for row in case_0004["stage_rows"]]
        stage_names_0012 = [row["stage"] for row in case_0012["stage_rows"]]
        if stage_names_0004 != ["writer-anchor", "cce0-result", "c280-dispatch", "producer-branch"]:
            raise AssertionError(stage_names_0004)
        if stage_names_0012 != ["writer-anchor", "cce0-result", "c280-dispatch", "producer-branch"]:
            raise AssertionError(stage_names_0012)
        required_0012 = "\n".join(case_0012["required_windows_fields"])
        if "cardinal6 descriptor/key" not in required_0012:
            raise AssertionError(required_0012)
        required_0004 = "\n".join(case_0004["required_windows_fields"])
        if "helper append src xy / rgba / weight" not in required_0004:
            raise AssertionError(required_0004)
        md = output_md.read_text(encoding="utf-8")
        for needle in (
            "writer-anchored-producer-trace-ready",
            "OLMSmoother2 Producer-Path Diff",
            "c280-polygon-or-cce0-fallback",
            "cardinal6-e170-f270-e3a0-emit-chain",
            "0xe8e8e871",
            "0xffffff00",
            "Stage Matrix",
            "Required Windows Fields",
        ):
            if needle not in md:
                raise AssertionError(f"markdown missing {needle!r}")
    print("[OK] Smoother2 producer-path diff smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
