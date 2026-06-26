#!/usr/bin/env python3
"""Smoke-test the OLMBlur decision matrix report."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olmblur_decision_") as tmp:
        out_dir = Path(tmp)
        report_json = out_dir / "decision_matrix.json"
        report_md = out_dir / "decision_matrix.md"
        subprocess.run(
            [
                "python3",
                str(ROOT / "scripts" / "analyze_olmblur_decision_matrix.py"),
                "--output-json",
                str(report_json),
                "--output-md",
                str(report_md),
            ],
            cwd=ROOT,
            check=True,
        )
        report = json.loads(report_json.read_text(encoding="utf-8"))
        assert report["kind"] == "olmblur_decision_matrix"
        assert report["decision"] == "preserve-normalized-ae-exact"
        assert report["normalized_8bpc"]["exact_count"] == 7
        assert report["windows_16bpc_reference"]["case_count"] == 7
        assert report["windows_16bpc_reference"]["status"] == "reference-covered-compare-pending"
        assert report["legacy_drift"]["classification"] == "normalized-software-exact-with-legacy-drift"
        assert report["legacy_drift"]["legacy_nonzero_count"] == 4
        assert report["cli_residuals"]["classification"] == "diagnostic-max1"
        assert report["cli_residuals"]["max_diff"] == 1
        assert report["runtime_trace"]["classification"] == "prewriteback-or-helper-state"
        md = report_md.read_text(encoding="utf-8")
        assert "OLMBlur Decision Matrix" in md
        assert "preserve-normalized-ae-exact" in md
        assert "7/7 exact" in md
        assert "Windows 16bpc reference" in md
        assert "case_0006" in md
        assert "185.49998474121094" in md or "0x1.72fffe0000000p+7" in md
    print("[OK] OLMBlur decision matrix smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
