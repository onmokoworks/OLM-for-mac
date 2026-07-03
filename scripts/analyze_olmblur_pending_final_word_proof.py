#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} top-level JSON must be an object")
    return data


def latest_runtime_witnesses(runtime_summary: dict) -> dict:
    results = runtime_summary.get("results", [])
    if not isinstance(results, list) or not results:
        raise ValueError("runtime summary results missing")
    observations = results[0].get("observations", {})
    if not isinstance(observations, dict):
        raise ValueError("runtime summary observations missing")
    cases = observations.get("cases", [])
    if not isinstance(cases, list):
        raise ValueError("runtime summary cases missing")
    by_id = {str(case.get("case_id")): case for case in cases if isinstance(case, dict)}
    return {
        "case_0006": by_id.get("case_0006", {}),
        "case_0007": by_id.get("case_0007", {}),
    }


def build_summary(writer: dict, runtime_pkg: Path, runtime_summary: dict, runtime_summary_path: Path) -> dict:
    runtime_witness = latest_runtime_witnesses(runtime_summary)
    case6 = runtime_witness["case_0006"]
    case7 = runtime_witness["case_0007"]
    case6_px = ((case6.get("residual_pixels") or [{}])[0]) if isinstance(case6.get("residual_pixels"), list) else {}
    case7_px = ((case7.get("residual_pixels") or [{}])[0]) if isinstance(case7.get("residual_pixels"), list) else {}
    return {
        "kind": "olmblur_pending_final_word_proof",
        "date": "2026-06-29",
        "status": "historical-superseded-by-closeout-gate",
        "superseded_by": {
            "report": str(repo_root() / "refs" / "conformance" / "olmblur_closeout_gate_audit_20260701.md"),
            "reason": (
                "The remaining OLMBlur work is no longer one live final-word lane. "
                "case_0006 is now provenance/export-first, normalized 16bpc Legacy case_0007 "
                "is closed as a Windows pre-store float delta, and only old normalized 8bpc "
                "case_0007 remains reopenable."
            ),
        },
        "runtime_package_context": str(runtime_pkg),
        "latest_runtime_summary": str(runtime_summary_path),
        "decision_boundary": (
            "Decide whether the remaining OLMBlur residuals come from slightly different "
            "pre-store floats/helper ordering at the two sign-mixed non-Legacy witnesses, "
            "or from a true last-step writer rule mismatch that would justify changing the "
            "non-Legacy 16bpc writer."
        ),
        "current_live_request_gap": {
            "why_old_windows_case0006_trace_is_not_enough": (
                "The latest imported Windows case_0006 pre-writeback fact is still the older "
                "full-comp output-address witness at (498,940). It proves the non-Legacy lane "
                "already diverges before the final byte store, but it does not answer the current "
                "normalized 16bpc current-word witnesses at (314,14) and (29,71)."
            ),
            "old_windows_case0006_xy": [case6_px.get("x"), case6_px.get("y")],
            "current_live_request_xy": [[314, 14], [29, 71]],
            "practical_consequence": (
                "Treat the 2026-06-19 Windows trace as proof context only. The live "
                "`olmblur_case0006_helper_prestore_witness_20260630` package is still required "
                "because only those two current-word witnesses can decide whether the remaining "
                "sign-mixed family is already split in helper/pre-store state."
            ),
        },
        "why_global_swap_is_forbidden_now": writer["conclusion"],
        "witness_families": [
            {
                "family": "nonlegacy_sign_mixed_one_word",
                "case_id": "olmblur__case_0006",
                "latest_windows_runtime_note": {
                    "summary": case6.get("accumulation_order_notes"),
                    "windows_pre_writeback_rgb_hex": case6_px.get("aex_pre_writeback_rgb_hex"),
                    "windows_final_rgba": case6_px.get("aex_final_rgba"),
                    "current_mac_cli_pre_writeback_rgb_hex": case6_px.get("cli_pre_writeback_rgb_hex"),
                    "current_mac_cli_candidate_rgba": case6_px.get("mac_cli_candidate_rgba"),
                },
                "points": [
                    {
                        "xy": [314, 14],
                        "mac_raw": 1100.5,
                        "mac_stored_word": 1100,
                        "windows_png": 2201,
                        "mac_png": 2199,
                        "inference": "Windows would need internal word 1101 at this witness.",
                    },
                    {
                        "xy": [29, 71],
                        "mac_raw": 363.5,
                        "mac_stored_word": 364,
                        "windows_png": 725,
                        "mac_png": 727,
                        "inference": "Windows would need internal word 363 at this witness.",
                    },
                ],
                "meaning": "Sign-mixed one-word family; this already argues against a blind global rounding-direction swap.",
            },
            {
                "family": "legacy_last_pixel_half_step",
                "case_id": "olmblur__case_0007",
                "latest_windows_runtime_note": {
                    "summary": case7.get("accumulation_order_notes"),
                    "windows_writeback_family": "OLMBlur+0x7FDF",
                    "windows_first_halfstep_xy": [case7_px.get("x"), case7_px.get("y")],
                    "windows_pre_writeback_rgb_hex": case7_px.get("aex_pre_writeback_rgb_hex"),
                    "current_mac_cli_pre_writeback_rgb_hex": case7_px.get("cli_pre_writeback_rgb_hex"),
                },
                "points": [
                    {
                        "xy": [345, 672],
                        "mac_raw_blue": 12544.5,
                        "mac_stored_word_blue": 12545,
                        "windows_pre_store_blue": 12544.498046875,
                        "windows_internal_word_blue": 12544,
                        "windows_png_blue": 97,
                        "mac_png_blue": 98,
                        "inference": "Resolved as pre-store float delta before truncation, not an open writer-rule question.",
                    },
                    {
                        "xy": [488, 941],
                        "context": "old 8bpc normalized witness",
                        "mac_raw_red": 250.499985,
                        "windows_png_red": 251,
                        "mac_png_red": 250,
                        "inference": "This is already a pure half-step boundary split.",
                    },
                ],
                "meaning": "Legacy border/all-same structural blocker is retired; only a narrow half-step family remained, and the 16bpc witness is now directly grounded.",
            },
        ],
        "actionable_return_if": [
            "It records Windows pre-store float(s) at the two listed case_0006 witnesses, not only final PNG bytes.",
            "It records any helper/clamp value between add-half and final CVTTSS2SI/truncate on the non-Legacy path.",
            "It can distinguish 'same writer rule but smaller pre-store float' from 'different writer/helper rule'.",
        ],
        "not_actionable_if": [
            "It only reports final PNG values or final RGBA16 words.",
            "It revisits the retired old Legacy (0,0) spill or reopens the already-grounded 16bpc Legacy (345,672) witness instead of answering case_0006.",
            "It broadens back into generic blur-kernel tuning rather than the narrow writer/helper boundary.",
        ],
        "recommended_next_windows_probe": [
            "16bpc non-Legacy case_0006 at (314,14) and (29,71): capture the last helper/upstream value, pre-store float, and final internal word.",
            "Do not spend this package on the already-grounded 16bpc Legacy (345,672) point unless it is only being used as a debugger control sample.",
            "Only revisit old normalized 8bpc (488,941) if the same debugger setup can return it almost for free after answering the two case_0006 witnesses.",
        ],
    }


