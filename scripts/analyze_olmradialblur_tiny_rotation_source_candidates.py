#!/usr/bin/env python3
"""Freeze the current source-site decision ladder for RadialBlur tiny Rotation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE_CPP = ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp"
LANE_AUDIT_JSON = ROOT / "refs/conformance/olmradialblur_tiny_rotation_lane_audit_20260701.json"
SUPPORT_JSON = ROOT / "refs/conformance/olmradialblur_tiny_rotation_support_envelope_20260701.json"
OUT_JSON = ROOT / "refs/conformance/olmradialblur_tiny_rotation_source_candidates_audit_20260701.json"
OUT_MD = ROOT / "refs/conformance/olmradialblur_tiny_rotation_source_candidates_audit_20260701.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-cpp", type=Path, default=SOURCE_CPP)
    parser.add_argument("--lane-audit-json", type=Path, default=LANE_AUDIT_JSON)
    parser.add_argument("--support-json", type=Path, default=SUPPORT_JSON)
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
            "site": "rotation_polar_population_and_validity_capture",
            "function": "RenderRotation8",
            "line": find_line(lines, "polar_valid[(size_t)ri * angular_count + ai] = PolarValidSample"),
            "why_still_live": (
                "The active witness is already black before final inverse sampling, and the local audits "
                "show the surviving bright family lives upstream in source-polar / preserved-validity ownership."
            ),
            "allowed_change_shape": "typed source-polar population or preserved-validity capture only",
        },
        {
            "rank": 2,
            "site": "rotation_scatter_and_neighboring_row_ownership",
            "function": "scatter_row_small / RenderRotation8",
            "line": find_line(lines, "const A_long src_ai = (ai - (A_long)(k % (size_t)angular_count) + angular_count) % angular_count;"),
            "why_still_live": (
                "The row-843 cluster is locally real, but the witness cannot directly see it in the current branch, "
                "so neighboring-row ownership or a substitute/fallback promotion before inverse sampling remains live."
            ),
            "allowed_change_shape": "upstream scatter/substitute-path ownership only; no broad same-row tweak",
        },
        {
            "rank": 3,
            "site": "rotation_final_inverse_sample_and_u8_writeback",
            "function": "RenderRotation8",
            "line": find_line(lines, "out->red = (A_u_char)ClampFloat((float)std::floor(outer_state.final_rgb[0] * 255.0), 0.0f, 255.0f);"),
            "why_still_live": (
                "This is second-order only. Reopen it only if a Windows typed witness proves upstream "
                "population already matches and the decisive split still appears at final sampling."
            ),
            "allowed_change_shape": "only with explicit Windows contradiction to the current upstream reading",
        },
    ]


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    lane = read_json(args.lane_audit_json)
    support = read_json(args.support_json)
    lines = args.source_cpp.read_text(encoding="utf-8").splitlines()
    sites = build_candidate_sites(lines)

    outputs = support["outputs"]
    witness_row = next(row for row in outputs if row["xy"] == [1614, 6])

    report = {
        "kind": "olmradialblur_tiny_rotation_source_candidates_audit",
        "schema": 1,
        "case_id": lane["case_id"],
        "witness_xy": lane["witness_xy"],
        "source_cpp": str(args.source_cpp.relative_to(ROOT)),
        "lane_summary": {
            "decision": lane["decision"]["status"],
            "current_candidate_rgba": lane["current_candidate_rgba"],
            "windows_reference_rgba": lane["windows_reference_rgba"],
            "direct_source_cells_all_black": lane["same_row_structure"]["direct_source_cells_all_black"],
            "reference_bright_count": lane["row_coupling_probe"]["reference_bright_count"],
            "all_variants_keep_bright_count_zero": lane["row_coupling_probe"]["all_variants_keep_bright_count_zero"],
            "witness_direct_cluster_visibility": witness_row["can_directly_see_cluster"],
        },
        "source_candidates": sites,
        "decision_ladder": [
            {
                "step": 1,
                "condition": "If Windows typed witness shows the decisive bright contribution is missing before scatter/normalization",
                "action": "Constrain changes to polar population / preserved-validity capture in RenderRotation8",
            },
            {
                "step": 2,
                "condition": "If Windows proves the bright family exists upstream but is lost in ownership, substitute, or neighboring-row promotion",
                "action": "Constrain changes to scatter/substitute-path ownership before final inverse sampling",
            },
            {
                "step": 3,
                "condition": "If Windows shows upstream population already matches but the split still appears at final sampling",
                "action": "Only then reopen final inverse-sample / writeback logic",
            },
        ],
        "forbidden_actions": [
            "Do not promote a global validity-alpha rewrite from this lane.",
            "Do not promote a same-row-only support tweak from the row-843 cluster evidence alone.",
            "Do not retune final byte conversion while the witness remains black before the proven upstream boundary.",
        ],
        "pending_windows_followup": lane["pending_windows_followup"],
        "windows_requirement": lane["decision"]["next_windows_requirement"],
    }
    return report


def render_md(report: dict[str, Any]) -> str:
    lines = [
        "# OLMRadialBlur tiny Rotation Source-Candidates Audit",
        "",
        f"- Case: `{report['case_id']}`",
        f"- Witness: `{tuple(report['witness_xy'])}`",
        f"- Source: `{report['source_cpp']}`",
        f"- Lane decision: `{report['lane_summary']['decision']}`",
        f"- Current candidate RGBA: `{report['lane_summary']['current_candidate_rgba']}`",
        f"- Windows reference RGBA: `{report['lane_summary']['windows_reference_rgba']}`",
        "",
        "## Lane Facts",
        "",
        f"- direct source cells all black: `{report['lane_summary']['direct_source_cells_all_black']}`",
        f"- witness directly sees row-843 cluster in current branch: `{report['lane_summary']['witness_direct_cluster_visibility']}`",
        f"- reference bright count in local 25x25 window: `{report['lane_summary']['reference_bright_count']}`",
        f"- tested local variants keep bright count zero: `{report['lane_summary']['all_variants_keep_bright_count_zero']}`",
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
    pending = report["pending_windows_followup"]
    lines.extend(
        [
            "",
            "## Pending Windows Follow-up",
            "",
            f"- Request: `{pending['request_id']}`",
            f"- Status: `{pending['status']}`",
            f"- Package: `{pending['package']}`",
            f"- Acceptance: `{pending['acceptance_note']}`",
            f"- Requirement: {report['windows_requirement']}",
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
