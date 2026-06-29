#!/usr/bin/env python3
"""Summarize runtime-trace returns into per-request proof-lane status."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-summary-json", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-md", type=Path, default=None)
    return parser.parse_args()


def resolve(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def contract_doc_for_request(request_id: str) -> str | None:
    mapping = [
        ("olmdistancegradation", "refs/conformance/olmdistancegradation_pending_layer_source_proof_20260629.md"),
        ("olmdirectionalblur", "refs/conformance/olmdirectionalblur_pending_witness_proof_20260629.md"),
        ("olmradialblur", "refs/conformance/olmradialblur_pending_narrow_proof_20260629.md"),
        ("olmkirakira", "refs/conformance/olmkirakira_pending_compose_proof_20260629.md"),
        ("olmsmoother2_current_aex", "refs/reports/olmsmoother2_current_aex_proof_plan_20260625/proof_plan.md"),
        ("olmsmoother2", "refs/reports/olmsmoother2_current_aex_proof_plan_20260625/proof_plan.md"),
        ("olmblur", "refs/conformance/olmblur_pending_final_word_proof_20260629.md"),
        ("colorkey", "notes/CONFORMANCE_LEDGER.md"),
    ]
    for needle, path in mapping:
        if needle in request_id:
            return path
    return None


def observation_lane_summaries(observations: dict[str, Any]) -> list[str]:
    summaries: list[str] = []
    best = observations.get("best_current_classification")
    if isinstance(best, dict):
        for key, value in best.items():
            summaries.append(f"{key}: {value}")
    cases = observations.get("cases")
    if isinstance(cases, list):
        for row in cases[:4]:
            if not isinstance(row, dict):
                continue
            case_id = row.get("case_id", "?")
            if isinstance(row.get("status"), str):
                summaries.append(f"{case_id}: status={row['status']}")
            if isinstance(row.get("reason"), str):
                summaries.append(f"{case_id}: {row['reason']}")
            if isinstance(row.get("next_trace_needed"), str):
                summaries.append(f"{case_id}: next={row['next_trace_needed']}")
            if isinstance(row.get("interpretation"), str):
                summaries.append(f"{case_id}: {row['interpretation']}")
    return summaries[:8]


def observation_missing_points(observations: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    why = observations.get("why_this_is_partial")
    if isinstance(why, list):
        missing.extend(str(item) for item in why[:6])
    cases = observations.get("cases")
    if isinstance(cases, list):
        for row in cases[:4]:
            if not isinstance(row, dict):
                continue
            if isinstance(row.get("next_trace_needed"), str):
                missing.append(row["next_trace_needed"])
    return missing[:8]


def build_summary(summary: dict[str, Any], summary_path: Path) -> dict[str, Any]:
    results = summary.get("results", [])
    if not isinstance(results, list):
        raise ValueError("runtime summary results must be a list")

    rows: list[dict[str, Any]] = []
    counts = Counter()
    for row in results:
        if not isinstance(row, dict):
            continue
        request_id = str(row.get("request_id") or "")
        status = str(row.get("status") or "unknown")
        counts[status] += 1
        observations = row.get("observations")
        if not isinstance(observations, dict):
            observations = {}
        effect = observations.get("effect") if isinstance(observations.get("effect"), str) else None
        summary_text = row.get("summary") if isinstance(row.get("summary"), str) else None
        rows.append(
            {
                "request_id": request_id,
                "status": status,
                "effect": effect,
                "summary": summary_text,
                "lane_summaries": observation_lane_summaries(observations),
                "missing_points": observation_missing_points(observations),
                "contract_doc": contract_doc_for_request(request_id),
            }
        )

    return {
        "kind": "runtime_trace_proof_lane_summary",
        "schema": 1,
        "runtime_summary_json": str(summary_path),
        "status_counts": dict(sorted(counts.items())),
        "requests": rows,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Runtime Trace Proof-Lane Summary",
        "",
        f"- Runtime summary: `{report['runtime_summary_json']}`",
        f"- Status counts: `{report['status_counts']}`",
        "",
    ]
    for row in report["requests"]:
        lines.extend(
            [
                f"## {row['request_id']}",
                "",
                f"- status: `{row['status']}`",
                f"- effect: `{row['effect'] or '-'}`",
            ]
        )
        if row.get("contract_doc"):
            lines.append(f"- contract doc: `{row['contract_doc']}`")
        if row.get("summary"):
            lines.append(f"- intake summary: {row['summary']}")
        if row["lane_summaries"]:
            lines.append("- lane summaries:")
            for item in row["lane_summaries"]:
                lines.append(f"  - {item}")
        if row["missing_points"]:
            lines.append("- still missing:")
            for item in row["missing_points"]:
                lines.append(f"  - {item}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    root = repo_root()
    summary_path = resolve(root, args.runtime_summary_json)
    report = build_summary(load_json(summary_path), summary_path)

    output_json = resolve(root, args.output_json) if args.output_json else summary_path.with_name(summary_path.stem + "_proof_lanes.json")
    output_md = resolve(root, args.output_md) if args.output_md else summary_path.with_name(summary_path.stem + "_proof_lanes.md")
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(report), encoding="utf-8")
    print(f"proof_lane_json={output_json}")
    print(f"proof_lane_md={output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
