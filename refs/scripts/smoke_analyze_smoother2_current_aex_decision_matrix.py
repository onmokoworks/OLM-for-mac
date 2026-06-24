#!/usr/bin/env python3
"""Smoke-test scripts/analyze_smoother2_current_aex_decision_matrix.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="olmsmoother2_decision_matrix_") as tmp:
        tmp_path = Path(tmp)
        output_json = tmp_path / "decision_matrix.json"
        output_md = tmp_path / "decision_matrix.md"
        proc = subprocess.run(
            [
                sys.executable,
                "scripts/analyze_smoother2_current_aex_decision_matrix.py",
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
        print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
        if proc.returncode != 0:
            return proc.returncode

        report = json.loads(output_json.read_text(encoding="utf-8"))
        if report.get("kind") != "olmsmoother2_current_aex_decision_matrix":
            raise AssertionError("unexpected report kind")
        if report["curve_idx"]["classification"] != "rejected-inert":
            raise AssertionError("curve_idx sweep should remain rejected as inert")
        if not report["curve_idx"]["all_identical"]:
            raise AssertionError("curve_idx metrics should be identical across 0..8")
        if report["f270_suppression"]["classification"] != "rejected-worse":
            raise AssertionError("f270 suppression should remain rejected as worse")
        if report["f270_suppression"]["mean_sum"] <= report["f270_suppression"]["baseline_mean_sum"]:
            raise AssertionError("f270 suppression should worsen total mean")
        witnesses = {row["case_id"]: row for row in report["residuals"]["witnesses"]}
        if witnesses["legacy_case_0004_current_aex"]["xy"] != [1903, 519]:
            raise AssertionError("expected 0004 transparent-center witness")
        if witnesses["legacy_case_0012_gamma5_red_blue_current_aex"]["xy"] != [91, 841]:
            raise AssertionError("expected 0012 f270/e170 witness")
        if "global curve_idx" not in " ".join(report["next_evidence"]):
            raise AssertionError("expected next evidence to reject broad global toggles")
        markdown = output_md.read_text(encoding="utf-8")
        for needle in ("Decision Matrix", "rejected-inert", "rejected-worse", "0012 (91,841)"):
            if needle not in markdown:
                raise AssertionError(f"Markdown missing {needle!r}")
    print("[OK] Smoother2 current-AEX decision matrix smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
