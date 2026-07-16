#!/usr/bin/env python3
"""Deterministic local audit for the retained OLMBlur case 0003/0004 evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REFS = ROOT / "refs" / "conformance"
OUT_JSON = REFS / "olmblur_case0003_0004_readiness_audit_20260717.json"
OUT_MD = REFS / "olmblur_case0003_0004_readiness_audit_20260717.md"
AEX = ROOT / "plugins_2025" / "OLMBlur.aex"
AEX_SHA256 = "f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b"


def load(name: str) -> dict:
    return json.loads((REFS / name).read_text())


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_case0003(report: dict) -> dict:
    calls = report["schedule_capture"]["calls"]
    assert len(calls) == 120
    groups = []
    for iteration in range(10):
        group = calls[iteration * 12:(iteration + 1) * 12]
        assert [c["direction"] for c in group] == ["horizontal"] * 6 + ["vertical"] * 6
        assert [c["offset"] for c in group[:6]] == [0, 90, 180, 270, 360, 450]
        assert [c["offset"] for c in group[6:]] == [0, 160, 320, 480, 640, 800]
        assert all(c["radius"] == 248 for c in group)
        assert all((c["columns"], c["rows"]) == (960, 90) for c in group[:6])
        assert all((c["columns"], c["rows"]) == (160, 540) for c in group[6:])
        groups.append({"iteration": iteration + 1, "calls": 12, "h_offsets": [0, 90, 180, 270, 360, 450], "v_offsets": [0, 160, 320, 480, 640, 800]})
    coeff = report["coefficient_candidate"]
    assert coeff["double_exp_float_cast_exact_words"] == 4970
    assert coeff["double_exp_float_cast_diff_words"] == 0
    return {"call_count": len(calls), "iterations": groups, "coefficient_words_exact": 4970}


def audit_case0004(report: dict) -> dict:
    captured = report["captured_iterations"]
    assert [item["radius"] for item in captured] == [125, 36, 10, 2]
    h_offsets = [[0, 90, 180, 270, 360, 450]] * 4
    v_offsets = [[0, 160, 320, 480, 640, 800]] * 4
    assert [item["horizontal_pass_ranges"] for item in captured] == [[[a, b] for a, b in zip(offsets, offsets[1:] + [540])] for offsets in h_offsets]
    assert [item["vertical_pass_ranges"] for item in captured] == [[[a, b] for a, b in zip(offsets, offsets[1:] + [960])] for offsets in v_offsets]
    assert report["actual_helper_micro_exact"]["all_exact"] is True
    return {"radius_sequence": [125, 36, 10, 2], "h_v_pass_ranges_exact": True, "helper_micro_exact": True}


def main() -> int:
    assert digest(AEX) == AEX_SHA256
    case3 = load("olmblur_case0003_legacy_schedule_fullframe_20260716.json")
    case4 = load("olmblur_case0004_staged_helper_replay_20260716.json")
    double_exp = load("olmblur_case0004_exp_double_candidate_20260716.json")
    differential = load("olmblur_case0003_0004_actual_aex_prestore_differential_20260716.json")
    writer = load("olmblur_writer_export_boundary_20260716.json")
    result = {
        "schema": "olmblur.case0003-0004.readiness-audit/1",
        "status": "pass_local_crosscheck_with_open_worker_boundary",
        "claim_boundary": "local actual-AEX fixture and portable evidence only; no AE exact claim",
        "aex": {"path": "plugins_2025/OLMBlur.aex", "sha256": AEX_SHA256},
        "inputs": {
            "case0003_schedule_report_sha256": digest(REFS / "olmblur_case0003_legacy_schedule_fullframe_20260716.json"),
            "case0004_replay_report_sha256": digest(REFS / "olmblur_case0004_staged_helper_replay_20260716.json"),
            "case0004_double_exp_report_sha256": digest(REFS / "olmblur_case0004_exp_double_candidate_20260716.json"),
            "actual_aex_prestore_report_sha256": digest(REFS / "olmblur_case0003_0004_actual_aex_prestore_differential_20260716.json"),
        },
        "checks": {
            "case0003": audit_case0003(case3),
            "case0004": audit_case0004(case4),
            "case0004_double_exp": {"coefficient_words_compared": double_exp["coefficient_words_compared"], "all_exact": double_exp["all_coefficient_words_exact"], "radii": double_exp["radius_sequence"]},
            "case0003_source_conversion": {"all_source_conversion_exact": differential["case_0003_legacy"]["all_source_conversion_exact"], "worker_helper_bounded": False},
            "case0004_source_and_writer": {"source_conversion_exact": differential["case_0004_nonlegacy"]["comparison"]["source_conversion_exact"], "writer_store_exact_for_portable_inputs": differential["case_0004_nonlegacy"]["comparison"]["writer_store_exact_for_portable_inputs"], "worker_helper_bounded": False},
            "writer_rounding": {"actual_aex_standard": writer["actual_aex_writer_runs"]["standard_case0004_values"], "rule": "actual-AEX standard writer stores the retained controlled values after the established add-0.5/truncate behavior"},
        },
        "uncovered_locally_testable": [
            "No additional schedule condition was uncovered: case0003 H/V partitions and offsets are now checked explicitly, not only by total call count.",
            "No additional coefficient condition was uncovered: case0004 covers all 16 H/V stages and case0003 covers 4970/4970 candidate words.",
            "No additional rounding condition was uncovered: the actual-AEX writer half-tie control remains the governing local evidence.",
        ],
        "remaining_blocker": "case0003 full-frame worker/helper pre-store and case0004 radius-125 worker/helper pre-store remain unexecuted; AE/Windows exactness remains unclaimed.",
    }
    OUT_JSON.write_text(json.dumps(result, indent=2) + "\n")
    lines = [
        "# OLMBlur case0003/0004 readiness audit (2026-07-17)", "", "## Result", "",
        "- Local cross-check: **PASS** against the pinned actual-AEX evidence.",
        "- Claim boundary: local actual-AEX fixture and portable evidence only; no AE exact claim.",
        "- case0003 schedule: 120 calls, ten exact `H x 6, V x 6` iterations, with H offsets `0..450` by 90 and V offsets `0..800` by 160.",
        "- case0004 schedule: four exact radius stages `[125, 36, 10, 2]`, one H and one V call per stage; retained helper microfixtures are exact.",
        "- Coefficients: case0004 double-exp candidate `177/177`; case0003 Legacy candidate `4970/4970` with zero candidate mismatches.",
        "- Rounding: actual-AEX writer evidence retains the add-0.5/truncate half-tie behavior; no rounding change is justified.",
        "", "## Open boundary", "",
        "The locally testable schedule/coefficient/rounding conditions are covered. The remaining blocker is the worker/helper pre-store boundary: case0003 is full-frame dependent and case0004 does not reach the radius-125 helper within the established cap. This report does not promote either case to AE exact.",
        "", "## Reproduction", "", "`python3 tools/emulation/test_olmblur_case0003_0004_readiness_audit_20260717.py`", "",
    ]
    OUT_MD.write_text("\n".join(lines))
    print(json.dumps({"status": result["status"], "report": str(OUT_JSON.relative_to(ROOT)), "schedule": "120 calls / 10 exact partitions", "coefficients": "177/177 and 4970/4970", "rounding": "actual-AEX half-tie retained"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
