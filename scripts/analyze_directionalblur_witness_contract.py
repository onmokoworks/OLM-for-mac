#!/usr/bin/env python3
"""Build a compact OLMDirectionalBlur witness contract.

DirectionalBlur is currently blocked by missing typed runtime/asm proof.  This
report freezes the two residual witness classes and the implementation changes
that must not be promoted from broad PNG matrices alone.
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
        "--decision-json",
        type=Path,
        default=ROOT / "refs" / "reports" / "olmdirectionalblur_decision_matrix_20260624" / "decision_matrix.json",
    )
    parser.add_argument(
        "--trace-json",
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


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    decision = read_json(args.decision_json)
    trace = read_json(args.trace_json)
    residual_cases = (decision.get("residuals") or {}).get("cases") or []
    residuals = []
    for row in residual_cases:
        if not isinstance(row, dict):
            continue
        case_id = str(row.get("case_id"))
        kind = str(row.get("residual_kind"))
        if case_id == "case_0001":
            proof = (
                "Typed angle-0 rowdriver accumulation or valid-alpha side-channel "
                "values at the RGB-only witness."
            )
            local_stop = (
                "Do not replace AEX choreography with direct/front-strength just "
                "because it has a lower broad mean; alpha already matches at this witness."
            )
        elif case_id == "case_0005":
            proof = (
                "Typed diagonal rotate/sampler/validity values at the RGB+alpha "
                "rotate-path witness."
            )
            local_stop = (
                "Do not use the angle-0 witness to tune diagonal behavior; this "
                "case has a separate rotate/validity failure class."
            )
        else:
            proof = "Typed runtime or asm proof for the first divergent stage."
            local_stop = "Do not promote a broad PNG candidate from this residual alone."
        residuals.append(
            {
                "case_id": case_id,
                "kind": kind,
                "witness": row.get("witness"),
                "max_diff": row.get("max_diff"),
                "mean_diff": row.get("mean_diff"),
                "rgb_max": row.get("rgb_max"),
                "alpha_max": row.get("alpha_max"),
                "required_proof": proof,
                "local_stop_line": local_stop,
            }
        )

    candidate_matrix = decision.get("candidate_matrix") or {}
    runtime_trace = decision.get("runtime_trace") or {}
    return {
        "kind": "olmdirectionalblur_witness_contract",
        "schema": 1,
        "inputs": {
            "decision_json": str(args.decision_json),
            "trace_json": str(args.trace_json),
        },
        "decision": "blocked-await-runtime-or-asm-proof",
        "runtime_trace": {
            "status": (trace.get("windows") or {}).get("status") or runtime_trace.get("status"),
            "classification": runtime_trace.get("classification"),
            "has_per_pixel_values": runtime_trace.get("has_per_pixel_values"),
            "summary": (trace.get("windows") or {}).get("summary"),
        },
        "candidate_matrix": {
            "classification": candidate_matrix.get("classification"),
            "best_overall": candidate_matrix.get("best_overall"),
            "best_aex_shaped": candidate_matrix.get("best_aex_shaped"),
            "exact_candidates": candidate_matrix.get("exact_candidates"),
            "implementation_warning": candidate_matrix.get("implementation_warning"),
        },
        "keep": [
            "Keep AEX-shaped rotate/populate/output facts as implementation truth even when measurement scaffolds score lower.",
            "Keep direct/rotated-front-strength as measurement baselines only.",
            "Do not tune from the 2026-06-24 runtime return; it is value-sparse and answered_partial.",
            "Do not merge angle-0 and diagonal residuals; they require separate proof.",
        ],
        "residuals": residuals,
        "next_step": (
            "Obtain or derive a typed witness for case_0001 angle-0 rowdriver/"
            "valid-alpha and case_0005 diagonal rotate/sampler/validity before "
            "changing DirectionalBlur implementation."
        ),
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OLMDirectionalBlur Witness Contract",
        "",
        f"- Decision: `{report['decision']}`",
        f"- Next step: {report['next_step']}",
        "",
        "## Runtime Trace",
        "",
        f"- Status: `{report['runtime_trace']['status']}`",
        f"- Classification: `{report['runtime_trace']['classification']}`",
        f"- Has per-pixel values: `{report['runtime_trace']['has_per_pixel_values']}`",
        f"- Summary: {report['runtime_trace']['summary']}",
        "",
        "## Candidate Matrix",
        "",
        f"- Classification: `{report['candidate_matrix']['classification']}`",
        f"- Best overall: `{report['candidate_matrix']['best_overall']}`",
        f"- Best AEX-shaped: `{report['candidate_matrix']['best_aex_shaped']}`",
        f"- Exact candidates: `{report['candidate_matrix']['exact_candidates']}`",
        f"- Warning: {report['candidate_matrix']['implementation_warning']}",
        "",
        "## Keep",
        "",
    ]
    lines.extend(f"- {item}" for item in report["keep"])
    lines.extend(
        [
            "",
            "## Residual Witnesses",
            "",
            "| Case | Kind | Witness | Max | RGB max | Alpha max | Required proof | Stop line |",
            "| --- | --- | --- | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for row in report["residuals"]:
        lines.append(
            f"| `{row['case_id']}` | `{row['kind']}` | `{row['witness']}` | "
            f"{row['max_diff']} | {row['rgb_max']} | {row['alpha_max']} | "
            f"{row['required_proof']} | {row['local_stop_line']} |"
        )
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
