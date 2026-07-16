from __future__ import annotations

import json
from pathlib import Path

from probe_olmcolorkey_replace_edge_orchestration_callback_20260716 import run

ROOT = Path(__file__).resolve().parents[2]


def test_callback_followup_reaches_next_stage_and_records_contract() -> None:
    report = run(ROOT / "aex/OLMColorKey/Plugins/64/2025/OLMColorKey.aex")
    assert report["status"] == "pass"
    assert report["stage_order"] == ["replacement_write", "thin_boundary", "blur_boundary", "blur_apply"]
    assert not report.get("error")
    assert report["callback_contract"] == "callback(refcon, output_world, params, 0, 0) -> PF_Err"
    assert report["output_matches_source"]
    assert report["cleanup_observed"]
    assert len(report["callback_events"]) >= 2


def test_report_is_hash_pinned_and_fail_closed() -> None:
    path = ROOT / "refs/conformance/olmcolorkey_replace_edge_orchestration_callback_20260716.json"
    report = json.loads(path.read_text(encoding="utf-8"))
    assert report["binary_sha256"] == report["expected_sha256"]
    assert report["status"] == "pass"


if __name__ == "__main__":
    # Keep direct Python smoke executable even without pytest discovery.
    test_callback_followup_reaches_next_stage_and_records_contract()
    test_report_is_hash_pinned_and_fail_closed()
    print("PASS: ColorKey Replace+Edge orchestration callback and report gates")
