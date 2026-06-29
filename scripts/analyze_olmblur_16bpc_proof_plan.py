#!/usr/bin/env python3
"""Generate the next-proof plan for OLMBlur 16bpc."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORD_AUDIT = ROOT / "refs" / "conformance" / "olmblur_16bpc_word_delta_audit_20260628.json"
DEFAULT_WRITER_CONTRACT = ROOT / "refs" / "conformance" / "olmblur_16bpc_writer_contract_audit_20260629.json"
DEFAULT_OUT_DIR = ROOT / "refs" / "reports" / "olmblur_16bpc_proof_plan_20260629"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--word-audit-json", type=Path, default=DEFAULT_WORD_AUDIT)
    parser.add_argument("--writer-contract-json", type=Path, default=DEFAULT_WRITER_CONTRACT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sample_for_delta(case: dict[str, Any], delta_value: int) -> dict[str, Any] | None:
    for row in case.get("samples", []):
        deltas = row.get("delta_reference_minus_candidate") or []
        if delta_value in deltas:
            return row
    return None


def build_report(word_audit: dict[str, Any], writer_contract: dict[str, Any]) -> dict[str, Any]:
    cases = {row["case_id"]: row for row in word_audit["cases"]}
    case6 = cases["case_0006"]
    case7 = cases["case_0007"]
    pos = sample_for_delta(case6, 2)
    neg = sample_for_delta(case6, -2)
    legacy_major = case7["samples"][0]
    legacy_minor = case7["samples"][1]

    return {
        "kind": "olmblur_16bpc_proof_plan",
        "date": "2026-06-29",
        "decision": "prewriteback-helper-proof-before-writer-swap",
        "nonlegacy_case_0006": {
            "why": "smallest grounded non-legacy 16bpc family; Windows 8bpc trace already proves mismatch before final byte writeback",
            "witness_positive_word": pos,
            "witness_negative_word": neg,
            "required_proof": [
                "final pre-writeback float values at the same 16bpc witness pixel(s)",
                "whether the helper/clamp path changes the float before truncation",
                "whether the Mac AE path differs before store16 or only in store16",
            ],
        },
        "legacy_case_0007": {
            "why": "contains two separate 16bpc phenomena: shared one-word family and localized border/seed anomaly",
            "witness_major_border_seed": legacy_major,
            "witness_minor_one_word": legacy_minor,
            "required_proof": [
                "keep (0,0) border/seed/all-same separate from the ordinary one-word family",
                "confirm whether alternate Legacy writer family alone explains the smaller one-word witness",
                "avoid promoting (0,0) into a general non-legacy store rule",
            ],
        },
        "writer_contract": {
            "mac_nonlegacy_round_expr": writer_contract["mac_source_writer"]["nonlegacy_round_expr"],
            "windows_standard_classification": writer_contract["windows_standard_writer"]["classification"],
            "blind_global_swap_allowed": False,
        },
        "next_actions": [
            "If working Mac-only: add a bounded 16bpc source-side pre-store instrumentation path for case_0006-class witnesses before changing round_blur_value.",
            "If using Windows again later: request typed 16bpc pre-writeback/helper values for a positive and negative case_0006 witness, plus separate Legacy (0,0) all-same/border state.",
            "Do not change the passing 8bpc AE path or make a global nearbyintf replacement from current evidence alone.",
        ],
    }


def render_md(report: dict[str, Any]) -> str:
    c6 = report["nonlegacy_case_0006"]
    c7 = report["legacy_case_0007"]
    pos = c6["witness_positive_word"]
    neg = c6["witness_negative_word"]
    maj = c7["witness_major_border_seed"]
    minor = c7["witness_minor_one_word"]
    lines = [
        "# OLMBlur 16bpc Proof Plan - 2026-06-29",
        "",
        f"- Decision: `{report['decision']}`",
        "",
        "## Non-Legacy Target",
        "",
        f"- Focus case: `case_0006`",
        f"- Why: {c6['why']}",
        f"- Positive one-word witness: `{pos['xy']}` delta `{pos['delta_reference_minus_candidate']}` inferred words `{pos['estimated_word_delta_nonzero_channels']}`",
        f"- Negative one-word witness: `{neg['xy']}` delta `{neg['delta_reference_minus_candidate']}` inferred words `{neg['estimated_word_delta_nonzero_channels']}`",
        "",
        "Required proof:",
    ]
    lines.extend(f"- {item}" for item in c6["required_proof"])
    lines.extend(
        [
            "",
            "## Legacy Target",
            "",
            f"- Focus case: `case_0007`",
            f"- Why: {c7['why']}",
            f"- Major localized witness: `{maj['xy']}` delta `{maj['delta_reference_minus_candidate']}` inferred words `{maj['estimated_word_delta_nonzero_channels']}`",
            f"- Minor shared-family witness: `{minor['xy']}` delta `{minor['delta_reference_minus_candidate']}` inferred words `{minor['estimated_word_delta_nonzero_channels']}`",
            "",
            "Required proof:",
        ]
    )
    lines.extend(f"- {item}" for item in c7["required_proof"])
    lines.extend(
        [
            "",
            "## Writer Contract Context",
            "",
            f"- Mac non-legacy source round expr: `{report['writer_contract']['mac_nonlegacy_round_expr']}`",
            f"- Windows standard writer: `{report['writer_contract']['windows_standard_classification']}`",
            f"- Blind global swap allowed: `{report['writer_contract']['blind_global_swap_allowed']}`",
            "",
            "## Next Actions",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in report["next_actions"])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    word_audit = read_json(args.word_audit_json)
    writer_contract = read_json(args.writer_contract_json)
    report = build_report(word_audit, writer_contract)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "proof_plan.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (args.output_dir / "proof_plan.md").write_text(render_md(report), encoding="utf-8")
    print(f"output_dir={args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
