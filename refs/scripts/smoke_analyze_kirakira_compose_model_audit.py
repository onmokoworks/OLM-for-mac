#!/usr/bin/env python3
"""Smoke-test the generated OLMKiraKira compose model audit report."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORT_JSON = (
    ROOT
    / "refs"
    / "reports"
    / "olmkirakira_compose_model_audit_20260625"
    / "compose_model_audit.json"
)
REPORT_MD = REPORT_JSON.with_suffix(".md")


def main() -> int:
    report = json.loads(REPORT_JSON.read_text(encoding="utf-8"))
    assert report["kind"] == "olmkirakira_compose_model_audit"
    assert report["decision"]["status"] == "preserve-current-compose-model"
    assert report["decision"]["best_by_mean"] == "current_gain_0_62"
    assert report["decision"]["best_by_max"] == "current_gain_0_62"
    assert len(report["case_ids"]) == 9
    assert len(report["variants"]) == 6

    variants = {row["id"]: row for row in report["variants"]}
    baseline = variants["current_gain_0_62"]
    assert baseline["total"]["case_count"] == 9
    assert baseline["total"]["exact_count"] == 1
    assert baseline["total"]["max_diff"] == 66
    assert baseline["groups"]["strength0_anchor"]["max_diff"] == 3

    scale_override = variants["scale_override_1_0"]
    assert scale_override["total"]["exact_count"] == 0
    assert scale_override["groups"]["strength0_anchor"]["max_diff"] >= 100

    premul = variants["premul_gain_0_62"]
    assert premul["total"]["exact_count"] == 0
    assert premul["total"]["mean_sum"] > baseline["total"]["mean_sum"]

    md = REPORT_MD.read_text(encoding="utf-8")
    assert "OLMKiraKira Compose Model Audit" in md
    assert "preserve-current-compose-model" in md
    assert "current_gain_0_62" in md
    print("[OK] KiraKira compose model audit smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
