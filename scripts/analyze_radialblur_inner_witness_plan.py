#!/usr/bin/env python3
"""Select narrow OLMRadialBlur Inner witness cases from the candidate matrix."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


CASE_FAMILIES = {
    "low-span": {
        "cases": {"rb_inner_only_strength_small", "rb_inner_only_strength_large", "rb_inner_offset_mode_3"},
        "why": "Low-span/offset cases prefer circular-wrap-like behavior and regress under loop-minus-one.",
        "required_proof": "Typed FUN_180001c90 values for one low-span cell: resolved span, table index, row/underflow target, source/destination polar cell, and accumulated RGBA/denom.",
    },
    "quality-strong": {
        "cases": {"rb_inner_existing_0011_software_pair", "rb_inner_existing_0012_software_pair", "rb_inner_quality_1", "rb_inner_quality_50"},
        "why": "Strong/high-Quality cases prefer loop-minus-one-like behavior but still keep max residuals.",
        "required_proof": "Typed FUN_180001c90 values for one Quality/strong cell: resolved span, loop bound, table divisor, gaussian weight, source row, and post-scatter accumulation.",
    },
    "edge-prepass": {
        "cases": {"rb_inner_edgefade_only", "rb_outer_inner_edgefade"},
        "why": "Edge Fade cases prefer table-span-minus-one-like behavior and exercise the prepass alpha tables.",
        "required_proof": "Prepass alpha/factor plane and scatter denominator values for one Edge Fade cell before changing table bounds.",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--matrix-csv",
        type=Path,
        default=ROOT / "refs" / "reports" / "olmradialblur_inner_candidate_matrix_20260622_002848" / "candidate_matrix.csv",
    )
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-md", type=Path, default=None)
    return parser.parse_args()


def load_rows(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        row["max_diff"] = int(row["max_diff"])
        row["mean_diff"] = float(row["mean_diff"])
        row["nonzero_px_percent"] = float(row["nonzero_px_percent"])
    return rows


def grouped_by_case(rows: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, Any]]]:
    by_case: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        by_case[str(row["case_id"])][str(row["candidate"])] = row
    return dict(by_case)


def candidate_delta(case_rows: dict[str, dict[str, Any]], candidate: str) -> float | None:
    base = case_rows.get("current-default")
    row = case_rows.get(candidate)
    if not base or not row:
        return None
    return float(row["mean_diff"]) - float(base["mean_diff"])


def classify_case(case_id: str, case_rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    base = case_rows["current-default"]
    deltas = {
        candidate: candidate_delta(case_rows, candidate)
        for candidate in ("loop-minus-one", "circular-wrap", "table-span-minus-one", "grid-aex-float")
    }
    best = min(case_rows.values(), key=lambda row: (float(row["mean_diff"]), int(row["max_diff"])))
    return {
        "case_id": case_id,
        "baseline": {
            "max_diff": base["max_diff"],
            "mean_diff": base["mean_diff"],
            "nonzero_px_percent": base["nonzero_px_percent"],
        },
        "best_candidate": best["candidate"],
        "best": {
            "max_diff": best["max_diff"],
            "mean_diff": best["mean_diff"],
            "nonzero_px_percent": best["nonzero_px_percent"],
        },
        "mean_deltas_vs_current": deltas,
        "exact": best["max_diff"] == 0 and best["mean_diff"] == 0.0,
    }


def choose_representative(family_cases: set[str], classified: dict[str, dict[str, Any]]) -> dict[str, Any]:
    family_rows = [classified[case_id] for case_id in family_cases if case_id in classified]
    if not family_rows:
        raise ValueError(f"missing family rows: {sorted(family_cases)}")
    # Prefer the case where the family-specific best candidate improves most,
    # then the highest baseline mean as a tie-breaker.
    return min(
        family_rows,
        key=lambda row: (
            float(row["mean_deltas_vs_current"].get(str(row["best_candidate"]), 0.0)),
            -float(row["baseline"]["mean_diff"]),
        ),
    )


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    rows = load_rows(args.matrix_csv)
    by_case = grouped_by_case(rows)
    classified = {case_id: classify_case(case_id, case_rows) for case_id, case_rows in by_case.items()}
    families = []
    for family, spec in CASE_FAMILIES.items():
        representative = choose_representative(set(spec["cases"]), classified)
        family_cases = [classified[case_id] for case_id in sorted(spec["cases"]) if case_id in classified]
        families.append(
            {
                "family": family,
                "why": spec["why"],
                "representative": representative,
                "cases": family_cases,
                "required_proof": spec["required_proof"],
            }
        )
    return {
        "kind": "olmradialblur_inner_witness_plan",
        "schema": 1,
        "inputs": {"matrix_csv": str(args.matrix_csv)},
        "decision": "typed-inner-cell-witnesses-only",
        "recommended_action": (
            "Do not promote global Inner toggles. If Windows is needed, trace one "
            "representative low-span cell and one Quality/strong cell; add Edge Fade "
            "prepass only if the first two do not explain the split."
        ),
        "families": families,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OLMRadialBlur Inner Witness Plan",
        "",
        f"- Decision: `{report['decision']}`",
        f"- Recommended action: {report['recommended_action']}",
        "",
        "## Representatives",
        "",
        "| Family | Representative | Baseline mean | Best candidate | Best mean | Required proof |",
        "| --- | --- | ---: | --- | ---: | --- |",
    ]
    for family in report["families"]:
        rep = family["representative"]
        lines.append(
            f"| `{family['family']}` | `{rep['case_id']}` | {rep['baseline']['mean_diff']:.6f} | "
            f"`{rep['best_candidate']}` | {rep['best']['mean_diff']:.6f} | {family['required_proof']} |"
        )
    lines.extend(["", "## Family Detail", ""])
    for family in report["families"]:
        lines.append(f"### {family['family']}")
        lines.append("")
        lines.append(f"- Why: {family['why']}")
        lines.append(f"- Required proof: {family['required_proof']}")
        lines.append("")
        lines.append("| Case | Baseline mean | Baseline max | Best candidate | Best mean | Best max | loop delta | circular delta | table delta |")
        lines.append("| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |")
        for row in family["cases"]:
            deltas = row["mean_deltas_vs_current"]
            lines.append(
                f"| `{row['case_id']}` | {row['baseline']['mean_diff']:.6f} | {row['baseline']['max_diff']} | "
                f"`{row['best_candidate']}` | {row['best']['mean_diff']:.6f} | {row['best']['max_diff']} | "
                f"{deltas['loop-minus-one']:.6f} | {deltas['circular-wrap']:.6f} | {deltas['table-span-minus-one']:.6f} |"
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
