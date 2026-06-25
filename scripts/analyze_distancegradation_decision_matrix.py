#!/usr/bin/env python3
"""Summarize OLMDistanceGradation conformance and residual decisions."""

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
        default=ROOT / "refs" / "reports" / "olmdistancegradation_reference_provenance_20260622_025045" / "audit.json",
    )
    parser.add_argument(
        "--canonicalization-json",
        type=Path,
        default=ROOT / "refs" / "reports" / "software_reference_canonicalization_8bpc.json",
    )
    parser.add_argument(
        "--trace-comparison-json",
        type=Path,
        default=ROOT / "refs" / "reports" / "runtime_trace_comparisons" / "olmdistancegradation_field_prep_latest.json",
    )
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-md", type=Path, default=None)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def distance_features(canonicalization: dict[str, Any]) -> list[dict[str, Any]]:
    features = [
        feature
        for feature in canonicalization.get("features", [])
        if isinstance(feature, dict) and str(feature.get("name", "")).startswith("OLMDistanceGradation")
    ]
    if not features:
        raise ValueError("OLMDistanceGradation features not found in canonicalization report")
    return features


def summarize_canonical(features: list[dict[str, Any]]) -> dict[str, Any]:
    case_count = sum(int(feature.get("case_count", 0)) for feature in features)
    normalized_nonzero = sum(int(feature.get("normalized_nonzero_count", 0)) for feature in features)
    legacy_nonzero = sum(int(feature.get("legacy_nonzero_count", 0)) for feature in features)
    statuses = sorted({str(feature.get("canonical_8bpc_status")) for feature in features})
    legacy_drift_cases = []
    for feature in features:
        for row in feature.get("legacy_drift_cases", []):
            if isinstance(row, dict):
                drift = dict(row)
                drift["feature"] = feature.get("name")
                legacy_drift_cases.append(drift)
    return {
        "case_count": case_count,
        "normalized_nonzero_count": normalized_nonzero,
        "legacy_nonzero_count": legacy_nonzero,
        "statuses": statuses,
        "legacy_drift_cases": legacy_drift_cases,
        "classification": "exact" if normalized_nonzero == 0 and statuses == ["normalized-software-exact"] else "residual",
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    provenance = read_json(args.provenance_json)
    canonical = summarize_canonical(distance_features(read_json(args.canonicalization_json)))
    trace = read_json(args.trace_comparison_json) if args.trace_comparison_json.exists() else {}
    classification = provenance.get("classification", {})
    trace_focus = trace.get("likely_next_focus", "missing-trace-comparison")
    trace_present = bool((trace.get("windows") or {}).get("present"))

    if canonical["classification"] == "exact" and classification.get("status") == "normalized-software-exact-with-legacy-drift":
        decision = "preserve-normalized-ae-exact"
        action = (
            "Do not tune DistanceGradation from legacy-only drift or AE-free CLI residuals. "
            "Preserve normalized 8bpc AE exact behavior and use binary/runtime evidence only if closing the CLI harness gap."
        )
    elif canonical["classification"] == "residual":
        decision = "current-residual-needs-proof"
        action = "Treat normalized residuals as active and inspect field/OpenCV/compose evidence before changing code."
    else:
        decision = "needs-review"
        action = "Review provenance/canonicalization before changing DistanceGradation behavior."

    return {
        "kind": "olmdistancegradation_decision_matrix",
        "schema": 1,
        "inputs": {
            "provenance_json": str(args.provenance_json),
            "canonicalization_json": str(args.canonicalization_json),
            "trace_comparison_json": str(args.trace_comparison_json),
        },
        "normalized_8bpc": {
            "case_count": canonical["case_count"],
            "exact_count": canonical["case_count"] - canonical["normalized_nonzero_count"],
            "normalized_nonzero_count": canonical["normalized_nonzero_count"],
            "statuses": canonical["statuses"],
            "classification": canonical["classification"],
        },
        "legacy_drift": {
            "classification": classification.get("status"),
            "legacy_nonzero_count": canonical["legacy_nonzero_count"],
            "cases": canonical["legacy_drift_cases"],
            "recommended_action": classification.get("recommended_action"),
        },
        "runtime_trace": {
            "likely_next_focus": trace_focus,
            "present": trace_present,
            "classification": "not-actionable" if trace_focus in {"await-windows-trace", "trace-too-sparse"} else "review",
        },
        "decision": decision,
        "recommended_action": action,
        "next_evidence": [
            "Preserve Mac AE exact behavior against canonical normalized 8bpc DistanceGradation refs.",
            "16bpc and 32bpc Software reference coverage for basic, extended, and blur groups.",
            "Only request field-prep/OpenCV runtime trace if we decide to close AE-free CLI residuals or a current normalized residual reappears.",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OLMDistanceGradation Decision Matrix",
        "",
        f"- Decision: `{report['decision']}`",
        f"- Recommended action: {report['recommended_action']}",
        "",
        "## Evidence",
        "",
        f"- Normalized 8bpc: `{report['normalized_8bpc']['classification']}` "
        f"({report['normalized_8bpc']['exact_count']}/{report['normalized_8bpc']['case_count']} exact)",
        f"- Legacy drift: `{report['legacy_drift']['classification']}` "
        f"({report['legacy_drift']['legacy_nonzero_count']} cases)",
        f"- Runtime trace: `{report['runtime_trace']['classification']}` "
        f"(focus `{report['runtime_trace']['likely_next_focus']}`)",
        "",
        "## Legacy Drift Cases",
        "",
        "| Feature | Case | Max | Mean | Witness |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for row in report["legacy_drift"]["cases"]:
        witness = row.get("max_at", {})
        lines.append(
            f"| `{row.get('feature')}` | `{row.get('id')}` | {row.get('max_diff')} | "
            f"{float(row.get('mean_diff', 0.0)):.9f} | "
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
