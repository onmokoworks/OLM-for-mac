#!/usr/bin/env python3
"""Summarize OLMColorKey Edge conformance and residual decisions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--provenance-json",
        type=Path,
        default=ROOT / "refs" / "reports" / "olmcolorkey_edge_reference_provenance_20260622_024907" / "audit.json",
    )
    parser.add_argument(
        "--canonicalization-json",
        type=Path,
        default=ROOT / "refs" / "reports" / "software_reference_canonicalization_8bpc.json",
    )
    parser.add_argument(
        "--trace-comparison-json",
        type=Path,
        default=ROOT / "refs" / "reports" / "runtime_trace_comparisons" / "olmcolorkey_edge_trace_latest.json",
    )
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-md", type=Path, default=None)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def color_key_feature(canonicalization: dict[str, Any]) -> dict[str, Any]:
    for feature in canonicalization.get("features", []):
        if isinstance(feature, dict) and feature.get("name") == "OLMColorKey":
            return feature
    raise ValueError("OLMColorKey feature not found in canonicalization report")


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    provenance = read_json(args.provenance_json)
    canonical = color_key_feature(read_json(args.canonicalization_json))
    trace = read_json(args.trace_comparison_json) if args.trace_comparison_json.exists() else {}
    classification = provenance.get("classification", {})
    normalized_status = canonical.get("canonical_8bpc_status")
    case_count = int(canonical.get("case_count", 0))
    normalized_nonzero = int(canonical.get("normalized_nonzero_count", -1))
    legacy_drift_cases = canonical.get("legacy_drift_cases", [])
    trace_focus = trace.get("likely_next_focus", "missing-trace-comparison")
    has_current_residual = normalized_status != "normalized-software-exact" or normalized_nonzero != 0

    if normalized_status == "normalized-software-exact" and classification.get("status") == "reference-generation-split":
        decision = "preserve-normalized-ae-exact"
        action = (
            "Do not tune Edge Blur from the 20260604 case_0009 residual. "
            "Use normalized 20260618 Software refs for 8bpc and move next to Mac AE exact / 16bpc / 32bpc coverage."
        )
    elif has_current_residual:
        decision = "current-residual-needs-proof"
        action = "Treat the normalized residual as active and request a narrow runtime/AE proof before implementation changes."
    else:
        decision = "needs-review"
        action = "Review provenance and canonicalization before changing Edge semantics."

    return {
        "kind": "olmcolorkey_edge_decision_matrix",
        "schema": 1,
        "inputs": {
            "provenance_json": str(args.provenance_json),
            "canonicalization_json": str(args.canonicalization_json),
            "trace_comparison_json": str(args.trace_comparison_json),
        },
        "normalized_8bpc": {
            "status": normalized_status,
            "case_count": case_count,
            "normalized_nonzero_count": normalized_nonzero,
            "exact_count": case_count - max(normalized_nonzero, 0),
            "classification": "exact" if normalized_status == "normalized-software-exact" and normalized_nonzero == 0 else "residual",
        },
        "legacy_split": {
            "classification": classification.get("status"),
            "legacy_max_diff": classification.get("legacy_max_diff"),
            "legacy_drift_cases": legacy_drift_cases,
            "recommended_action": classification.get("recommended_action"),
        },
        "runtime_trace": {
            "likely_next_focus": trace_focus,
            "present": bool((trace.get("windows") or {}).get("present")),
            "classification": "not-actionable" if trace_focus in {"await-windows-trace", "trace-too-sparse"} else "review",
        },
        "decision": decision,
        "recommended_action": action,
        "next_evidence": [
            "Mac AE exact against canonical normalized 8bpc ColorKey refs.",
            "16bpc and 32bpc Software reference coverage for core and Edge paths.",
            "Only request narrow Edge runtime trace if a current normalized Software residual reappears.",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OLMColorKey Edge Decision Matrix",
        "",
        f"- Decision: `{report['decision']}`",
        f"- Recommended action: {report['recommended_action']}",
        "",
        "## Evidence",
        "",
        f"- Normalized 8bpc: `{report['normalized_8bpc']['status']}` "
        f"({report['normalized_8bpc']['exact_count']}/{report['normalized_8bpc']['case_count']} exact)",
        f"- Legacy split: `{report['legacy_split']['classification']}` "
        f"(legacy max `{report['legacy_split']['legacy_max_diff']}`)",
        f"- Runtime trace: `{report['runtime_trace']['classification']}` "
        f"(focus `{report['runtime_trace']['likely_next_focus']}`)",
        "",
        "## Legacy Drift Cases",
        "",
        "| Case | Max | Mean | Witness |",
        "| --- | ---: | ---: | --- |",
    ]
    for row in report["legacy_split"]["legacy_drift_cases"]:
        witness = row.get("max_at", {})
        lines.append(
            f"| `{row.get('id')}` | {row.get('max_diff')} | {float(row.get('mean_diff', 0.0)):.9f} | "
            f"`x={witness.get('x')} y={witness.get('y')} c={witness.get('channel')} "
            f"ref={witness.get('reference')} cand={witness.get('candidate')}` |"
        )
    lines.extend(["", "## Next Evidence", ""])
    lines.extend(f"- {item}" for item in report["next_evidence"])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    report = build_report(args)
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
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
