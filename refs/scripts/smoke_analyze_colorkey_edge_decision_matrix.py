#!/usr/bin/env python3
"""Smoke-test scripts/analyze_colorkey_edge_decision_matrix.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    trace_json = root / "refs" / "reports" / "runtime_trace_comparisons" / "olmcolorkey_edge_trace_latest.json"
    if not trace_json.exists():
        proc = subprocess.run(
            [
                sys.executable,
                "scripts/compare_colorkey_edge_trace.py",
                "--runtime-summary-json",
                "refs/reports/runtime_trace_summary.json",
                "--output-json",
                str(trace_json),
                "--output-md",
                "refs/reports/runtime_trace_comparisons/olmcolorkey_edge_trace_latest.md",
            ],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
        if proc.returncode != 0:
            return proc.returncode

    with tempfile.TemporaryDirectory(prefix="olmcolorkey_edge_decision_") as tmp:
        out_json = Path(tmp) / "decision_matrix.json"
        out_md = Path(tmp) / "decision_matrix.md"
        proc = subprocess.run(
            [
                sys.executable,
                "scripts/analyze_colorkey_edge_decision_matrix.py",
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
        if report.get("kind") != "olmcolorkey_edge_decision_matrix":
            raise AssertionError("unexpected report kind")
        if report["decision"] != "preserve-normalized-ae-exact":
            raise AssertionError("expected ColorKey Edge to preserve normalized exact behavior")
        if report["normalized_8bpc"]["exact_count"] != 9:
            raise AssertionError("expected 9/9 normalized ColorKey cases to be exact")
        if (report.get("windows_16bpc_reference") or {}).get("case_count") != 9:
            raise AssertionError("expected 9 covered ColorKey 16bpc reference cases")
        if (report.get("windows_16bpc_reference") or {}).get("status") != "reference-covered-compare-pending":
            raise AssertionError("expected ColorKey 16bpc references to await Mac AE comparison")
        if report["legacy_split"]["classification"] != "reference-generation-split":
            raise AssertionError("expected case_0009 to remain a reference-generation split")
        if report["legacy_split"]["legacy_max_diff"] != 47:
            raise AssertionError("expected legacy case_0009 max drift to remain 47")
        if report["runtime_trace"]["classification"] != "not-actionable":
            raise AssertionError("expected current ColorKey Edge trace to be non-actionable")
        markdown = out_md.read_text(encoding="utf-8")
        for needle in (
            "Decision Matrix",
            "preserve-normalized-ae-exact",
            "9/9 exact",
            "Windows 16bpc reference",
            "case_0009",
        ):
            if needle not in markdown:
                raise AssertionError(f"Markdown missing {needle!r}")
    print("[OK] ColorKey Edge decision matrix smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
