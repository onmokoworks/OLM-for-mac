#!/usr/bin/env python3
"""Smoke-test scripts/analyze_distancegradation_decision_matrix.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    trace_json = root / "refs" / "reports" / "runtime_trace_comparisons" / "olmdistancegradation_field_prep_latest.json"
    if not trace_json.exists():
        proc = subprocess.run(
            [
                sys.executable,
                "scripts/compare_distancegradation_trace.py",
                "--runtime-summary-json",
                "refs/reports/runtime_trace_summary.json",
                "--output-json",
                str(trace_json),
                "--output-md",
                "refs/reports/runtime_trace_comparisons/olmdistancegradation_field_prep_latest.md",
            ],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
        if proc.returncode != 0:
            return proc.returncode

    with tempfile.TemporaryDirectory(prefix="olmdistancegradation_decision_") as tmp:
        out_json = Path(tmp) / "decision_matrix.json"
        out_md = Path(tmp) / "decision_matrix.md"
        proc = subprocess.run(
            [
                sys.executable,
                "scripts/analyze_distancegradation_decision_matrix.py",
                "--output-json",
                str(out_json),
                "--output-md",
                str(out_md),
            ],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
        if proc.returncode != 0:
            return proc.returncode
        report = json.loads(out_json.read_text(encoding="utf-8"))
        if report.get("kind") != "olmdistancegradation_decision_matrix":
            raise AssertionError("unexpected report kind")
        if report["decision"] != "preserve-normalized-ae-exact":
            raise AssertionError("expected DistanceGradation to preserve normalized exact behavior")
        if report["normalized_8bpc"]["exact_count"] != 29:
            raise AssertionError("expected 29/29 normalized DistanceGradation cases to be exact")
        ref16 = report.get("windows_16bpc_reference") or {}
        if ref16.get("case_count") != 29:
            raise AssertionError("expected 29 covered DistanceGradation 16bpc reference cases")
        if ref16.get("status") != "reference-covered-compare-pending":
            raise AssertionError("expected DistanceGradation 16bpc references to await Mac AE comparison")
        if ref16.get("groups") != {"basic": 12, "blur": 1, "extended": 16}:
            raise AssertionError("unexpected DistanceGradation 16bpc group coverage")
        if report["legacy_drift"]["classification"] != "normalized-software-exact-with-legacy-drift":
            raise AssertionError("expected normalized exact with legacy drift")
        if report["legacy_drift"]["legacy_nonzero_count"] != 7:
            raise AssertionError("expected seven legacy-only drift cases")
        if report["runtime_trace"]["classification"] != "not-actionable":
            raise AssertionError("expected current DistanceGradation trace to be non-actionable")
        markdown = out_md.read_text(encoding="utf-8")
        for needle in (
            "Decision Matrix",
            "preserve-normalized-ae-exact",
            "29/29 exact",
            "Windows 16bpc reference",
            "case_0012",
        ):
            if needle not in markdown:
                raise AssertionError(f"Markdown missing {needle!r}")
    print("[OK] DistanceGradation decision matrix smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
