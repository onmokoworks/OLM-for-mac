#!/usr/bin/env python3
"""Summarize OLMRadialBlur Zoom/Rotation/Inner decision state."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--zoom-witness-json",
        type=Path,
        default=ROOT / "refs" / "reports" / "olmradialblur_zoom_witness_20260624" / "audit.json",
    )
    parser.add_argument(
        "--trace-comparison-json",
        type=Path,
        default=ROOT / "refs" / "reports" / "runtime_trace_comparisons" / "olmradialblur_residual_witness_20260624.json",
    )
    parser.add_argument(
        "--inner-summary-json",
        type=Path,
        default=ROOT / "refs" / "reports" / "olmradialblur_inner_candidate_matrix_20260622_002848" / "summary.json",
    )
    parser.add_argument(
        "--inner-csv",
        type=Path,
        default=ROOT / "refs" / "reports" / "olmradialblur_inner_candidate_matrix_20260622_002848" / "candidate_matrix.csv",
    )
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-md", type=Path, default=None)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def inner_candidate_stats(csv_path: Path) -> dict[str, Any]:
    by_candidate: dict[str, list[dict[str, Any]]] = defaultdict(list)
    with csv_path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            candidate = str(row["candidate"])
            by_candidate[candidate].append(
                {
                    "case_id": row["case_id"],
                    "max_diff": int(row["max_diff"]),
                    "mean_diff": float(row["mean_diff"]),
                    "nonzero_px_percent": float(row["nonzero_px_percent"]),
                }
            )

    current = {row["case_id"]: row for row in by_candidate.get("current-default", [])}
    rows = []
    for candidate, candidate_rows in sorted(by_candidate.items()):
        mean_sum = sum(float(row["mean_diff"]) for row in candidate_rows)
        max_max = max((int(row["max_diff"]) for row in candidate_rows), default=0)
        exact_count = sum(1 for row in candidate_rows if int(row["max_diff"]) == 0 and float(row["mean_diff"]) == 0.0)
        improved = 0
        worsened = 0
        for row in candidate_rows:
            base = current.get(row["case_id"])
            if not base or candidate == "current-default":
                continue
            if float(row["mean_diff"]) < float(base["mean_diff"]):
                improved += 1
            elif float(row["mean_diff"]) > float(base["mean_diff"]):
                worsened += 1
        rows.append(
            {
                "candidate": candidate,
                "mean_sum": mean_sum,
                "max_max": max_max,
                "exact_count": exact_count,
                "improved_cases": improved,
                "worsened_cases": worsened,
            }
        )
    rows.sort(key=lambda row: float(row["mean_sum"]))
    return {
        "candidates": rows,
        "best_by_mean_sum": rows[0]["candidate"] if rows else None,
        "all_exact_candidates": [row["candidate"] for row in rows if row["exact_count"] == len(current) and current],
        "case_count": len(current),
    }


def trace_cases(trace: dict[str, Any]) -> dict[str, dict[str, Any]]:
    cases = {}
    for row in (trace.get("windows") or {}).get("cases", []):
        if isinstance(row, dict):
            cases[str(row.get("case_id"))] = row
    return cases


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    zoom = read_json(args.zoom_witness_json)
    trace = read_json(args.trace_comparison_json)
    inner_summary = read_json(args.inner_summary_json)
    inner_stats = inner_candidate_stats(args.inner_csv)
    cases = trace_cases(trace)
    zoom_delta = zoom.get("deltas", {}).get("local_floor_minus_windows_u8")
    tiny = cases.get("case_0010") or {}

    zoom_decision = (
        "guarded-alpha-normalization"
        if zoom_delta == [0, 0, 0, 1]
        else "needs-review"
    )
    rotation_decision = (
        "blocked-sampler-validity"
        if tiny.get("classification", "").startswith("inverse-sampler")
        else "needs-review"
    )
    inner_decision = (
        "blocked-no-global-toggle"
        if inner_stats["best_by_mean_sum"] == inner_summary.get("best_by_mean_sum")
        and not inner_stats["all_exact_candidates"]
        else "needs-review"
    )

    return {
        "kind": "olmradialblur_decision_matrix",
        "schema": 1,
        "inputs": {
            "zoom_witness_json": str(args.zoom_witness_json),
            "trace_comparison_json": str(args.trace_comparison_json),
            "inner_summary_json": str(args.inner_summary_json),
            "inner_csv": str(args.inner_csv),
        },
        "zoom": {
            "decision": zoom_decision,
            "case_id": zoom.get("case_id"),
            "xy": zoom.get("xy"),
            "local_floor_minus_windows_u8": zoom_delta,
            "local_float": (zoom.get("local") or {}).get("local_sample_float"),
            "windows_float": (zoom.get("windows_trace") or {}).get("pre_writeback_rgba_float"),
            "interpretation": zoom.get("interpretation"),
            "next_evidence": "Zoom polar alpha/sample accumulation; not final byte packing.",
        },
        "tiny_rotation": {
            "decision": rotation_decision,
            "case_id": tiny.get("case_id"),
            "xy": (tiny.get("witness") or {}),
            "classification": tiny.get("classification"),
            "final_rgba_u8": tiny.get("aex_final_rgba_u8"),
            "closest_sampler_float": tiny.get("aex_source_or_polar_rgba_float"),
            "next_evidence": "Exact inverse-sampler validity/border and pre-writeback path for the high-max top-border witness.",
        },
        "inner": {
            "decision": inner_decision,
            "reference": inner_summary.get("reference"),
            "case_count": inner_stats["case_count"],
            "best_by_mean_sum": inner_stats["best_by_mean_sum"],
            "all_exact_candidates": inner_stats["all_exact_candidates"],
            "top_candidates": inner_stats["candidates"][:4],
            "next_evidence": "Typed FUN_180001c90 per-cell witness for one low-span cell and one Quality/strong cell.",
        },
        "decision": "blocked-needs-narrow-proof",
        "recommended_action": (
            "Do not promote broad RadialBlur toggles from PNG matrices. Zoom is alpha-normalization/sampler-side; "
            "tiny Rotation needs sampler/validity proof; Inner needs typed per-cell helper evidence."
        ),
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OLMRadialBlur Decision Matrix",
        "",
        f"- Decision: `{report['decision']}`",
        f"- Recommended action: {report['recommended_action']}",
        "",
        "## Zoom",
        "",
        f"- Decision: `{report['zoom']['decision']}`",
        f"- Case/XY: `{report['zoom']['case_id']}` `{report['zoom']['xy']}`",
        f"- Local floor minus Windows u8: `{report['zoom']['local_floor_minus_windows_u8']}`",
        f"- Next evidence: {report['zoom']['next_evidence']}",
        "",
        "## Tiny Rotation",
        "",
        f"- Decision: `{report['tiny_rotation']['decision']}`",
        f"- Classification: `{report['tiny_rotation']['classification']}`",
        f"- Final u8: `{report['tiny_rotation']['final_rgba_u8']}`",
        f"- Closest sampler float: `{report['tiny_rotation']['closest_sampler_float']}`",
        f"- Next evidence: {report['tiny_rotation']['next_evidence']}",
        "",
        "## Inner",
        "",
        f"- Decision: `{report['inner']['decision']}`",
        f"- Best by mean sum: `{report['inner']['best_by_mean_sum']}`",
        f"- Exact candidates: `{report['inner']['all_exact_candidates']}`",
        f"- Next evidence: {report['inner']['next_evidence']}",
        "",
        "| Candidate | Mean sum | Max max | Improved | Worsened | Exact |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in report["inner"]["top_candidates"]:
        lines.append(
            f"| `{row['candidate']}` | {float(row['mean_sum']):.6f} | {row['max_max']} | "
            f"{row['improved_cases']} | {row['worsened_cases']} | {row['exact_count']} |"
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