def write_markdown(summary: dict, out: Path) -> None:
    lines = [
        "# OLMBlur Pending Final-Word Proof",
        "",
        f"- Historical status: `{summary['status']}`",
        f"- Superseded by: `{summary['superseded_by']['report']}`",
        f"- Why superseded: {summary['superseded_by']['reason']}",
        "",
        f"- Runtime package context: `{summary['runtime_package_context']}`",
        f"- Latest runtime summary: `{summary['latest_runtime_summary']}`",
        "",
        "## Decision Boundary",
        "",
        summary["decision_boundary"],
        "",
        "## Why The Live Windows Request Still Matters",
        "",
        f"- {summary['current_live_request_gap']['why_old_windows_case0006_trace_is_not_enough']}",
        f"- Older imported Windows case_0006 witness: `{summary['current_live_request_gap']['old_windows_case0006_xy']}`",
        f"- Current live request witnesses: `{summary['current_live_request_gap']['current_live_request_xy']}`",
        f"- Practical consequence: {summary['current_live_request_gap']['practical_consequence']}",
        "",
        "## Why A Global Writer Swap Is Still Forbidden",
        "",
    ]
    lines.extend([
    ])
    for item in summary["why_global_swap_is_forbidden_now"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Witness Families", ""])
    for family in summary["witness_families"]:
        lines.append(f"### {family['case_id']}")
        lines.append("")
        lines.append(f"- Family: `{family['family']}`")
        lines.append(f"- Meaning: {family['meaning']}")
        latest = family.get("latest_windows_runtime_note")
        if latest:
            lines.append(f"- Latest Windows runtime note: `{latest}`")
        for point in family["points"]:
            lines.append(f"- Witness: `{point}`")
        lines.append("")
    lines.extend(["## Actionable Return Criteria", ""])
    for item in summary["actionable_return_if"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Not Actionable", ""])
    for item in summary["not_actionable_if"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Recommended Next Windows Probe", ""])
    for item in summary["recommended_next_windows_probe"]:
        lines.append(f"- {item}")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--writer-audit-json",
        type=Path,
        default=repo_root() / "refs" / "conformance" / "olmblur_16bpc_writer_contract_audit_20260629.json",
    )
    parser.add_argument(
        "--runtime-package",
        type=Path,
        default=repo_root() / "refs" / "runtime_trace_packages" / "olm_runtime_trace_olmblur_case0006_helper_prestore_witness_20260630.zip",
    )
    parser.add_argument(
        "--runtime-summary-json",
        type=Path,
        default=(
            repo_root()
            / "refs"
            / "reports"
            / "runtime_trace_bundle"
            / "olm_windows_action_bundle_20260629_232710_priority4_runtime_return_windows"
            / "runtime_trace_summary_olmblur_repeat_threshold_20260629_235638.json"
        ),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=repo_root() / "refs" / "conformance" / "olmblur_pending_final_word_proof_20260629.json",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=repo_root() / "refs" / "conformance" / "olmblur_pending_final_word_proof_20260629.md",
    )
    args = parser.parse_args()

    summary = build_summary(
        load_json(args.writer_audit_json),
        args.runtime_package,
        load_json(args.runtime_summary_json),
        args.runtime_summary_json,
    )
    args.output_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(summary, args.output_md)
    print(args.output_json)
    print(args.output_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
