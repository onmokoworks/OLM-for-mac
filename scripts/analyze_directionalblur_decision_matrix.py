#!/usr/bin/env python3
"""Summarize OLMDirectionalBlur candidate/residual/runtime decision state."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--candidate-summary-json",
        type=Path,
        default=ROOT / "refs" / "reports" / "olmdirectionalblur_candidate_matrix_20260622_010433" / "summary.json",
    )
    parser.add_argument(
        "--residual-clusters-json",
        type=Path,
        default=ROOT / "refs" / "reports" / "olmdirectionalblur_residual_clusters_20260622_022500" / "residual_clusters.json",
    )
    parser.add_argument(
        "--trace-comparison-json",
        type=Path,
        default=ROOT / "refs" / "reports" / "runtime_trace_comparisons" / "olmdirectionalblur_residual_witness_20260624.json",
    )
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-md", type=Path, default=None)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def summarize_candidates(data: dict[str, Any]) -> dict[str, Any]:
    rows = data.get("summary", [])
    if not isinstance(rows, list):
        rows = []
    sorted_rows = [row for row in rows if isinstance(row, dict)]
    sorted_rows.sort(key=lambda row: float(row.get("mean_sum", 1e99)))
    aex_rows = [
        row
        for row in sorted_rows
        if str(row.get("candidate", "")).startswith("rotated-aex")
    ]
    exact_rows = [row for row in sorted_rows if int(row.get("max_diff", 0)) == 0 and float(row.get("mean_sum", 0.0)) == 0.0]
    return {
        "profile": data.get("profile"),
        "cases": data.get("cases", []),
        "best_overall": sorted_rows[0] if sorted_rows else None,
        "best_aex_shaped": aex_rows[0] if aex_rows else None,
        "exact_candidates": exact_rows,
        "top_candidates": sorted_rows[:5],
    }


def summarize_residuals(data: dict[str, Any]) -> list[dict[str, Any]]:
    results = []
    for row in data.get("cases", []):
        if not isinstance(row, dict):
            continue
        classification = row.get("classification") if isinstance(row.get("classification"), dict) else {}
        witness = row.get("top_witnesses", [{}])[0] if row.get("top_witnesses") else row.get("max_at", {})
        results.append(
            {
                "name": row.get("name"),
                "case_id": row.get("case_id"),
                "residual_kind": classification.get("residual_kind"),
                "max_diff": int(row.get("max_diff", 0)),
                "mean_diff": float(row.get("mean_diff", 0.0)),
                "alpha_max": classification.get("alpha_max"),
                "rgb_max": classification.get("rgb_max"),
                "witness": witness,
            }
        )
    return results


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    candidate = summarize_candidates(read_json(args.candidate_summary_json))
    residuals = summarize_residuals(read_json(args.residual_clusters_json))
    trace = read_json(args.trace_comparison_json)
    trace_focus = str(trace.get("likely_next_focus", "missing-trace-comparison"))
    trace_status = ((trace.get("windows") or {}).get("status"))
    has_runtime_values = bool((trace.get("windows") or {}).get("cases"))

    decision = "blocked-await-runtime-or-asm-proof"
    if has_runtime_values:
        decision = "review-runtime-values"

    return {
        "kind": "olmdirectionalblur_decision_matrix",
        "schema": 1,
        "inputs": {
            "candidate_summary_json": str(args.candidate_summary_json),
            "residual_clusters_json": str(args.residual_clusters_json),
            "trace_comparison_json": str(args.trace_comparison_json),
        },
        "candidate_matrix": {
            **candidate,
            "classification": "no-exact-candidate",
            "implementation_warning": "best overall candidates are measurement scaffolds; AEX-shaped candidates remain high residual",
        },
        "residuals": {
            "cases": residuals,
            "classification": "split-angle0-vs-diagonal" if len(residuals) >= 2 else "needs-review",
        },
        "runtime_trace": {
            "status": trace_status,
            "likely_next_focus": trace_focus,
            "has_per_pixel_values": has_runtime_values,
            "classification": "not-actionable" if not has_runtime_values else "review",
        },
        "decision": decision,
        "recommended_action": (
            "Do not tune DirectionalBlur from broad PNG matrices. Need a typed angle-0 rowdriver/valid-alpha witness "
            "and a separate diagonal rotate-path sampler/validity witness before changing implementation."
        ),
        "next_evidence": [
            "Successful runtime/asm proof for angle-0 case_0001 rowdriver accumulation or valid-alpha side channel.",
            "Successful runtime/asm proof for diagonal case_0005 rotate/sampler/validity path.",
            "Keep direct/rotated-front-strength as measurement baselines only, not implementation truth.",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    best = report["candidate_matrix"]["best_overall"] or {}
    best_aex = report["candidate_matrix"]["best_aex_shaped"] or {}
    lines = [
        "# OLMDirectionalBlur Decision Matrix",
        "",
        f"- Decision: `{report['decision']}`",
        f"- Recommended action: {report['recommended_action']}",
        "",
        "## Candidate Matrix",
        "",
        f"- Best overall: `{best.get('candidate')}` mean `{best.get('mean_sum')}` max `{best.get('max_diff')}`",
        f"- Best AEX-shaped: `{best_aex.get('candidate')}` mean `{best_aex.get('mean_sum')}` max `{best_aex.get('max_diff')}`",
        f"- Exact candidates: `{[row.get('candidate') for row in report['candidate_matrix']['exact_candidates']]}`",
        f"- Warning: {report['candidate_matrix']['implementation_warning']}",
        "",
        "| Candidate | Mean sum | Max |",
        "| --- | ---: | ---: |",
    ]
    for row in report["candidate_matrix"]["top_candidates"]:
        lines.append(f"| `{row.get('candidate')}` | {float(row.get('mean_sum', 0.0)):.6f} | {row.get('max_diff')} |")
    lines.extend(
        [
            "",
            "## Residual Split",
            "",
            f"- Classification: `{report['residuals']['classification']}`",
            "",
            "| Case | Kind | Max | Mean | Witness |",
            "| --- | --- | ---: | ---: | --- |",
        ]
    )
    for row in report["residuals"]["cases"]:
        witness = row.get("witness") or {}
        xy = [witness.get("x"), witness.get("y")]
        lines.append(
            f"| `{row.get('case_id')}` | `{row.get('residual_kind')}` | {row.get('max_diff')} | "
            f"{float(row.get('mean_diff', 0.0)):.6f} | `{xy}` |"
        )
    lines.extend(
        [
            "",
            "## Runtime Trace",
            "",
            f"- Status: `{report['runtime_trace']['status']}`",
            f"- Focus: `{report['runtime_trace']['likely_next_focus']}`",
            f"- Classification: `{report['runtime_trace']['classification']}`",
            "",
            "## Next Evidence",
            "",
        ]
    )
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
