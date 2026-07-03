#!/usr/bin/env python3
"""Consolidate the current narrow-proof state for OLMRadialBlur."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

TINY_COMPARE_JSON = ROOT / "refs/reports/runtime_trace_comparisons/olmradialblur_tiny_rotation_followup_20260701.json"
ZOOM_COMPARE_JSON = ROOT / "refs/reports/runtime_trace_comparisons/olmradialblur_caller_collapse_followup_20260701.json"
LANE_AUDIT_JSON = ROOT / "refs/conformance/olmradialblur_tiny_rotation_lane_audit_20260701.json"
PENDING_JSON = ROOT / "refs/reports/pending_runtime_trace_packages.json"
OUT_JSON = ROOT / "refs/conformance/olmradialblur_pending_narrow_proof_20260629.json"
OUT_MD = ROOT / "refs/conformance/olmradialblur_pending_narrow_proof_20260629.md"

ACTIVE_REQUEST_ID = "olmradialblur_tiny_rotation_anchor_context_watch_followup_20260702"
ZOOM_CONTEXT_REQUEST_ID = "olmradialblur_caller_collapse_followup_20260701"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tiny-compare-json", type=Path, default=TINY_COMPARE_JSON)
    parser.add_argument("--zoom-compare-json", type=Path, default=ZOOM_COMPARE_JSON)
    parser.add_argument("--lane-audit-json", type=Path, default=LANE_AUDIT_JSON)
    parser.add_argument("--pending-json", type=Path, default=PENDING_JSON)
    parser.add_argument("--output-json", type=Path, default=OUT_JSON)
    parser.add_argument("--output-md", type=Path, default=OUT_MD)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def pending_row(report: dict[str, Any], request_id: str) -> dict[str, Any]:
    for row in report["requests"]:
        if row.get("request_id") == request_id:
            return row
    raise KeyError(f"missing pending request {request_id}")


def residual_case(compare: dict[str, Any], case_id: str) -> dict[str, Any]:
    for row in compare["windows"]["cases"]:
        if row.get("case_id") == case_id:
            return row
    raise KeyError(f"missing case {case_id}")


def build_summary(args: argparse.Namespace) -> dict[str, Any]:
    tiny_followup = read_json(args.tiny_compare_json)
    zoom_followup = read_json(args.zoom_compare_json)
    lane = read_json(args.lane_audit_json)
    pending = read_json(args.pending_json)

    zoom = residual_case(zoom_followup, "case_0009")
    tiny = residual_case(tiny_followup, "case_0010")
    active = pending_row(pending, ACTIVE_REQUEST_ID)
    zoom_context = pending_row(pending, ZOOM_CONTEXT_REQUEST_ID)

    return {
        "kind": "olmradialblur_pending_narrow_proof",
        "date": "2026-07-01",
        "decision_boundary": (
            "Keep OLMRadialBlur on narrow binary-proof lanes only. Zoom is no longer the first Windows ask; "
            "it is a context lane whose sampled/pre-writeback floats already truncate to the exact stored "
            "Windows byte. The only active Windows runtime package now is tiny Rotation case_0010, which still "
            "needs the anchored pointer/watchpoint witness for typed upstream RGB / substitute-path / "
            "neighboring-contribution proof before final inverse sampling."
        ),
        "active_request": {
            "request_id": active["request_id"],
            "status": active["status"],
            "package": active["package"],
            "acceptance_note": active["acceptance_note"],
            "stop_condition": active["stop_condition"],
        },
        "context_requests": [
            {
                "request_id": zoom_context["request_id"],
                "status": zoom_context["status"],
                "latest_known_result_status": zoom_context["latest_known_result_status"],
                "latest_known_result_summary": zoom_context["latest_known_result_summary"],
            }
        ],
        "why_global_tuning_is_forbidden_now": [
            "Zoom already has sampled/pre-writeback floats that truncate to the exact stored Windows byte, so final byte packing is not the live issue there.",
            "tiny Rotation already rejects final-byte tuning, propagated-validity substitutes, same-row source support, and the current row-coupled surrogates.",
            "The missing bright lobe remains upstream of final inverse sampling: either neighboring-row/source-population ownership or an AEX substitute/fallback branch.",
        ],
        "lanes": [
            {
                "lane": "zoom_context",
                "status": "guarded-context-not-first-windows-ask",
                "case_id": zoom["case_id"],
                "witness": zoom["witness"],
                "windows_pre_writeback_rgba_float": zoom["aex_pre_writeback_rgba_float_or_hex"],
                "windows_final_rgba_u8": zoom["aex_final_rgba_u8"],
                "required_next_proof_if_reopened": (
                    "Caller-collapse alpha/sample accumulation between preserved validity `+0xf252`, accumulated "
                    "`+0xf250` RGBA, normalized final polar `+0xe`, and the final stored alpha."
                ),
            },
            {
                "lane": "tiny_rotation_active",
                "status": lane["decision"]["status"],
                "case_id": tiny["case_id"],
                "witness": tiny["witness"],
                "closest_traced_sampler_rgba_float": tiny["aex_source_or_polar_rgba_float"],
                "windows_final_rgba_u8": tiny["aex_final_rgba_u8"],
                "lane_audit": {
                    "same_row_direct_source_cells_all_black": lane["same_row_structure"]["direct_source_cells_all_black"],
                    "dominant_local_positive_cluster": lane["source_polar_structure"]["dominant_local_positive_cluster"],
                    "reference_bright_count": lane["row_coupling_probe"]["reference_bright_count"],
                    "all_variants_keep_bright_count_zero": lane["row_coupling_probe"]["all_variants_keep_bright_count_zero"],
                },
                "required_next_proof": (
                    "Exact source-population / neighboring-row ownership or substitute/fallback branch for case_0010 "
                    "witness `(1614,6)`, reached from the stable `+0x4eb9/+0x4ec8` anchor and including stack/pointer "
                    "or watchpoint context plus typed RGBA before and after that branch, preserved validity `+0xf252`, "
                    "accumulated `+0xf250`, normalized final polar `+0xe`, pre-writeback RGBA float, and final stored RGBA8."
                ),
            },
            {
                "lane": "inner_context",
                "status": "parked-typed-per-cell-witness-still-separate",
                "required_next_proof_if_reopened": (
                    "A typed FUN_180001c90 helper-to-output witness that survives beyond effective span into real "
                    "accumulation / denominator / writeback for one low-span and one quality-strong family."
                ),
            },
        ],
        "actionable_return_if": [
            "The return stays on case_0010 `(1614,6)` and isolates either the substitute/fallback branch or the exact neighboring/source-population chain that creates the missing bright lobe.",
            "It includes typed values, not only screenshots or a re-confirmed final white byte.",
            "It maps the decisive value back to a Mac-side ownership boundary before final inverse sampling.",
        ],
        "not_actionable_if": [
            "It only repeats the final white byte or the already-known near-black closest inverse-sampler return.",
            "It only says 'suspected substitute path' without the actual branch/value.",
            "It suggests global validity-alpha, span/wrap, or final-byte tuning without witness values that survive to writeback.",
        ],
        "recommended_next_windows_probe": [
            "Send only `olmradialblur_tiny_rotation_anchor_context_watch_followup_20260702` while it remains pending.",
            "If the Windows helper cannot hold the exact watchpoint path, return the exact failed pointer/watchpoint condition plus the closest typed values that still land on the target witness chain.",
            "Do not reopen Zoom first unless a later Mac code move specifically needs the denominator-side context.",
        ],
    }


def write_markdown(summary: dict[str, Any], out: Path) -> None:
    lines = [
        "# OLMRadialBlur Pending Narrow Proof",
        "",
        "## Decision Boundary",
        "",
        summary["decision_boundary"],
        "",
        "## Active Request",
        "",
        f"- Request: `{summary['active_request']['request_id']}`",
        f"- Status: `{summary['active_request']['status']}`",
        f"- Package: `{summary['active_request']['package']}`",
        f"- Acceptance note: `{summary['active_request']['acceptance_note']}`",
        f"- Stop condition: {summary['active_request']['stop_condition']}",
        "",
        "## Why Global Tuning Is Still Forbidden",
        "",
    ]
    for item in summary["why_global_tuning_is_forbidden_now"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Lanes", ""])
    for lane in summary["lanes"]:
        lines.append(f"### {lane['lane']}")
        lines.append("")
        lines.append(f"- Status: `{lane['status']}`")
        if "case_id" in lane:
            lines.append(f"- Case: `{lane['case_id']}`")
        if "witness" in lane:
            lines.append(f"- Witness: `{lane['witness']}`")
        if "windows_pre_writeback_rgba_float" in lane:
            lines.append(f"- Windows pre-writeback RGBA float: `{lane['windows_pre_writeback_rgba_float']}`")
        if "windows_final_rgba_u8" in lane:
            lines.append(f"- Windows final RGBA u8: `{lane['windows_final_rgba_u8']}`")
        if "closest_traced_sampler_rgba_float" in lane:
            lines.append(f"- Closest traced sampler RGBA float: `{lane['closest_traced_sampler_rgba_float']}`")
        if "lane_audit" in lane:
            lines.append(f"- Lane audit: `{lane['lane_audit']}`")
        if "required_next_proof" in lane:
            lines.append(f"- Required next proof: {lane['required_next_proof']}")
        if "required_next_proof_if_reopened" in lane:
            lines.append(f"- Required next proof if reopened: {lane['required_next_proof_if_reopened']}")
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
    args = parse_args()
    summary = build_summary(args)
    args.output_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_markdown(summary, args.output_md)
    print(args.output_json)
    print(args.output_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
