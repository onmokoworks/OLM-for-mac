#!/usr/bin/env python3
"""Smoke-test the OLMKiraKira decision matrix report."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olmkirakira_decision_") as tmp:
        out_dir = Path(tmp)
        report_json = out_dir / "decision_matrix.json"
        report_md = out_dir / "decision_matrix.md"
        subprocess.run(
            [
                "python3",
                str(ROOT / "scripts" / "analyze_kirakira_decision_matrix.py"),
                "--output-json",
                str(report_json),
                "--output-md",
                str(report_md),
            ],
            cwd=ROOT,
            check=True,
        )
        report = json.loads(report_json.read_text(encoding="utf-8"))
        assert report["kind"] == "olmkirakira_decision_matrix"
        assert report["decision"] == "blocked-compose-or-final-quantization"
        assert report["classification"] == "ray-helper-and-fd90-grounded"
        assert report["ray_helper"]["decision"] == "grounded-within-float-print-precision"
        assert report["aggregation"]["decision"] == "fd90-grounded-compose-unisolated"
        assert report["compose_model_audit"]["decision"] == "preserve-current-compose-model"
        assert report["compose_model_audit"]["best_by_mean"] == "current_gain_0_62"
        assert report["compose_model_audit"]["best_by_max"] == "current_gain_0_62"
        assert report["bt709_remeasure"]["groups"]["strength100_single_ray"]["max_diff_max"] == 23
        assert report["bt709_remeasure"]["groups"]["rotation13"]["max_diff_max"] == 66
        assert len(report["aggregation"]["samples"]) == 3
        md = report_md.read_text(encoding="utf-8")
        assert "OLMKiraKira Decision Matrix" in md
        assert "blocked-compose-or-final-quantization" in md
        assert "fd90-grounded-compose-unisolated" in md
        assert "preserve-current-compose-model" in md
    print("[OK] KiraKira decision matrix smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
