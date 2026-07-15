#!/usr/bin/env python3
"""Regression gate for the accepted DG8 exact-coordinate bind failure."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "refs/windows_returns/20260715/20260715_184157__RETURN__OLMDISTANCEGRADATION_EXACT_FIXED_FAILURE.zip"
CLASSIFIER = ROOT / "scripts/classify_olmdistancegradation_exact_fixed_failure_20260715.py"


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="olmdg8_exact_fixed_failure_") as temp:
        output_json = Path(temp) / "report.json"
        output_md = Path(temp) / "report.md"
        subprocess.run(
            [
                sys.executable,
                str(CLASSIFIER),
                str(SOURCE),
                "--output-json",
                str(output_json),
                "--output-md",
                str(output_md),
            ],
            check=True,
        )
        report = json.loads(output_json.read_text(encoding="utf-8"))
        assert report["status"] == "accepted_exact_bind_failure"
        assert report["classification"] == "target-coordinate-not-observed-and-aex-hash-unbound"
        assert report["request_satisfied"] is False
        assert report["algorithm_evidence"] is False
        assert report["target_xy"] == [397, 281]
        assert report["callback"]["target_hit_count"] == 0
        assert report["callback"]["aex_sha256_present"] is False
        assert [case["case_id"] for case in report["cases"]] == [
            "case_0001",
            "case_0015",
            "case_0029",
        ]
        assert all(case["output_png"]["width_height"] == [1920, 1080] for case in report["cases"])
        assert "Algorithm evidence: no" in output_md.read_text(encoding="utf-8")
    print("[OK] DG8 exact-coordinate failure classifier smoke")


if __name__ == "__main__":
    main()
