#!/usr/bin/env python3
"""Consolidate the surviving OLMBlur case_0007 half-step family."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASELINE_JSON = ROOT / "refs/conformance/olmblur_current_word_baseline_20260629.json"
WRITER_ONLY_JSON = ROOT / "refs/conformance/olmblur_writer_only_hypothesis_20260630.json"
WINDOWS_16_JSON = ROOT / "refs/conformance/olmblur_olmblur_case_0007_16bpc_345_672_b_witness_intake_20260630.json"
OUT_JSON = ROOT / "refs/conformance/olmblur_case0007_halfstep_family_audit_20260701.json"
OUT_MD = ROOT / "refs/conformance/olmblur_case0007_halfstep_family_audit_20260701.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-json", type=Path, default=BASELINE_JSON)
    parser.add_argument("--writer-only-json", type=Path, default=WRITER_ONLY_JSON)
    parser.add_argument("--windows-16-json", type=Path, default=WINDOWS_16_JSON)
    parser.add_argument("--output-json", type=Path, default=OUT_JSON)
    parser.add_argument("--output-md", type=Path, default=OUT_MD)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def find_case(baseline: dict[str, Any], case_id: str) -> dict[str, Any]:
    for case in baseline["cases"]:
        if case.get("case_id") == case_id:
            return case
    raise KeyError(case_id)


def find_writer_witness(writer: dict[str, Any], case_id: str, xy: tuple[int, int]) -> dict[str, Any]:
    for row in writer["witnesses"]:
        if row.get("case_id") == case_id and row.get("xy") == [xy[0], xy[1]]:
            return row
    raise KeyError((case_id, xy))


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    baseline = read_json(args.baseline_json)
    writer = read_json(args.writer_only_json)
    windows16 = read_json(args.windows_16_json)

    case16 = find_case(baseline, "olmblur__case_0007")
    case8 = find_case(baseline, "case_0007")
    writer16 = find_writer_witness(writer, "olmblur__case_0007", (345, 672))
    writer8_low = find_writer_witness(writer, "case_0007", (488, 941))
    writer8_high = find_writer_witness(writer, "case_0007", (488, 942))

    sample16 = next(sample for sample in case16["samples"] if sample["x"] == 345 and sample["y"] == 672)
    sample8_low = next(sample for sample in case8["samples"] if sample["x"] == 488 and sample["y"] == 941)
    sample8_high = next(sample for sample in case8["samples"] if sample["x"] == 488 and sample["y"] == 942)

    return {
        "kind": "olmblur_case0007_halfstep_family_audit",
        "schema": 1,
        "family": "legacy_last_pixel_half_step",
        "cases": {
            "16bpc": {
                "case_id": "olmblur__case_0007",
                "witness_xy": [345, 672],
                "mac_reference_rgba": sample16["reference"],
                "mac_candidate_rgba": sample16["candidate"],
                "mac_probe": sample16["probe"],
                "writer_only_row": writer16,
                "windows_witness": {
                    "target_channel_pre_store_float": windows16["target_channel_pre_store_float"],
                    "final_word": windows16["final_word"],
                    "summary": windows16["summary"],
                },
                "status": "resolved-as-pre-store-float-delta",
            },
            "8bpc_old_normalized": {
                "case_id": "case_0007",
                "low_witness_xy": [488, 941],
                "high_control_xy": [488, 942],
                "low_witness": {
                    "reference_rgba": sample8_low["reference"],
                    "candidate_rgba": sample8_low["candidate"],
                    "trace": sample8_low["trace"],
                    "writer_only_row": writer8_low,
                },
                "high_control": {
                    "reference_rgba": sample8_high["reference"],
                    "candidate_rgba": sample8_high["candidate"],
                    "trace": sample8_high["trace"],
                    "writer_only_row": writer8_high,
                },
                "status": "still-needs-windows-pre-store-float",
            },
        },
        "decision": {
            "status": "16bpc-resolved-8bpc-still-open-prestore-family",
            "reason": (
                "The surviving Legacy case_0007 family is no longer one undifferentiated residual. "
                "The normalized 16bpc witness at `(345,672)` is already closed as a pre-store float delta: "
                "Mac lands at exactly `12544.5`, while Windows runtime witness says `12544.498046875 -> 12544`. "
                "The old normalized 8bpc witness at `(488,941)` remains below the half-step on the Mac side "
                "(`250.499985`) and is not solved by either local writer rule, so that companion witness still "
                "needs a Windows pre-store float rather than a blind writer rewrite."
            ),
            "forbidden_action": (
                "Do not reopen the retired Legacy `(0,0)` blocker, do not treat case_0007 as proof for a global "
                "writer-rule swap, and do not mix the resolved 16bpc witness with the still-open 8bpc witness."
            ),
            "next_allowed_action": (
                "Keep case_0007 split by bit depth: preserve the 16bpc witness as resolved, and only ask Windows "
                "for the old normalized 8bpc pre-store float/helper boundary at `(488,941)` if this family needs "
                "to move further."
            ),
        },
        "writer_only_conclusion": writer["conclusion"],
    }


def render_md(report: dict[str, Any]) -> str:
    c16 = report["cases"]["16bpc"]
    c8 = report["cases"]["8bpc_old_normalized"]
    d = report["decision"]
    lines = [
        "# OLMBlur case_0007 Half-Step Family Audit",
        "",
        f"- Family: `{report['family']}`",
        f"- Decision: `{d['status']}`",
        f"- Reason: {d['reason']}",
        f"- Forbidden action: {d['forbidden_action']}",
        f"- Next allowed action: {d['next_allowed_action']}",
        "",
        "## 16bpc Witness",
        "",
        f"- XY: `{tuple(c16['witness_xy'])}`",
        f"- Mac reference RGBA: `{c16['mac_reference_rgba']}`",
        f"- Mac candidate RGBA: `{c16['mac_candidate_rgba']}`",
        f"- Mac raw/store note: `{c16['mac_probe']['raw']}` -> stored `{c16['mac_probe']['stored']}`",
        f"- Windows pre-store float: `{c16['windows_witness']['target_channel_pre_store_float']}`",
        f"- Windows final word: `{c16['windows_witness']['final_word']}`",
        f"- Status: `{c16['status']}`",
        "",
        "## 8bpc Old Normalized Witness Pair",
        "",
        f"- Low witness XY: `{tuple(c8['low_witness_xy'])}`",
        f"- Low witness reference/candidate: `{c8['low_witness']['reference_rgba']}` / `{c8['low_witness']['candidate_rgba']}`",
        f"- Low witness trace: `{c8['low_witness']['trace']}`",
        f"- High control XY: `{tuple(c8['high_control_xy'])}`",
        f"- High control reference/candidate: `{c8['high_control']['reference_rgba']}` / `{c8['high_control']['candidate_rgba']}`",
        f"- High control trace: `{c8['high_control']['trace']}`",
        f"- Status: `{c8['status']}`",
        "",
        "## Reading",
        "",
        "- The 16bpc Legacy witness is already resolved as a pre-store float delta before truncation, not a writer-rule mystery.",
        "- The 8bpc old normalized witness is a companion half-step family, but it is still open because the Mac-side raw value is already below 250.5 and no Windows pre-store float is recorded in-tree yet.",
        "- So `case_0007` should stay split by bit depth in future decisions.",
        "",
    ]
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
