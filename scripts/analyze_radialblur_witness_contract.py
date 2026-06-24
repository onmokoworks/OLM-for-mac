#!/usr/bin/env python3
"""Build a compact OLMRadialBlur witness contract.

This report freezes the current narrow evidence boundary for Zoom, tiny
Rotation, and Inner.  It is meant to prevent broad PNG-matrix tuning from being
mistaken for binary-grounded progress.
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
        default=ROOT / "refs" / "reports" / "olmradialblur_decision_matrix_20260624" / "decision_matrix.json",
    )
    parser.add_argument(
        "--zoom-json",
        type=Path,
        default=ROOT / "refs" / "reports" / "olmradialblur_zoom_witness_20260624" / "audit.json",
    )
    parser.add_argument(
        "--trace-json",
        type=Path,
        default=ROOT / "refs" / "reports" / "runtime_trace_comparisons" / "olmradialblur_residual_witness_20260624.json",
    )
    parser.add_argument(
        "--scatter-json",
        type=Path,
        default=ROOT / "refs" / "reports" / "olmradialblur_scatter_static_facts.json",
    )
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-md", type=Path, default=None)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def trace_case(trace: dict[str, Any], case_id: str) -> dict[str, Any]:
    for row in (trace.get("windows") or {}).get("cases", []):
        if isinstance(row, dict) and row.get("case_id") == case_id:
            return row
    return {}


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    decision = read_json(args.decision_json)
    zoom = read_json(args.zoom_json)
    trace = read_json(args.trace_json)
    scatter = read_json(args.scatter_json)
    rotation = trace_case(trace, "case_0010")

    top_inner = (decision.get("inner") or {}).get("top_candidates") or []
    zoom_delta = (zoom.get("deltas") or {}).get("local_floor_minus_windows_u8")
    rotation_sample = rotation.get("aex_source_or_polar_rgba_float")
    rotation_final = rotation.get("aex_final_rgba_u8")
    scatter_conclusions = scatter.get("conclusions") or {}
    rotation_sample_u8 = None
    if isinstance(rotation_sample, list) and all(isinstance(v, (int, float)) for v in rotation_sample):
        rotation_sample_u8 = [max(0, min(255, int(float(v) * 255.0))) for v in rotation_sample]

    return {
        "kind": "olmradialblur_witness_contract",
        "schema": 1,
        "inputs": {
            "decision_json": str(args.decision_json),
            "zoom_json": str(args.zoom_json),
            "trace_json": str(args.trace_json),
            "scatter_json": str(args.scatter_json),
        },
        "decision": "blocked-narrow-proof-only",
        "keep": [
            "Do not change final byte packing for Zoom case_0009; Windows floats truncate to the Windows bytes.",
            "Do not treat the closest tiny-Rotation sampler return as the final pre-writeback value.",
            "Do not promote loop-minus-one, table-span-minus-one, circular-wrap, or grid-aex-float globally.",
            "Keep static FUN_180001c90 facts: effective span truncation, table divisor by R14D, inner tail < R14D, underflow to next radius row.",
        ],
        "zoom": {
            "case_id": "case_0009",
            "xy": zoom.get("xy"),
            "local_float": (zoom.get("local") or {}).get("local_sample_float"),
            "windows_float": (zoom.get("windows_trace") or {}).get("pre_writeback_rgba_float"),
            "local_floor_minus_windows_u8": zoom_delta,
            "classification": (zoom.get("windows_trace") or {}).get("classification"),
            "required_proof": "Zoom polar alpha/sample accumulation before sampler return; final byte conversion is already ruled out.",
        },
        "tiny_rotation": {
            "case_id": "case_0010",
            "xy": (rotation.get("witness") or {}),
            "classification": rotation.get("classification"),
            "closest_sampler_float": rotation_sample,
            "closest_sampler_floor_u8": rotation_sample_u8,
            "windows_final_u8": rotation_final,
            "required_proof": "Exact inverse-sampler validity/border branch or substitute pre-writeback path for the top-border high-max witness.",
        },
        "inner": {
            "classification": (decision.get("inner") or {}).get("decision"),
            "best_by_mean_sum": (decision.get("inner") or {}).get("best_by_mean_sum"),
            "exact_candidates": (decision.get("inner") or {}).get("all_exact_candidates"),
            "top_candidates": top_inner[:4],
            "static_facts": {
                "effective_span": scatter_conclusions.get("effective_span_rule"),
                "table_step": scatter_conclusions.get("table_step_rule"),
                "inner_tail": scatter_conclusions.get("tail_loop_rule"),
                "underflow": scatter_conclusions.get("inner_underflow_rule"),
            },
            "required_proof": "Typed FUN_180001c90 per-cell values for a low-span cell and a Quality/strong cell before changing loop/table/wrap behavior.",
        },
        "next_step": "Read/trace only the listed narrow proof points; no broad PNG tuning or global helper toggles.",
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OLMRadialBlur Witness Contract",
        "",
        f"- Decision: `{report['decision']}`",
        f"- Next step: {report['next_step']}",
        "",
        "## Keep",
        "",
    ]
    lines.extend(f"- {item}" for item in report["keep"])
    lines.extend(
        [
            "",
            "## Zoom",
            "",
            f"- Case/XY: `{report['zoom']['case_id']}` `{report['zoom']['xy']}`",
            f"- Classification: `{report['zoom']['classification']}`",
            f"- Local float: `{report['zoom']['local_float']}`",
            f"- Windows float: `{report['zoom']['windows_float']}`",
            f"- Local floor minus Windows u8: `{report['zoom']['local_floor_minus_windows_u8']}`",
            f"- Required proof: {report['zoom']['required_proof']}",
            "",
            "## Tiny Rotation",
            "",
            f"- Case/XY: `{report['tiny_rotation']['case_id']}` `{report['tiny_rotation']['xy']}`",
            f"- Classification: `{report['tiny_rotation']['classification']}`",
            f"- Closest sampler float: `{report['tiny_rotation']['closest_sampler_float']}`",
            f"- Closest sampler floor u8: `{report['tiny_rotation']['closest_sampler_floor_u8']}`",
            f"- Windows final u8: `{report['tiny_rotation']['windows_final_u8']}`",
            f"- Required proof: {report['tiny_rotation']['required_proof']}",
            "",
            "## Inner",
            "",
            f"- Classification: `{report['inner']['classification']}`",
            f"- Best by mean sum: `{report['inner']['best_by_mean_sum']}`",
            f"- Exact candidates: `{report['inner']['exact_candidates']}`",
            f"- Required proof: {report['inner']['required_proof']}",
            "",
            "| Candidate | Mean sum | Max max | Improved | Worsened | Exact |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in report["inner"]["top_candidates"]:
        lines.append(
            f"| `{row['candidate']}` | {float(row['mean_sum']):.6f} | {row['max_max']} | "
            f"{row['improved_cases']} | {row['worsened_cases']} | {row['exact_count']} |"
        )
    lines.extend(["", "## Static Scatter Facts", ""])
    for key, value in report["inner"]["static_facts"].items():
        lines.append(f"- {key}: `{value}`")
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
