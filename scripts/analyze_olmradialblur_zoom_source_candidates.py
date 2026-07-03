#!/usr/bin/env python3
"""Freeze the current source-site decision ladder for RadialBlur Zoom caller-collapse."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE_CPP = ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp"
PLANE_DIAG_JSON = ROOT / "refs/conformance/olmradialblur_caller_collapse_plane_diag_20260701.json"
PROP_VALIDITY_JSON = ROOT / "refs/conformance/olmradialblur_outer_propagated_validity_probe_20260701.json"
OUTER_CONTRACT = ROOT / "refs/conformance/olmradialblur_outer_witness_contract_20260701.md"
OUT_JSON = ROOT / "refs/conformance/olmradialblur_zoom_source_candidates_audit_20260701.json"
OUT_MD = ROOT / "refs/conformance/olmradialblur_zoom_source_candidates_audit_20260701.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-cpp", type=Path, default=SOURCE_CPP)
    parser.add_argument("--plane-diag-json", type=Path, default=PLANE_DIAG_JSON)
    parser.add_argument("--propagated-validity-json", type=Path, default=PROP_VALIDITY_JSON)
    parser.add_argument("--outer-contract", type=Path, default=OUTER_CONTRACT)
    parser.add_argument("--output-json", type=Path, default=OUT_JSON)
    parser.add_argument("--output-md", type=Path, default=OUT_MD)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def find_line(lines: list[str], needle: str) -> int:
    for idx, line in enumerate(lines, start=1):
        if needle in line:
            return idx
    raise KeyError(f"missing source needle: {needle}")


def build_candidate_sites(lines: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "rank": 1,
            "site": "zoom_polar_population_and_validity_capture",
            "function": "RenderZoom8",
            "line": find_line(lines, "polar_valid[(size_t)ai * radius_count + ri] = PolarValidSample"),
            "why_still_live": (
                "The remaining Zoom split is no longer RGB or final-byte broad drift; it is the caller-collapse "
                "state between sampler return and final alpha, so source-polar population and preserved-validity capture stay first."
            ),
            "allowed_change_shape": "typed caller-collapse input / preserved-validity capture only",
        },
        {
            "rank": 2,
            "site": "zoom_alpha_accumulation_and_denominator_state",
            "function": "RenderZoom8",
            "line": find_line(lines, "accum_alpha += alpha * weight;"),
            "why_still_live": (
                "Windows already truncates to the stored byte exactly, and the local propagated-validity probe is inert, "
                "so the live question is the alpha coverage denominator or equivalent normalization state before final inverse sampling."
            ),
            "allowed_change_shape": "alpha accumulation / denominator state only; no broad geometry rewrite",
        },
        {
            "rank": 3,
            "site": "zoom_final_inverse_sample_and_u8_writeback",
            "function": "RenderZoom8",
            "line": find_line(lines, "const RadialBlurOuterSampleState outer_state = ComputeRadialBlurOuterSampleState("),
            "why_still_live": (
                "This is second-order only. Reopen it only if a Windows typed witness proves upstream caller-collapse "
                "state already matches while the 254/255 split still appears at final sampling."
            ),
            "allowed_change_shape": "only with explicit Windows contradiction to the current caller-collapse reading",
        },
    ]


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    plane = read_json(args.plane_diag_json)
    prop = read_json(args.propagated_validity_json)
    lines = args.source_cpp.read_text(encoding="utf-8").splitlines()
    sites = build_candidate_sites(lines)

    zoom = plane["zoom_case_0009"]
    max_gap = zoom["row_probe"]["max_alpha_validity_gap"]
    prop_zoom = prop["zoom_case_0009"]

    report = {
        "kind": "olmradialblur_zoom_source_candidates_audit",
        "schema": 1,
        "case_id": "case_0009",
        "witness_xy": zoom["witness_xy"],
        "source_cpp": str(args.source_cpp.relative_to(ROOT)),
        "lane_summary": {
            "current_sample_u8": zoom["witness_sample_u8"],
            "reference_u8": next(row["reference_u8"] for row in zoom["row_probe"]["row"] if row["x"] == zoom["witness_xy"][0]),
            "alpha_u8": zoom["witness_alpha_u8"],
            "validity_alpha_u8": zoom["witness_validity_alpha_u8"],
            "center_gap": next(row["alpha_minus_validity_alpha_u8"] for row in zoom["row_probe"]["row"] if row["x"] == zoom["witness_xy"][0]),
            "largest_gap_x": max_gap["x"],
            "largest_gap": max_gap["gap"],
            "propagated_validity_diff": prop_zoom["stats"],
            "propagated_validity_reading": prop["reading"]["zoom"],
        },
        "source_candidates": sites,
        "decision_ladder": [
            {
                "step": 1,
                "condition": "If Windows typed witness shows the alpha split is already present in caller-collapse inputs",
                "action": "Constrain changes to polar population / preserved-validity capture in RenderZoom8",
            },
            {
                "step": 2,
                "condition": "If Windows proves sampler return is right but the denominator or collapse state differs before final inverse sampling",
                "action": "Constrain changes to alpha accumulation / denominator state only",
            },
            {
                "step": 3,
                "condition": "If Windows shows caller-collapse state already matches but the 254/255 split still appears at final sampling",
                "action": "Only then reopen final inverse-sample / writeback logic",
            },
        ],
        "forbidden_actions": [
            "Do not promote direct use of the current preserved-validity plane as final alpha.",
            "Do not promote a same-kernel propagated-validity plane as the fix.",
            "Do not retune final byte conversion while Windows already matches the stored byte from traced pre-writeback floats.",
        ],
        "outer_contract_path": str(args.outer_contract.relative_to(ROOT)),
    }
    return report


def render_md(report: dict[str, Any]) -> str:
    lines = [
        "# OLMRadialBlur Zoom Source-Candidates Audit",
        "",
        f"- Case: `{report['case_id']}`",
        f"- Witness: `{tuple(report['witness_xy'])}`",
        f"- Source: `{report['source_cpp']}`",
        f"- Current sample_u8: `{report['lane_summary']['current_sample_u8']}`",
        f"- Windows reference_u8: `{report['lane_summary']['reference_u8']}`",
        "",
        "## Lane Facts",
        "",
        f"- center alpha_u8: `{report['lane_summary']['alpha_u8']}`",
        f"- center validity_alpha_u8: `{report['lane_summary']['validity_alpha_u8']}`",
        f"- center gap: `{report['lane_summary']['center_gap']}`",
        f"- largest same-row alpha-validity gap: `x={report['lane_summary']['largest_gap_x']} gap={report['lane_summary']['largest_gap']}`",
        f"- propagated-validity diff: `{report['lane_summary']['propagated_validity_diff']}`",
        f"- propagated-validity reading: {report['lane_summary']['propagated_validity_reading']}",
        "",
        "## Source Candidates",
        "",
        "| Rank | Site | Function | Line | Why live | Allowed change shape |",
        "| --- | --- | --- | ---: | --- | --- |",
    ]
    for row in report["source_candidates"]:
        lines.append(
            f"| {row['rank']} | `{row['site']}` | `{row['function']}` | `{row['line']}` | {row['why_still_live']} | {row['allowed_change_shape']} |"
        )
    lines.extend(
        [
            "",
            "## Decision Ladder",
            "",
        ]
    )
    for row in report["decision_ladder"]:
        lines.append(f"{row['step']}. {row['condition']} -> {row['action']}")
    lines.extend(
        [
            "",
            "## Forbidden Actions",
            "",
        ]
    )
    for row in report["forbidden_actions"]:
        lines.append(f"- {row}")
    lines.extend(
        [
            "",
            "## Contract",
            "",
            f"- Outer witness contract: `{report['outer_contract_path']}`",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    report = build_report(args)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_md.write_text(render_md(report), encoding="utf-8")
    print(f"[ok] wrote {args.output_json}")
    print(f"[ok] wrote {args.output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
