#!/usr/bin/env python3
"""Smoke-test scripts/analyze_soft_reference_canonicalization.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    repo = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="soft_ref_canon_smoke_") as tmp:
        out_json = Path(tmp) / "canonicalization.json"
        out_md = Path(tmp) / "canonicalization.md"
        proc = subprocess.run(
            [
                sys.executable,
                "scripts/analyze_soft_reference_canonicalization.py",
                "--output-json",
                str(out_json),
                "--output-md",
                str(out_md),
            ],
            cwd=repo,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
        if proc.returncode != 0:
            return proc.returncode
        report = json.loads(out_json.read_text(encoding="utf-8"))
        features = {row["name"]: row for row in report["features"]}
        expected_counts = {
            "OLMBlur": 7,
            "OLMColorKey": 9,
            "OLMDistanceGradation basic": 12,
            "OLMDistanceGradation extended": 16,
            "OLMDistanceGradation blur": 1,
        }
        for name, expected_count in expected_counts.items():
            row = features.get(name)
            if row is None:
                raise AssertionError(f"missing feature row: {name}")
            if row["case_count"] != expected_count:
                raise AssertionError(f"{name}: expected {expected_count} cases, got {row['case_count']}")
            if row["normalized_nonzero_count"] != 0:
                raise AssertionError(f"{name}: normalized refs should be exact")
            if row["canonical_8bpc_status"] != "normalized-software-exact":
                raise AssertionError(f"{name}: unexpected status {row['canonical_8bpc_status']}")
        markdown = out_md.read_text(encoding="utf-8")
        for needle in ("8bpc Software Reference Canonicalization Audit", "OLMBlur", "OLMDistanceGradation"):
            if needle not in markdown:
                raise AssertionError(f"markdown missing {needle}")
    print("[OK] software reference canonicalization smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
