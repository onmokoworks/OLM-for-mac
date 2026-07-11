#!/usr/bin/env python3
"""Freeze the current OLMBlur closeout gate across case_0006 / case_0007."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CASE0006_CONTRACT_JSON = ROOT / "refs/conformance/olmblur_case0006_current_aex_export_contract_audit_20260701.json"
CASE0006_PROVENANCE_JSON = ROOT / "refs/conformance/olmblur_case0006_reference_provenance_audit_20260701.json"
CASE0007_HALFSTEP_JSON = ROOT / "refs/conformance/olmblur_case0007_halfstep_family_audit_20260701.json"
SOURCE_CANDIDATES_JSON = ROOT / "refs/conformance/olmblur_source_candidates_audit_20260701.json"
OUT_JSON = ROOT / "refs/conformance/olmblur_closeout_gate_audit_20260701.json"
OUT_MD = ROOT / "refs/conformance/olmblur_closeout_gate_audit_20260701.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case0006-contract-json", type=Path, default=CASE0006_CONTRACT_JSON)
    parser.add_argument("--case0006-provenance-json", type=Path, default=CASE0006_PROVENANCE_JSON)
    parser.add_argument("--case0007-halfstep-json", type=Path, default=CASE0007_HALFSTEP_JSON)
    parser.add_argument("--source-candidates-json", type=Path, default=SOURCE_CANDIDATES_JSON)
    parser.add_argument("--output-json", type=Path, default=OUT_JSON)
    parser.add_argument("--output-md", type=Path, default=OUT_MD)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    case0006_contract = read_json(args.case0006_contract_json)
    case0006_provenance = read_json(args.case0006_provenance_json)
    case0007_halfstep = read_json(args.case0007_halfstep_json)
    source_candidates = read_json(args.source_candidates_json)
    case0006_status = str(case0006_contract["decision"]["status"])
    case0006_closed = case0006_status == "outcome-a-current-aex-matches-canonical"
    if case0006_closed:
        case0006_reason = (
            "The non-Legacy 16bpc `case_0006` Windows reference/provenance question is closed as Outcome A: "
            "the imported current-AEX export is byte-identical to the canonical Windows Software reference. "
            "Remaining work, if any, is Mac export / AE-host run provenance before source changes."
        )
        case0006_next = (
            "Preserve current source behavior. If this lane is reopened, audit Mac export / AE-host run "
            "provenance for `case_0006`; only ask Windows again if a new contradictory current-AEX artifact appears."
        )
        closeout_status = "case0006-windows-provenance-closed-and-split-case0007"
    else:
        case0006_reason = (
            "The non-Legacy 16bpc lane `case_0006` is still a provenance/export gate because no same-run Windows "
            "current-AEX export is imported, while Legacy `case_0007` is no longer one unresolved family: its "
            "16bpc witness is already closed as a Windows-side pre-store float delta and only the old normalized "
            "8bpc half-step witness remains open."
        )
        case0006_next = (
            "Preserve current source behavior. Advance only by importing a same-run Windows current-AEX export for "
            "`case_0006`, or by capturing the old normalized 8bpc Windows pre-store float/helper boundary at "
            "`(488,941)` for `case_0007`."
        )
        closeout_status = "provenance-first-case0006-and-split-case0007"

    return {
        "kind": "olmblur_closeout_gate_audit",
        "schema": 1,
        "plugin": "OLMBlur",
        "closeout_status": closeout_status,
        "decision": {
            "status": "do-not-reopen-source-without-two-specific-external-proofs",
            "reason": case0006_reason,
            "next_allowed_action": case0006_next,
        },
        "lanes": [
            {
                "lane": "case_0006_nonlegacy_16bpc",
                "status": case0006_contract["decision"]["status"],
                "reason": case0006_contract["decision"]["reason"],
                "next_step": case0006_contract["decision"]["next_step"],
                "required_external_evidence": case0006_contract["required_windows_payload"],
                "key_points": case0006_contract["witness_points"][:2],
            },
            {
                "lane": "case_0007_legacy_16bpc",
                "status": case0007_halfstep["cases"]["16bpc"]["status"],
                "reason": (
                    "Windows pre-store float is already grounded at `12544.498046875 -> 12544`, so this lane is closed "
                    "as a pre-store float delta rather than an open writer-rule mystery."
                ),
                "next_step": "Keep this lane closed unless contradictory same-run witness evidence appears.",
                "key_points": [
                    {
                        "xy": case0007_halfstep["cases"]["16bpc"]["witness_xy"],
                        "windows_pre_store": case0007_halfstep["cases"]["16bpc"]["windows_witness"]["target_channel_pre_store_float"],
                        "windows_final_word": case0007_halfstep["cases"]["16bpc"]["windows_witness"]["final_word"],
                    }
                ],
            },
            {
                "lane": "case_0007_legacy_8bpc_old_normalized",
                "status": case0007_halfstep["cases"]["8bpc_old_normalized"]["status"],
                "reason": (
                    "The remaining old normalized 8bpc witness stays just below the half-step on the Mac side and has "
                    "no in-tree Windows pre-store float, so it cannot justify a writer or helper rewrite yet."
                ),
                "next_step": case0007_halfstep["decision"]["next_allowed_action"],
                "key_points": [
                    {
                        "xy": case0007_halfstep["cases"]["8bpc_old_normalized"]["low_witness_xy"],
                        "reference_rgba": case0007_halfstep["cases"]["8bpc_old_normalized"]["low_witness"]["reference_rgba"],
                        "candidate_rgba": case0007_halfstep["cases"]["8bpc_old_normalized"]["low_witness"]["candidate_rgba"],
                        "trace": case0007_halfstep["cases"]["8bpc_old_normalized"]["low_witness"]["trace"],
                    }
                ],
            },
        ],
        "source_reopen_order": source_candidates["decision_ladder"],
        "forbidden_actions": [
            *source_candidates["forbidden_actions"],
            "Do not collapse the unresolved OLMBlur work back into one generic 16bpc writer problem.",
            "Do not spend the next Windows round on the already-closed 16bpc Legacy witness unless it is only a debugger control sample.",
        ],
        "supporting_evidence": {
            "case0006_contract_status": case0006_status,
            "case0006_provenance_status": case0006_provenance["outcome"]["status"],
            "case0006_point_pattern": case0006_provenance["overall_point_pattern"],
            "case0007_decision_status": case0007_halfstep["decision"]["status"],
            "source_candidates_status": source_candidates["lane_summary"],
        },
    }


def render_md(report: dict[str, Any]) -> str:
    lines = [
        "# OLMBlur Closeout Gate Audit",
        "",
        f"- Plug-in: `{report['plugin']}`",
        f"- Closeout status: `{report['closeout_status']}`",
        f"- Decision: `{report['decision']['status']}`",
        f"- Reason: {report['decision']['reason']}",
        f"- Next allowed action: {report['decision']['next_allowed_action']}",
        "",
        "## Lanes",
        "",
    ]
    for lane in report["lanes"]:
        lines.append(f"### {lane['lane']}")
        lines.append("")
        lines.append(f"- Status: `{lane['status']}`")
        lines.append(f"- Reason: {lane['reason']}")
        lines.append(f"- Next step: {lane['next_step']}")
        if lane.get("required_external_evidence"):
            lines.append("- Required external evidence:")
            for item in lane["required_external_evidence"]:
                lines.append(f"  - {item}")
        if lane.get("key_points"):
            lines.append("- Key points:")
            for item in lane["key_points"]:
                lines.append(f"  - `{item}`")
        lines.append("")
    lines.extend(["## Source Reopen Order", ""])
    for row in report["source_reopen_order"]:
        lines.append(f"{row['step']}. {row['condition']} -> {row['action']}")
    lines.extend(["", "## Forbidden Actions", ""])
    for row in report["forbidden_actions"]:
        lines.append(f"- {row}")
    lines.extend(
        [
            "",
            "## Supporting Evidence",
            "",
            f"- case_0006 provenance status: `{report['supporting_evidence']['case0006_provenance_status']}`",
            f"- case_0006 point pattern: `{report['supporting_evidence']['case0006_point_pattern']}`",
            f"- case_0007 decision status: `{report['supporting_evidence']['case0007_decision_status']}`",
            f"- source-candidates status: `{report['supporting_evidence']['source_candidates_status']}`",
            "",
        ]
    )
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
    print(f"decision={report['decision']['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
