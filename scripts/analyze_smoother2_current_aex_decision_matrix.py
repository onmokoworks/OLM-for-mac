#!/usr/bin/env python3
"""Summarize OLMSmoother2 current-AEX residual decision evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--residual-audit-json",
        type=Path,
        default=ROOT / "refs" / "reports" / "olmsmoother2_current_aex_residual_audit_latest" / "residual_audit.json",
    )
    parser.add_argument(
        "--curve-sweep-json",
        type=Path,
        default=ROOT / "refs" / "reports" / "olmsmoother2_current_aex_curve_idx_sweep_latest" / "curve_idx_sweep.json",
    )
    parser.add_argument(
        "--f270-suppression-json",
        type=Path,
        default=ROOT / "refs" / "reports" / "olmsmoother2_current_aex_leaf_diag_suppress_f270_latest" / "reports" / "diff.json",
    )
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-md", type=Path, default=None)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def metric_tuple(row: dict[str, Any]) -> tuple[int, float, float]:
    return (
        int(row["max_diff"]),
        float(row["mean_sum"]),
        float(row["nonzero_px_percent_sum"]),
    )


def summarize_curve_sweep(curve: dict[str, Any]) -> dict[str, Any]:
    summaries = curve.get("summaries", [])
    if not isinstance(summaries, list) or not summaries:
        raise ValueError("curve sweep has no summaries")
    metrics = [metric_tuple(row) for row in summaries if isinstance(row, dict)]
    first = metrics[0]
    all_identical = all(row == first for row in metrics)
    return {
        "curve_indices": [int(row["curve_idx"]) for row in summaries],
        "all_identical": all_identical,
        "baseline": {
            "curve_idx": int(summaries[0]["curve_idx"]),
            "max_diff": first[0],
            "mean_sum": first[1],
            "nonzero_px_percent_sum": first[2],
        },
        "classification": "rejected-inert" if all_identical else "needs-review",
        "decision": (
            "Do not tune bb10/curve_idx globally; all tested overrides produced identical metrics."
            if all_identical
            else "Curve sweep is not inert; review per-case changes before making any implementation decision."
        ),
    }


def summarize_f270(curve_summary: dict[str, Any], f270: dict[str, Any]) -> dict[str, Any]:
    cases = f270.get("cases", [])
    if not isinstance(cases, list) or not cases:
        raise ValueError("f270 suppression report has no cases")
    max_diff = max(int(row["max_diff"]) for row in cases)
    mean_sum = sum(float(row["mean_diff"]) for row in cases)
    nonzero_sum = sum(float(row["nonzero_px_percent"]) for row in cases)
    baseline = curve_summary["baseline"]
    worsens_mean = mean_sum > float(baseline["mean_sum"])
    worsens_max = max_diff > int(baseline["max_diff"])
    return {
        "max_diff": max_diff,
        "mean_sum": mean_sum,
        "nonzero_px_percent_sum": nonzero_sum,
        "baseline_mean_sum": baseline["mean_sum"],
        "baseline_max_diff": baseline["max_diff"],
        "worsens_mean": worsens_mean,
        "worsens_max": worsens_max,
        "classification": "rejected-worse" if worsens_mean and worsens_max else "needs-review",
        "decision": (
            "Do not suppress f270 globally; it worsens both total mean and max residuals."
            if worsens_mean and worsens_max
            else "f270 suppression is not clearly worse; inspect per-case metrics before deciding."
        ),
    }


def summarize_residuals(residual: dict[str, Any]) -> dict[str, Any]:
    cases = residual.get("cases", [])
    if not isinstance(cases, list) or not cases:
        raise ValueError("residual audit has no cases")
    witnesses = []
    for row in cases:
        witness = row.get("witness", {}) if isinstance(row, dict) else {}
        witnesses.append(
            {
                "case_id": row.get("case_id"),
                "xy": [int(witness["x"]), int(witness["y"])],
                "reference_rgba": witness.get("reference_rgba"),
                "candidate_rgba": witness.get("candidate_rgba"),
                "delta_rgba": witness.get("delta_rgba"),
                "max_channel_diff": int(witness["max_channel_diff"]),
                "mean_diff": float(witness["mean_diff"]),
            }
        )
    return {
        "witnesses": witnesses,
        "classification": "localized-opposite-shapes",
        "decision": (
            "Keep the Smooth Range threshold fix, but do not apply broad alpha/index/curve/f270 toggles. "
            "The next useful evidence is exact local polygon/classifier state for the listed witnesses."
        ),
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    residual = read_json(args.residual_audit_json)
    curve = read_json(args.curve_sweep_json)
    f270 = read_json(args.f270_suppression_json)
    curve_summary = summarize_curve_sweep(curve)
    return {
        "kind": "olmsmoother2_current_aex_decision_matrix",
        "schema": 1,
        "inputs": {
            "residual_audit_json": str(args.residual_audit_json),
            "curve_sweep_json": str(args.curve_sweep_json),
            "f270_suppression_json": str(args.f270_suppression_json),
        },
        "curve_idx": curve_summary,
        "f270_suppression": summarize_f270(curve_summary, f270),
        "residuals": summarize_residuals(residual),
        "next_evidence": [
            "0012 (91,841): exact Windows d3b0/da50/e170/f270/e3a0 state or equivalent asm proof.",
            "0004 (1903,519): exact Windows polygon/no-polygon proof for transparent-center neighbor contribution.",
            "Do not spend the next step on global curve_idx, alpha/index, or f270 suppression toggles.",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OLMSmoother2 Current-AEX Decision Matrix",
        "",
        "## Decisions",
        "",
        f"- Curve index: `{report['curve_idx']['classification']}` - {report['curve_idx']['decision']}",
        f"- f270 suppression: `{report['f270_suppression']['classification']}` - {report['f270_suppression']['decision']}",
        f"- Residual shape: `{report['residuals']['classification']}` - {report['residuals']['decision']}",
        "",
        "## Metrics",
        "",
        f"- Baseline mean sum: `{report['curve_idx']['baseline']['mean_sum']:.12f}`",
        f"- Baseline max diff: `{report['curve_idx']['baseline']['max_diff']}`",
        f"- f270-suppressed mean sum: `{report['f270_suppression']['mean_sum']:.12f}`",
        f"- f270-suppressed max diff: `{report['f270_suppression']['max_diff']}`",
        f"- Curve indices tested: `{report['curve_idx']['curve_indices']}`",
        "",
        "## Witnesses",
        "",
        "| Case | XY | Reference | Candidate | Delta | Max | Mean |",
        "| --- | --- | --- | --- | --- | ---: | ---: |",
    ]
    for row in report["residuals"]["witnesses"]:
        lines.append(
            f"| `{row['case_id']}` | `{row['xy']}` | `{row['reference_rgba']}` | "
            f"`{row['candidate_rgba']}` | `{row['delta_rgba']}` | "
            f"{row['max_channel_diff']} | {row['mean_diff']:.6f} |"
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
