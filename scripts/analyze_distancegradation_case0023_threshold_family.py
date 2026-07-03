#!/usr/bin/env python3
"""Consolidate the current OLMDistanceGradation case_0023 threshold-family lane."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

SPLIT_JSON = ROOT / "refs/conformance/olmdistancegradation_16bpc_case0023_residual_split_20260630.json"
POINTDEBUG_JSON = ROOT / "refs/conformance/olmdistancegradation_16bpc_case0023_pointdebug_20260630.json"
PLATEAU_JSON = ROOT / "refs/conformance/olmdistancegradation_16bpc_case0023_plateau_transition_20260701.json"
PENDING_JSON = ROOT / "refs/reports/pending_runtime_trace_packages.json"
OUT_JSON = ROOT / "refs/conformance/olmdistancegradation_case0023_threshold_family_audit_20260701.json"
OUT_MD = ROOT / "refs/conformance/olmdistancegradation_case0023_threshold_family_audit_20260701.md"
REQUEST_ID = "olmdistancegradation_case0023_refcon_stack_wordmap_followup_20260702"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split-json", type=Path, default=SPLIT_JSON)
    parser.add_argument("--pointdebug-json", type=Path, default=POINTDEBUG_JSON)
    parser.add_argument("--plateau-json", type=Path, default=PLATEAU_JSON)
    parser.add_argument("--pending-json", type=Path, default=PENDING_JSON)
    parser.add_argument("--output-json", type=Path, default=OUT_JSON)
    parser.add_argument("--output-md", type=Path, default=OUT_MD)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def pick_threshold_bucket(split: dict[str, Any]) -> dict[str, Any]:
    buckets = split["inside_distance_buckets"]
    match = min(buckets, key=lambda row: abs(float(row["inside_distance"]) - 36.013885))
    return match


def pending_row(report: dict[str, Any]) -> dict[str, Any]:
    for row in report["requests"]:
        if row.get("request_id") == REQUEST_ID:
            return row
    raise KeyError(f"missing pending request {REQUEST_ID}")


def point_by_xy(points: list[dict[str, Any]], x: int, y: int) -> dict[str, Any]:
    for row in points:
        if int(row["x"]) == x and int(row["y"]) == y:
            return row
    raise KeyError(f"missing point ({x},{y})")


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    split = read_json(args.split_json)
    pointdebug = read_json(args.pointdebug_json)
    plateau = read_json(args.plateau_json)
    pending = pending_row(read_json(args.pending_json))

    edge_bucket = min(split["inside_distance_buckets"], key=lambda row: abs(float(row["inside_distance"]) - 1.0))
    threshold_bucket = pick_threshold_bucket(split)
    plateau_rows = plateau["bucket_transition"]
    plateau_edge = min(plateau_rows, key=lambda row: abs(float(row["inside_distance"]) - 1.0))
    plateau_threshold = min(plateau_rows, key=lambda row: abs(float(row["inside_distance"]) - 36.013885))
    triplet_points = pointdebug["bucket_b_inside_36_points"]
    threshold_value = 36.0
    threshold_triplet = [
        {
            "role": "below_threshold_same_row",
            **point_by_xy(triplet_points, 414, 393),
            "inside_minus_threshold": round(float(point_by_xy(triplet_points, 414, 393)["raw_inside"]) - threshold_value, 7),
        },
        {
            "role": "first_above_threshold_same_row",
            **point_by_xy(triplet_points, 415, 393),
            "inside_minus_threshold": round(float(point_by_xy(triplet_points, 415, 393)["raw_inside"]) - threshold_value, 7),
        },
        {
            "role": "deeper_plateau_same_row",
            **point_by_xy(triplet_points, 416, 393),
            "inside_minus_threshold": round(float(point_by_xy(triplet_points, 416, 393)["raw_inside"]) - threshold_value, 7),
        },
        {
            "role": "vertical_contrast_above",
            **point_by_xy(triplet_points, 415, 392),
            "inside_minus_threshold": round(float(point_by_xy(triplet_points, 415, 392)["raw_inside"]) - threshold_value, 7),
        },
        {
            "role": "vertical_contrast_below",
            **point_by_xy(triplet_points, 415, 394),
            "inside_minus_threshold": round(float(point_by_xy(triplet_points, 415, 394)["raw_inside"]) - threshold_value, 7),
        },
    ]

    report = {
        "kind": "olmdistancegradation_case0023_threshold_family_audit",
        "schema": 1,
        "case_id": "olmdistancegradation_extended__case_0023",
        "mode": {
            "interpolation": "Constant",
            "in_out": "Both",
            "outside_threshold": 0,
        },
        "residual": {
            "total_px": int(split["residual_px"]),
            "endpoint_pairs": split["candidate_to_reference_endpoint_pairs"],
            "edge_bucket": {
                "inside_distance": edge_bucket["inside_distance"],
                "count": edge_bucket["count"],
                "outside_distance_values": edge_bucket["outside_distance_values"],
                "candidate_rgba_counts": edge_bucket["candidate_rgba_counts"],
                "reference_rgba_counts": edge_bucket["reference_rgba_counts"],
            },
            "threshold_bucket": {
                "inside_distance": threshold_bucket["inside_distance"],
                "count": threshold_bucket["count"],
                "outside_distance_values": threshold_bucket["outside_distance_values"],
                "candidate_rgba_counts": threshold_bucket["candidate_rgba_counts"],
                "reference_rgba_counts": threshold_bucket["reference_rgba_counts"],
            },
        },
        "threshold_triplet_roles": threshold_triplet,
        "live_mac_triplet": triplet_points,
        "live_mac_edge_family": pointdebug["bucket_a_inside_1_points"],
        "plateau_probe": {
            "current_residual_px": 73,
            "plateau_residual_px": int(sum(int(row["plateau_count"]) for row in plateau_rows)),
            "edge_bucket_delta": int(plateau_edge["delta_count"]),
            "threshold_bucket_current_count": int(plateau_threshold["current_count"]),
            "threshold_bucket_plateau_count": int(plateau_threshold["plateau_count"]),
            "threshold_bucket_delta": int(plateau_threshold["delta_count"]),
            "threshold_bucket_invariant_under_plateau_probe": int(plateau_threshold["delta_count"]) == 0,
        },
        "pending_windows_followup": {
            "request_id": pending["request_id"],
            "status": pending["status"],
            "package": pending["package"],
            "acceptance_note": pending["acceptance_note"],
            "stop_condition": pending["stop_condition"],
        },
        "decision": {
            "status": "threshold-family-historical-bounded-context",
            "reason": (
                "The current residual is only 73px and already splits into two helper-stage buckets, "
                "including an 8px threshold-family crossing at raw_inside 35.014 -> 36.013 -> 37.013. "
                "Local field debug proves the field_x flip happens before compose, while the broad "
                "trunc_plateau_binary probe explodes the frame to 182793px. This lane is now historical "
                "bounded context: it explains why broad Constant rewrites stay forbidden, while the live "
                "Windows ask has moved to the narrower output-word / compose-refcon triplet witness."
            ),
            "forbidden_action": (
                "Do not promote a global Constant plateau/equality tweak or compose/writeback retune "
                "from the current local evidence alone."
            ),
            "next_windows_requirement": (
                "Bind the `414/415/416,393` triplet from the output-word address or compose refcon at "
                "`FUN_181170480`; do not accept another broad callback stop with no retained XY."
            ),
        },
    }
    return report


def render_md(report: dict[str, Any]) -> str:
    edge = report["residual"]["edge_bucket"]
    threshold = report["residual"]["threshold_bucket"]
    plateau = report["plateau_probe"]
    pending = report["pending_windows_followup"]
    lines = [
        "# OLMDistanceGradation case_0023 Threshold-Family Audit",
        "",
        f"- Case: `{report['case_id']}`",
        f"- Mode: `Interpolation={report['mode']['interpolation']}`, `In/Out={report['mode']['in_out']}`, `Outside Threshold={report['mode']['outside_threshold']}`",
        f"- Decision: `{report['decision']['status']}`",
        f"- Reason: {report['decision']['reason']}",
        f"- Forbidden action: {report['decision']['forbidden_action']}",
        f"- Next Windows requirement: {report['decision']['next_windows_requirement']}",
        "",
        "## Residual Split",
        "",
        f"- Total residual px: `{report['residual']['total_px']}`",
        f"- Endpoint pairs: `{report['residual']['endpoint_pairs']}`",
        f"- Edge bucket: `inside={edge['inside_distance']}` / `count={edge['count']}` / `outside={edge['outside_distance_values']}`",
        f"- Threshold bucket: `inside={threshold['inside_distance']}` / `count={threshold['count']}` / `outside={threshold['outside_distance_values']}`",
        "",
        "## Threshold Triplet",
        "",
        "| Role | XY | field_x | raw_inside | inside-threshold | raw_outside | d_alpha |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in report["threshold_triplet_roles"]:
        lines.append(
            f"| `{row['role']}` | `({row['x']},{row['y']})` | `{row['field_x']}` | `{row['raw_inside']}` | `{row['inside_minus_threshold']}` | `{row['raw_outside']}` | `{row['d_alpha']}` |"
        )
    lines.extend(
        [
            "",
            "## Plateau Probe Rejection",
            "",
            f"- Current residual px: `{plateau['current_residual_px']}`",
            f"- Plateau residual px: `{plateau['plateau_residual_px']}`",
            f"- Edge bucket delta: `{plateau['edge_bucket_delta']}`",
            f"- Threshold bucket current -> plateau: `{plateau['threshold_bucket_current_count']} -> {plateau['threshold_bucket_plateau_count']}`",
            f"- Threshold bucket delta: `{plateau['threshold_bucket_delta']}`",
            f"- Threshold bucket invariant under plateau probe: `{plateau['threshold_bucket_invariant_under_plateau_probe']}`",
            "",
            "## Pending Windows Follow-up",
            "",
            f"- Request: `{pending['request_id']}`",
            f"- Status: `{pending['status']}`",
            f"- Package: `{pending['package']}`",
            f"- Acceptance: `{pending['acceptance_note']}`",
            f"- Stop condition: {pending['stop_condition']}",
            "",
            "## Reading",
            "",
            "- The threshold-family lane is already bounded locally: `(414,393)` stays below threshold, `(415,393)` is the first above-threshold side, and `(416,393)` is deeper into the same plateau side.",
            "- The broad plateau rewrite is explicitly non-promotable because it turns a 73px lane into a 182793px frame-wide regression.",
            "- This audit is historical bounded context only; the live Windows requirement is now the narrower output-word / compose-refcon triplet witness.",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    report = build_report(args)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_md(report), encoding="utf-8")
    print(f"report_json={args.output_json}")
    print(f"report_md={args.output_md}")
    print(f"decision={report['decision']['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
