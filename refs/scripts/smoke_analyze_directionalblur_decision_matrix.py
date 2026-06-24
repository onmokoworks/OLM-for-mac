#!/usr/bin/env python3
"""Smoke-test the OLMDirectionalBlur decision matrix report."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olmdirectionalblur_decision_") as tmp:
        out_dir = Path(tmp)
        report_json = out_dir / "decision_matrix.json"
        report_md = out_dir / "decision_matrix.md"
        subprocess.run(
            [
                "python3",
                str(ROOT / "scripts" / "analyze_directionalblur_decision_matrix.py"),
                "--output-json",
                str(report_json),
                "--output-md",
                str(report_md),
            ],
            cwd=ROOT,
            check=True,
        )
        report = json.loads(report_json.read_text(encoding="utf-8"))
        assert report["kind"] == "olmdirectionalblur_decision_matrix"
        assert report["decision"] == "blocked-await-runtime-or-asm-proof"
        assert report["candidate_matrix"]["best_overall"]["candidate"] == "rotated-front-strength"
        assert report["candidate_matrix"]["best_aex_shaped"]["candidate"] == "rotated-aex-trunc-output"
        assert report["candidate_matrix"]["exact_candidates"] == []
        assert report["residuals"]["classification"] == "split-angle0-vs-diagonal"
        assert report["runtime_trace"]["classification"] == "not-actionable"
        md = report_md.read_text(encoding="utf-8")
        assert "OLMDirectionalBlur Decision Matrix" in md
        assert "blocked-await-runtime-or-asm-proof" in md
        assert "angle0-rgb-only-rowdriver-or-valid-alpha" in md
        assert "diagonal-rgb-alpha-rotate-validity" in md
    print("[OK] DirectionalBlur decision matrix smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
