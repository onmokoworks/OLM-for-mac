#!/usr/bin/env python3
"""Freeze the current source-site decision ladder for DistanceGradation case_0023."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE_CPP = ROOT / "mac/OLMDistanceGradation/OLMDistanceGradation.cpp"
THRESHOLD_AUDIT_JSON = ROOT / "refs/conformance/olmdistancegradation_case0023_threshold_family_audit_20260701.json"
PROVENANCE_JSON = ROOT / "refs/conformance/olmdistancegradation_case0023_reference_provenance_20260702.json"
BGOFF_PROBE_JSON = ROOT / "refs/conformance/olmdistancegradation_case0023_bgoff_current_probe_20260702.json"
OUT_JSON = ROOT / "refs/conformance/olmdistancegradation_case0023_source_candidates_audit_20260701.json"
OUT_MD = ROOT / "refs/conformance/olmdistancegradation_case0023_source_candidates_audit_20260701.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-cpp", type=Path, default=SOURCE_CPP)
    parser.add_argument("--threshold-audit-json", type=Path, default=THRESHOLD_AUDIT_JSON)
    parser.add_argument("--provenance-json", type=Path, default=PROVENANCE_JSON)
    parser.add_argument("--bgoff-probe-json", type=Path, default=BGOFF_PROBE_JSON)
    parser.add_argument("--output-json", type=Path, default=OUT_JSON)
    parser.add_argument("--output-md", type=Path, default=OUT_MD)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def find_line(lines: list[str], needle: str) -> int:
    for idx, line in enumerate(lines, start=1):
        if needle in line:
            return idx
    raise KeyError(f"missing source needle: {needle}")


def build_edge_candidate_sites(lines: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "rank": 1,
            "family": "edge",
            "site": "build_distance_field_both_ownership",
            "function": "build_distance_field",
            "line": find_line(lines, "df.x[i] = std::max(inside[i], outside[i]);"),
            "why_still_live": (
                "The surviving bg_off mismatch at (1699,7) keeps the case_0023 lane upstream of the final "
                "background blend. Neighboring edge witnesses already match, so the remaining live suspicion "
                "is the Both-mode ownership handoff for a narrow subset of pixels."
            ),
            "allowed_change_shape": "Both-mode ownership only; no broad field rewrite",
        },
        {
            "rank": 2,
            "family": "edge",
            "site": "dt_to_normalized_constant_threshold",
            "function": "dt_to_normalized",
            "line": find_line(lines, "out[i] = (out[i] > t) ? 1.0f : 0.0f;"),
            "why_still_live": (
                "The edge-family mismatch still lives in Constant mode with Outside Threshold=0, so the "
                "binary threshold helper stays relevant if Windows current export later says the decisive "
                "edge pixel is already wrong before the Both-mode ownership merge."
            ),
            "allowed_change_shape": "helper-stage threshold ownership / plateau membership only",
        },
        {
            "rank": 2,
            "rank": 3,
            "family": "edge",
            "site": "compose_pixel_constant_endpoint",
            "function": "compose_pixel",
            "line": find_line(lines, "X = (X > 0.0f) ? 1.0f : 0.0f;"),
            "why_still_live": (
                "This remains second-order only. Reopen it only if a current Windows export or typed witness "
                "shows compose input already matches Mac while the endpoint still differs at the live edge pixel."
            ),
            "allowed_change_shape": "only with explicit Windows contradiction to current field-first reading",
        },
    ]


def build_threshold_candidate_sites(lines: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "rank": 1,
            "family": "threshold",
            "site": "current_aex_export_provenance_gate",
            "function": "reference/export lane",
            "line": 0,
            "why_still_live": (
                "The latest live Mac AE rerun already matches the latest Windows typed triplet at "
                "(415,393), while the packaged expected PNG stays stale there. This family must stay in "
                "provenance/export classification until a same-run current Windows export lands."
            ),
            "allowed_change_shape": "no source patch until current export provenance is resolved",
        },
        {
            "rank": 2,
            "family": "threshold",
            "site": "dt_to_normalized_constant_threshold",
            "function": "dt_to_normalized",
            "line": find_line(lines, "out[i] = (out[i] > t) ? 1.0f : 0.0f;"),
            "why_still_live": (
                "Keep this as the first implementation reopen site only if a current Windows export or a "
                "future typed witness contradicts the current provenance split and says the threshold family "
                "is still a true output mismatch."
            ),
            "allowed_change_shape": "threshold-family reopen only after provenance contradiction",
        },
        {
            "rank": 3,
            "family": "threshold",
            "site": "compose_pixel_constant_endpoint",
            "function": "compose_pixel",
            "line": find_line(lines, "X = (X > 0.0f) ? 1.0f : 0.0f;"),
            "why_still_live": (
                "This remains second-order even for the threshold family. Reopen it only if both current "
                "export provenance and helper-stage ownership are cleared first."
            ),
            "allowed_change_shape": "only after threshold-family provenance is cleared",
        },
    ]


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    threshold_audit = read_json(args.threshold_audit_json)
    provenance = read_json(args.provenance_json)
    bgoff_probe = read_json(args.bgoff_probe_json)
    lines = args.source_cpp.read_text(encoding="utf-8").splitlines()
    edge_sites = build_edge_candidate_sites(lines)
    threshold_sites = build_threshold_candidate_sites(lines)

    report = {
        "kind": "olmdistancegradation_case0023_source_candidates_audit",
        "schema": 1,
        "case_id": threshold_audit["case_id"],
        "source_cpp": str(args.source_cpp.relative_to(ROOT)),
        "residual_summary": {
            "total_px": threshold_audit["residual"]["total_px"],
            "edge_bucket_count": threshold_audit["residual"]["edge_bucket"]["count"],
            "threshold_bucket_count": threshold_audit["residual"]["threshold_bucket"]["count"],
            "threshold_crossing": [
                row
                for row in threshold_audit["threshold_triplet_roles"]
                if row["role"] in {
                    "below_threshold_same_row",
                    "first_above_threshold_same_row",
                    "deeper_plateau_same_row",
                }
            ],
        },
        "family_status": {
            "threshold_family": {
                "status": provenance["status"],
                "summary": provenance["decision"]["summary"],
                "next_action": provenance["next_action"],
            },
            "edge_family": {
                "status": bgoff_probe["status"],
                "summary": bgoff_probe["decision"]["summary"],
                "important_split": bgoff_probe["decision"]["important_split"],
            },
        },
        "source_candidates": edge_sites + threshold_sites,
        "edge_family_candidates": edge_sites,
        "threshold_family_candidates": threshold_sites,
        "decision_ladder": [
            {
                "step": 1,
                "condition": "If the question is about the threshold-family triplet, resolve current-AEX export provenance first",
                "action": "Do not patch source until the current Windows export says the family is still a true mismatch",
            },
            {
                "step": 2,
                "condition": "If the question is about the surviving edge-family pixel and Windows says field/ownership is already wrong before compose",
                "action": "Constrain changes to build_distance_field() and dt_to_normalized()",
            },
            {
                "step": 3,
                "condition": "If Windows says compose input already matches Mac but the endpoint still differs",
                "action": "Only then reopen compose_pixel()",
            },
        ],
        "forbidden_actions": [
            "Do not promote a global Constant plateau rewrite from the rejected trunc_plateau_binary family.",
            "Do not retune generic 16bpc writeback from this lane.",
            "Do not reopen broad color-mix tuning while the field-first witness still stands.",
            "Do not treat the packaged expected PNG as equivalent to current Windows output for the threshold-family slice without proof.",
        ],
        "pending_windows_followup": threshold_audit["pending_windows_followup"],
        "windows_requirement": threshold_audit["decision"]["next_windows_requirement"],
        "provenance_reference_request": {
            "request_id": "olmdistancegradation_case0023_current_aex_recapture_20260702",
            "request_json": "refs/reference_requests/olmdistancegradation_case0023_current_aex_recapture_20260702.json",
            "contract": "refs/conformance/olmdistancegradation_case0023_current_aex_export_contract_20260702.md",
        },
    }
    return report


def render_md(report: dict[str, Any]) -> str:
    lines = [
        "# OLMDistanceGradation case_0023 Source-Candidates Audit",
        "",
        f"- Case: `{report['case_id']}`",
        f"- Source: `{report['source_cpp']}`",
        f"- Residual px: `{report['residual_summary']['total_px']}`",
        f"- Edge bucket px: `{report['residual_summary']['edge_bucket_count']}`",
        f"- Threshold bucket px: `{report['residual_summary']['threshold_bucket_count']}`",
        "",
        "## Family Status",
        "",
        f"- Threshold family: `{report['family_status']['threshold_family']['status']}`",
        f"  - {report['family_status']['threshold_family']['summary']}",
        f"  - Next action: {report['family_status']['threshold_family']['next_action']}",
        f"- Edge family: `{report['family_status']['edge_family']['status']}`",
        f"  - {report['family_status']['edge_family']['summary']}",
        f"  - Split: {report['family_status']['edge_family']['important_split']}",
        "",
        "## Threshold Crossing Witness",
        "",
        "| Role | XY | field_x | raw_inside |",
        "| --- | --- | ---: | ---: |",
    ]
    for row in report["residual_summary"]["threshold_crossing"]:
        lines.append(
            f"| `{row['role']}` | `({row['x']},{row['y']})` | `{row['field_x']}` | `{row['raw_inside']}` |"
        )

    lines.extend(
        [
            "",
            "## Edge-Family Source Candidates",
            "",
            "| Rank | Site | Function | Line | Why live | Allowed change shape |",
            "| --- | --- | --- | ---: | --- | --- |",
        ]
    )
    for row in report["edge_family_candidates"]:
        lines.append(
            f"| {row['rank']} | `{row['site']}` | `{row['function']}` | `{row['line']}` | {row['why_still_live']} | {row['allowed_change_shape']} |"
        )

    lines.extend(
        [
            "",
            "## Threshold-Family Reopen Order",
            "",
            "| Rank | Site | Function | Line | Why live | Allowed change shape |",
            "| --- | --- | --- | ---: | --- | --- |",
        ]
    )
    for row in report["threshold_family_candidates"]:
        lines.append(
            f"| {row['rank']} | `{row['site']}` | `{row['function']}` | `{row['line']}` | {row['why_still_live']} | {row['allowed_change_shape']} |"
        )

    lines.extend(
        [
            "",
            "## Decision Ladder",
            "",
        ]
    )
    for row in report["decision_ladder"]:
        lines.append(f"{row['step']}. {row['condition']} -> {row['action']}")

    lines.extend(
        [
            "",
            "## Forbidden Actions",
            "",
        ]
    )
    for row in report["forbidden_actions"]:
        lines.append(f"- {row}")

    pending = report["pending_windows_followup"]
    lines.extend(
        [
            "",
            "## Active Runtime Follow-up",
            "",
            f"- Request: `{pending['request_id']}`",
            f"- Status: `{pending['status']}`",
            f"- Package: `{pending['package']}`",
            f"- Acceptance: `{pending['acceptance_note']}`",
            f"- Requirement: {report['windows_requirement']}",
            "",
            "## Provenance Export Follow-up",
            "",
            f"- Request: `{report['provenance_reference_request']['request_id']}`",
            f"- JSON: `{report['provenance_reference_request']['request_json']}`",
            f"- Contract: `{report['provenance_reference_request']['contract']}`",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    report = build_report(args)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_md.write_text(render_md(report), encoding="utf-8")
    print(f"[ok] wrote {args.output_json}")
    print(f"[ok] wrote {args.output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
