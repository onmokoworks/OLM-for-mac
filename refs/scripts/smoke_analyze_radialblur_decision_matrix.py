#!/usr/bin/env python3
"""Smoke-test the OLMRadialBlur decision matrix report."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olmradialblur_decision_") as tmp:
        out_dir = Path(tmp)
        report_json = out_dir / "decision_matrix.json"
        report_md = out_dir / "decision_matrix.md"
        subprocess.run(
            [
                "python3",
                str(ROOT / "scripts" / "analyze_radialblur_decision_matrix.py"),
                "--output-json",
                str(report_json),
                "--output-md",
                str(report_md),
            ],
            cwd=ROOT,
            check=True,
        )
        report = json.loads(report_json.read_text(encoding="utf-8"))
        assert report["kind"] == "olmradialblur_decision_matrix"
        assert report["decision"] == "blocked-needs-narrow-proof"
        assert report["zoom"]["decision"] == "guarded-alpha-normalization"
        assert report["zoom"]["local_floor_minus_windows_u8"] == [0, 0, 0, 1]
        assert report["tiny_rotation"]["decision"] == "blocked-sampler-validity"
        assert report["inner"]["decision"] == "blocked-no-global-toggle"
        assert report["inner"]["best_by_mean_sum"] == "loop-minus-one"
        assert report["inner"]["all_exact_candidates"] == []
        witness_plan = report["inner"]["witness_plan"]
        assert witness_plan["decision"] == "typed-inner-cell-witnesses-only"
        representatives = {
            row["family"]: row["case_id"]
            for row in witness_plan["representatives"]
        }
        assert representatives == {
            "low-span": "rb_inner_only_strength_large",
            "quality-strong": "rb_inner_quality_1",
            "edge-prepass": "rb_inner_edgefade_only",
        }
        cell_witness = report["inner"]["cell_witness"]
        assert cell_witness["status"] == "answered_partial"
        spans = {
            row["case_id"]: row["effective_span_r14d"]
            for row in cell_witness["cases"]
        }
        assert spans == {
            "rb_inner_only_strength_large": 477,
            "rb_inner_quality_1": 51,
            "rb_inner_edgefade_only": 255,
        }
        assert cell_witness["failure_classification"] == "partial_trace_after_effective_span"
        md = report_md.read_text(encoding="utf-8")
        assert "OLMRadialBlur Decision Matrix" in md
        assert "guarded-alpha-normalization" in md
        assert "blocked-sampler-validity" in md
        assert "blocked-no-global-toggle" in md
        assert "Inner Witness Plan" in md
        assert "Inner Cell Witness Return" in md
        assert "rb_inner_only_strength_large" in md
        assert "rb_inner_quality_1" in md
        assert "rb_inner_edgefade_only" in md
    print("[OK] RadialBlur decision matrix smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
