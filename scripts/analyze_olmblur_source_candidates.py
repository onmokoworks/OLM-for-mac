#!/usr/bin/env python3
"""Freeze the current source-side decision ladder for OLMBlur unresolved lanes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE_CPP = ROOT / "mac/OLMBlur/OLMBlur.cpp"
CASE0006_PROVENANCE_JSON = ROOT / "refs/conformance/olmblur_case0006_reference_provenance_audit_20260701.json"
CASE0007_HALFSTEP_JSON = ROOT / "refs/conformance/olmblur_case0007_halfstep_family_audit_20260701.json"
OUT_JSON = ROOT / "refs/conformance/olmblur_source_candidates_audit_20260701.json"
OUT_MD = ROOT / "refs/conformance/olmblur_source_candidates_audit_20260701.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-cpp", type=Path, default=SOURCE_CPP)
    parser.add_argument("--case0006-provenance-json", type=Path, default=CASE0006_PROVENANCE_JSON)
    parser.add_argument("--case0007-halfstep-json", type=Path, default=CASE0007_HALFSTEP_JSON)
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
            "site": "store16_nonlegacy_writer_boundary",
            "function": "round_blur_value / store16",
            "line": find_line(lines, "return legacy ? floorf(v + 0.5f) : nearbyintf(v);"),
            "why_still_live": (
                "This is only the first source reopen point if a future same-run Windows export or witness explicitly "
                "contradicts the current case_0006 provenance reading and says helper/pre-store match while final stored words differ."
            ),
            "allowed_change_shape": "non-Legacy 16bpc writer-only contradiction only",
        },
        {
            "rank": 2,
            "site": "nonlegacy_helper_accumulation",
            "function": "blur_1d_horizontal / blur_1d_vertical",
            "line": find_line(lines, "static void blur_1d_horizontal("),
            "why_still_live": (
                "Reopen the non-Legacy helpers only if a future Windows witness disproves the current provenance freeze "
                "and shows the decisive mismatch already exists before the 16bpc writer boundary."
            ),
            "allowed_change_shape": "case_0006 helper-local contradiction only; no broad kernel retune",
        },
        {
            "rank": 3,
            "site": "legacy_carry_prev_horizontal_vertical",
            "function": "legacy_blur_1d_horizontal / legacy_blur_1d_vertical",
            "line": find_line(lines, "float carryPrevR = -1.0f, carryPrevG = -1.0f, carryPrevB = -1.0f;"),
            "why_still_live": (
                "The old normalized 8bpc case_0007 witness is still open, but only as a separate pre-store-float lane. "
                "The normalized 16bpc witness is already resolved as a Windows-side pre-store float delta."
            ),
            "allowed_change_shape": "old normalized 8bpc witness only; keep 16bpc Legacy witness closed",
        },
    ]


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    case0006 = read_json(args.case0006_provenance_json)
    case0007 = read_json(args.case0007_halfstep_json)
    lines = args.source_cpp.read_text(encoding="utf-8").splitlines()
    sites = build_candidate_sites(lines)

    return {
        "kind": "olmblur_source_candidates_audit",
        "schema": 1,
        "source_cpp": str(args.source_cpp.relative_to(ROOT)),
        "lane_summary": {
            "case0006_status": case0006["outcome"]["status"],
            "case0007_status": case0007["decision"]["status"],
            "case0006_recommended_action": case0006["outcome"]["recommended_action"],
            "case0007_next_allowed_action": case0007["decision"]["next_allowed_action"],
        },
        "non_source_gates": [
            {
                "lane": "case_0006_nonlegacy_16bpc",
                "required_before_source_patch": "Same-run Windows current-AEX export or witness that contradicts the current provenance/export reading.",
                "why": case0006["outcome"]["reason"],
            },
            {
                "lane": "case_0007_legacy_8bpc_old_normalized",
                "required_before_source_patch": "Windows pre-store float/helper boundary at `(488,941)`.",
                "why": case0007["decision"]["reason"],
            },
        ],
        "source_candidates": sites,
        "decision_ladder": [
            {
                "step": 1,
                "condition": "If no same-run Windows current-AEX export/witness contradicts case_0006 provenance",
                "action": "Do not patch OLMBlur source for case_0006; keep the lane in provenance/export classification.",
            },
            {
                "step": 2,
                "condition": "If Windows shows case_0006 helper/pre-store already match but final stored words differ",
                "action": "Reopen only the non-Legacy 16bpc writer boundary (`round_blur_value` / `store16`).",
            },
            {
                "step": 3,
                "condition": "If Windows shows case_0006 mismatch already exists before final store",
                "action": "Only then reopen non-Legacy helper accumulation in `blur_1d_horizontal` / `blur_1d_vertical`.",
            },
            {
                "step": 4,
                "condition": "If case_0007 advances again",
                "action": "Keep Legacy split by bit depth: 16bpc remains closed, only the old normalized 8bpc witness may reopen carry-prev/helper logic.",
            },
        ],
        "forbidden_actions": [
            "Do not promote a blind global `nearbyint -> floor05` writer swap from the current OLMBlur evidence.",
            "Do not mix case_0006 provenance/export uncertainty with the resolved 16bpc Legacy case_0007 witness.",
            "Do not reopen the retired Legacy `(0,0)` blocker or broad kernel tuning from these lanes.",
        ],
    }


def render_md(report: dict[str, Any]) -> str:
    lines = [
        "# OLMBlur Source-Candidates Audit",
        "",
        f"- Source: `{report['source_cpp']}`",
        f"- case_0006 status: `{report['lane_summary']['case0006_status']}`",
        f"- case_0007 status: `{report['lane_summary']['case0007_status']}`",
        "",
        "## Non-Source Gates",
        "",
    ]
    for row in report["non_source_gates"]:
        lines.append(f"- `{row['lane']}`")
        lines.append(f"  - Required before source patch: {row['required_before_source_patch']}")
        lines.append(f"  - Why: {row['why']}")
    lines.extend(["", "## Source Candidates", "", "| Rank | Site | Function | Line | Why live | Allowed change shape |", "| --- | --- | --- | ---: | --- | --- |"])
    for row in report["source_candidates"]:
        lines.append(
            f"| {row['rank']} | `{row['site']}` | `{row['function']}` | `{row['line']}` | {row['why_still_live']} | {row['allowed_change_shape']} |"
        )
    lines.extend(["", "## Decision Ladder", ""])
    for row in report["decision_ladder"]:
        lines.append(f"{row['step']}. {row['condition']} -> {row['action']}")
    lines.extend(["", "## Forbidden Actions", ""])
    for row in report["forbidden_actions"]:
        lines.append(f"- {row}")
    lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    report = build_report(args)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_md(report), encoding="utf-8")
    print(f"report_json={args.output_json}")
    print(f"report_md={args.output_md}")
    print(f"decision={report['lane_summary']['case0006_status']} / {report['lane_summary']['case0007_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
