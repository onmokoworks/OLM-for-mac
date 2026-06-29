#!/usr/bin/env python3
"""Select narrow OLMDirectionalBlur runtime/asm witness pixels.

This is a smaller follow-up to the witness contract.  The contract says
DirectionalBlur needs separate angle-0 and diagonal proof; this report chooses
the exact pixels and companion checks that make a Windows trace useful.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--residual-clusters-json",
        type=Path,
        default=ROOT
        / "refs"
        / "reports"
        / "olmdirectionalblur_residual_clusters_20260622_022500"
        / "residual_clusters.json",
    )
    parser.add_argument(
        "--decision-json",
        type=Path,
        default=ROOT
        / "refs"
        / "reports"
        / "olmdirectionalblur_decision_matrix_20260624"
        / "decision_matrix.json",
    )
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-md", type=Path, default=None)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def by_case_id(clusters: dict[str, Any]) -> dict[str, dict[str, Any]]:
    cases = clusters.get("cases") or []
    result: dict[str, dict[str, Any]] = {}
    for row in cases:
        if isinstance(row, dict) and row.get("case_id"):
            result[str(row["case_id"])] = row
    return result


def first_negative_witness(case: dict[str, Any]) -> dict[str, Any] | None:
    for witness in case.get("top_witnesses") or []:
        signed = witness.get("signed_delta_candidate_minus_reference") or []
        if signed and signed[0] < 0:
            return witness
    return None


def preferred_angle0_witness(case: dict[str, Any]) -> dict[str, Any]:
    top = case.get("top_witnesses") or []
    if isinstance(top, list) and top:
        first = top[0]
        if isinstance(first, dict) and "x" in first and "y" in first:
            return first
    return case["max_at"]


def compact_witness(witness: dict[str, Any]) -> dict[str, Any]:
    return {
        "xy": [int(witness["x"]), int(witness["y"])],
        "reference_rgba": witness.get("reference") or witness.get("reference_rgba"),
        "candidate_rgba": witness.get("candidate") or witness.get("candidate_rgba"),
        "signed_delta_candidate_minus_reference": witness.get("signed")
        or witness.get("signed_delta_candidate_minus_reference"),
        "abs_delta_rgba": witness.get("delta") or witness.get("abs_delta_rgba"),
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    clusters = read_json(args.residual_clusters_json)
    decision = read_json(args.decision_json)
    cases = by_case_id(clusters)
    angle0 = cases["case_0001"]
    diagonal = cases["case_0005"]
    angle0_top = [compact_witness(row) for row in (angle0.get("top_witnesses") or [])[:8]]
    diagonal_top = [compact_witness(row) for row in (diagonal.get("top_witnesses") or [])[:8]]
    diagonal_negative = first_negative_witness(diagonal)

    plans = [
        {
            "family": "angle0-rowdriver-valid-alpha",
            "case_id": "case_0001",
            "primary_witness": compact_witness(preferred_angle0_witness(angle0)),
            "scan_order_max_witness": compact_witness(angle0["max_at"]),
            "companion_witnesses": angle0_top,
            "why": (
                "Angle-0/front-only residual has alpha exactly matching but red "
                "missing across a long horizontal strip, so the first proof should "
                "separate rowdriver/group membership from a validity/alpha side channel."
            ),
            "primary_reason": (
                "Use the right-edge strip endpoint instead of the first scan-order max: "
                "the endpoint is more useful for proving row coverage/boundary behavior, "
                "while the interior max belongs to the same long strip."
            ),
            "required_values": [
                "normalized front/back strength, angle, Size Variation, Edge Fade, Sharp Tail, Noise",
                "output pixel to A/B buffer coordinates",
                "rowdriver/group membership and valid-alpha side-channel for the strip",
                "accumulation numerator/denominator and pre-writeback RGBA",
                "final stored RGBA bytes",
            ],
            "stop_line": (
                "Do not replace the AEX-shaped implementation with direct or "
                "rotated-front-strength from this family; alpha is already exact here."
            ),
        },
        {
            "family": "diagonal-rotate-validity",
            "case_id": "case_0005",
            "primary_witness": compact_witness(diagonal["max_at"]),
            "companion_witnesses": [
                compact_witness(diagonal_negative) if diagonal_negative else None,
                *diagonal_top[:5],
            ],
            "why": (
                "Diagonal residual has large signed red errors in both directions "
                "and nonzero alpha residuals, so it must prove rotate sampler order, "
                "border/validity, and normalization separately from the angle-0 path."
            ),
            "required_values": [
                "normalized angle/front/back strength and group-size inputs",
                "rotate sampler source coordinates and sample order",
                "border/validity decision for positive and negative red witnesses",
                "group-size or opacity gate and accumulation denominator",
                "pre-writeback RGBA and final stored RGBA bytes",
            ],
            "stop_line": (
                "Do not tune diagonal behavior from the angle-0 witness; this "
                "family exercises rotate/validity and has a separate failure class."
            ),
        },
    ]
    for plan in plans:
        plan["companion_witnesses"] = [w for w in plan["companion_witnesses"] if w is not None]

    return {
        "kind": "olmdirectionalblur_witness_plan",
        "schema": 1,
        "inputs": {
            "residual_clusters_json": str(args.residual_clusters_json),
            "decision_json": str(args.decision_json),
        },
        "decision": "two-independent-witness-families",
        "recommended_action": (
            "Keep DirectionalBlur blocked until both witness families have typed "
            "runtime/asm values. Do not tune from broad PNG matrices or from only "
            "one of the two families."
        ),
        "decision_matrix_status": decision.get("decision"),
        "plans": plans,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OLMDirectionalBlur Witness Plan",
        "",
        f"- Decision: `{report['decision']}`",
        f"- Recommended action: {report['recommended_action']}",
        f"- Decision matrix status: `{report['decision_matrix_status']}`",
        "",
        "## Representatives",
        "",
        "| Family | Case | Primary XY | Primary ref | Primary cand | Required proof |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for plan in report["plans"]:
        primary = plan["primary_witness"]
        lines.append(
            f"| `{plan['family']}` | `{plan['case_id']}` | `{primary['xy']}` | "
            f"`{primary['reference_rgba']}` | `{primary['candidate_rgba']}` | "
            f"{'; '.join(plan['required_values'][:2])} |"
        )
    lines.append("")
    for plan in report["plans"]:
        lines.extend(
            [
                f"## {plan['family']}",
                "",
                f"- Why: {plan['why']}",
                f"- Primary witness reason: {plan.get('primary_reason', 'Use the primary max witness for this family.')}",
                f"- Stop line: {plan['stop_line']}",
                "",
                "Required values:",
                "",
            ]
        )
        if plan.get("scan_order_max_witness"):
            lines.extend(
                [
                    f"- Scan-order max witness kept for reference: `{plan['scan_order_max_witness']['xy']}` "
                    f"`{plan['scan_order_max_witness']['reference_rgba']}` -> "
                    f"`{plan['scan_order_max_witness']['candidate_rgba']}`",
                    "",
                ]
            )
        lines.extend(f"- {value}" for value in plan["required_values"])
        lines.extend(
            [
                "",
                "Companion witnesses:",
                "",
                "| XY | Ref | Cand | Signed delta |",
                "| --- | --- | --- | --- |",
            ]
        )
        for witness in plan["companion_witnesses"]:
            lines.append(
                f"| `{witness['xy']}` | `{witness['reference_rgba']}` | "
                f"`{witness['candidate_rgba']}` | "
                f"`{witness['signed_delta_candidate_minus_reference']}` |"
            )
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    report = build_report(args)
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(
            json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f"report_json={args.output_json}")
    if args.output_md:
        args.output_md.parent.mkdir(parents=True, exist_ok=True)
        args.output_md.write_text(render_markdown(report), encoding="utf-8")
        print(f"report_md={args.output_md}")
    if not args.output_json and not args.output_md:
        print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
