#!/usr/bin/env python3
"""Freeze the current source-side decision ladder for OLMKiraKira."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE_CPP = ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp"
HOTSPOT_AUDIT_JSON = ROOT / "refs/conformance/olmkirakira_hotspot_lane_audit_20260701.json"
PROVENANCE_AUDIT_JSON = ROOT / "refs/conformance/olmkirakira_reference_provenance_audit_20260701.json"
OUT_JSON = ROOT / "refs/conformance/olmkirakira_source_candidates_audit_20260701.json"
OUT_MD = ROOT / "refs/conformance/olmkirakira_source_candidates_audit_20260701.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-cpp", type=Path, default=SOURCE_CPP)
    parser.add_argument("--hotspot-audit-json", type=Path, default=HOTSPOT_AUDIT_JSON)
    parser.add_argument("--provenance-audit-json", type=Path, default=PROVENANCE_AUDIT_JSON)
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
            "site": "render_typed_merge_mode_1_screen_compose",
            "function": "RenderTyped",
            "line": find_line(lines, "out.r = 1.0f - (1.0f - src.r) * (1.0f - Clamp01(glow[idx].r * glow_a));"),
            "why_still_live": (
                "This is the first in-source place to reopen only if a future same-run export/reference witness "
                "explicitly contradicts the current traced hotspot agreement through compose and sampled writeback."
            ),
            "allowed_change_shape": "single-witness merge-mode-1 compose or writeback boundary only",
        },
        {
            "rank": 2,
            "site": "add_colored_union_glow_aggregation",
            "function": "AddColoredUnion",
            "line": find_line(lines, "glow[i].a = glow[i].a + alpha - glow[i].a * alpha;"),
            "why_still_live": (
                "Aggregation remains second-order only. Reopen it only if a later witness proves the same-run "
                "export disagrees before final compose, not because the canonical reference PNG differs from the traced hotspot."
            ),
            "allowed_change_shape": "typed per-ray aggregation contradiction only; no broad brightness/gain retune",
        },
        {
            "rank": 3,
            "site": "params_setup_highlight_ramp_control_surface",
            "function": "ParamsSetup",
            "line": find_line(lines, "PF_ADD_COLOR(GetStringPtr(StrID_HighlightColor_Param_Name), 255, 255, 255, HIGHLIGHT_COLOR_DISK_ID);"),
            "why_still_live": (
                "The remaining KiraKira work may still need control-surface coverage because Windows manifests expose "
                "ramp/highlight controls. But that is a schema/endgame-coverage lane, not a hotspot compose fix."
            ),
            "allowed_change_shape": "parameter/control-surface coverage only; not a hotspot pixel-math patch",
        },
    ]


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    hotspot = read_json(args.hotspot_audit_json)
    provenance = read_json(args.provenance_audit_json)
    lines = args.source_cpp.read_text(encoding="utf-8").splitlines()
    sites = build_candidate_sites(lines)

    report = {
        "kind": "olmkirakira_source_candidates_audit",
        "schema": 1,
        "case_id": hotspot["case_id"],
        "witness_xy": hotspot["witness_xy"],
        "source_cpp": str(args.source_cpp.relative_to(ROOT)),
        "lane_summary": {
            "hotspot_decision": hotspot["decision"]["status"],
            "provenance_decision": provenance["decision"]["status"],
            "canonical_reference_rgba": provenance["artifacts"]["canonical_reference_png"]["hotspot_rgba"],
            "windows_traced_rgba": provenance["artifacts"]["windows_traced_hotspot"]["hotspot_rgba"],
            "current_mac_witness_rgba": provenance["artifacts"]["current_mac_compose_witness"]["hotspot_rgba"],
            "archived_candidate_rgba": provenance["artifacts"]["archived_bt709_candidate_png"]["hotspot_rgba"],
        },
        "non_source_gate": {
            "required_before_source_patch": (
                "Same-run export or witness-placement evidence that contradicts the current traced hotspot agreement."
            ),
            "why": (
                "The current in-tree facts already split into reference/export provenance or witness-placement: "
                "Windows traced hotspot == current Mac witness == 144, while canonical reference is 131."
            ),
        },
        "source_candidates": sites,
        "decision_ladder": [
            {
                "step": 1,
                "condition": "If no new same-run export/reference contradiction exists",
                "action": "Do not patch OLMKiraKira source for the hotspot lane; keep work in provenance/export or witness-placement validation.",
            },
            {
                "step": 2,
                "condition": "If a future witness says compose/writeback diverges on the same run and same hotspot",
                "action": "Reopen RenderTyped merge-mode-1 screen compose at the hotspot before touching upstream aggregation.",
            },
            {
                "step": 3,
                "condition": "If the future witness proves the mismatch already exists before final compose",
                "action": "Only then reopen AddColoredUnion or upstream per-ray aggregation.",
            },
            {
                "step": 4,
                "condition": "If remaining work is about missing Windows-visible controls rather than the hotspot pixel",
                "action": "Treat highlight/ramp parameters as a separate schema/endgame-coverage lane.",
            },
        ],
        "forbidden_actions": [
            "Do not retune BT.709, boxFilter, ray-helper choreography, or global brightness gain from the current hotspot evidence.",
            "Do not promote a broad final-quantization tweak from the canonical-reference mismatch alone.",
            "Do not treat highlight/ramp control coverage as proof that the hotspot compose math is wrong.",
        ],
    }
    return report


def render_md(report: dict[str, Any]) -> str:
    summary = report["lane_summary"]
    lines = [
        "# OLMKiraKira Source-Candidates Audit",
        "",
        f"- Case: `{report['case_id']}`",
        f"- Witness: `{tuple(report['witness_xy'])}`",
        f"- Source: `{report['source_cpp']}`",
        f"- Hotspot decision: `{summary['hotspot_decision']}`",
        f"- Provenance decision: `{summary['provenance_decision']}`",
        "",
        "## Lane Summary",
        "",
        f"- canonical reference hotspot: `{summary['canonical_reference_rgba']}`",
        f"- windows traced hotspot: `{summary['windows_traced_rgba']}`",
        f"- current Mac witness hotspot: `{summary['current_mac_witness_rgba']}`",
        f"- archived BT.709 candidate hotspot: `{summary['archived_candidate_rgba']}`",
        "",
        "## Non-Source Gate",
        "",
        f"- Required before source patch: {report['non_source_gate']['required_before_source_patch']}",
        f"- Why: {report['non_source_gate']['why']}",
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
    print(f"decision={report['lane_summary']['hotspot_decision']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
