#!/usr/bin/env python3
"""Freeze the current OLMKiraKira hotspot provenance split."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]

MAC_WITNESS_JSON = ROOT / "refs/conformance/olmkirakira_compose_boundary_mac_witness_20260630.json"
WINDOWS_COMPARE_JSON = (
    ROOT / "refs/reports/runtime_trace_comparisons/olmkirakira_hotspot_compose_writeback_witness_20260701.json"
)
CANDIDATE_PNG = (
    ROOT
    / "refs/reports/olmkirakira_remeasure_20260624_bt709_software/candidate/"
    / "kirakira_single_ray_20260606__software__fr24__kk_vertical_len50_brightness1_strength100.png"
)
REFERENCE_PNG = (
    ROOT
    / "refs/reports/olmkirakira_remeasure_20260624_bt709_software/reference/"
    / "kirakira_single_ray_20260606__software__fr24__kk_vertical_len50_brightness1_strength100.png"
)
OUT_JSON = ROOT / "refs/conformance/olmkirakira_reference_provenance_audit_20260701.json"
OUT_MD = ROOT / "refs/conformance/olmkirakira_reference_provenance_audit_20260701.md"

CASE_ID = "kk_vertical_len50_brightness1_strength100"
HOTSPOT_XY = (934, 118)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mac-witness-json", type=Path, default=MAC_WITNESS_JSON)
    parser.add_argument("--windows-compare-json", type=Path, default=WINDOWS_COMPARE_JSON)
    parser.add_argument("--candidate-png", type=Path, default=CANDIDATE_PNG)
    parser.add_argument("--reference-png", type=Path, default=REFERENCE_PNG)
    parser.add_argument("--output-json", type=Path, default=OUT_JSON)
    parser.add_argument("--output-md", type=Path, default=OUT_MD)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_rgba(path: Path, xy: tuple[int, int]) -> list[int]:
    with Image.open(path).convert("RGBA") as image:
        return [int(v) for v in image.getpixel(xy)]


def witness_point(report: dict[str, Any], xy: str) -> dict[str, Any]:
    return report["points"][xy]


def compose_sample(report: dict[str, Any], label: str) -> dict[str, Any]:
    for row in report["windows"]["merge_mode_1_compose"]["sample_inputs_outputs"]:
        if row["label"] == label:
            return row
    raise KeyError(f"missing compose sample {label}")


def hotspot_row(report: dict[str, Any], label: str) -> dict[str, Any]:
    for row in report["windows"]["residual_hotspot"]:
        if row["label"] == label:
            return row
    raise KeyError(f"missing hotspot row {label}")


def delta(lhs: list[int], rhs: list[int]) -> list[int]:
    return [int(a) - int(b) for a, b in zip(lhs, rhs)]


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    mac_witness = witness_point(read_json(args.mac_witness_json), "934,118")
    compare = read_json(args.windows_compare_json)
    windows_hotspot = compose_sample(compare, "hotspot")
    residual_hotspot = hotspot_row(compare, "primary_vertical_case_hotspot")

    candidate_rgba = read_rgba(args.candidate_png, HOTSPOT_XY)
    reference_rgba = read_rgba(args.reference_png, HOTSPOT_XY)
    mac_witness_rgba = list(mac_witness["out_u8"])
    windows_traced_rgba = list(windows_hotspot["final_writeback_or_png_rgba"])

    role_matrix = {
        "canonical_reference_vs_windows_traced": reference_rgba == windows_traced_rgba,
        "canonical_reference_vs_mac_witness": reference_rgba == mac_witness_rgba,
        "canonical_reference_vs_archived_candidate": reference_rgba == candidate_rgba,
        "windows_traced_vs_mac_witness": windows_traced_rgba == mac_witness_rgba,
        "windows_traced_vs_archived_candidate": windows_traced_rgba == candidate_rgba,
        "mac_witness_vs_archived_candidate": mac_witness_rgba == candidate_rgba,
    }

    return {
        "kind": "olmkirakira_reference_provenance_audit",
        "schema": 1,
        "case_id": CASE_ID,
        "hotspot_xy": [HOTSPOT_XY[0], HOTSPOT_XY[1]],
        "artifacts": {
            "canonical_reference_png": {
                "path": str(args.reference_png.relative_to(ROOT)),
                "hotspot_rgba": reference_rgba,
            },
            "archived_bt709_candidate_png": {
                "path": str(args.candidate_png.relative_to(ROOT)),
                "hotspot_rgba": candidate_rgba,
            },
            "current_mac_compose_witness": {
                "path": str(args.mac_witness_json.relative_to(ROOT)),
                "hotspot_rgba": mac_witness_rgba,
                "compose_rgba_float": mac_witness["out_prequantized_rgba_float"],
            },
            "windows_traced_hotspot": {
                "path": str(args.windows_compare_json.relative_to(ROOT)),
                "hotspot_rgba": windows_traced_rgba,
                "compose_rgba_float": windows_hotspot["composed_rgba_float"],
                "glow_after_opacity_rgba_float": windows_hotspot["glow_after_opacity_rgba_float"],
                "residual_hotspot_row": residual_hotspot,
            },
        },
        "pairwise_deltas": {
            "archived_candidate_minus_reference": delta(candidate_rgba, reference_rgba),
            "windows_traced_minus_reference": delta(windows_traced_rgba, reference_rgba),
            "mac_witness_minus_reference": delta(mac_witness_rgba, reference_rgba),
            "archived_candidate_minus_windows_traced": delta(candidate_rgba, windows_traced_rgba),
        },
        "role_matrix": role_matrix,
        "decision": {
            "status": "reference-export-or-witness-placement-pending",
            "reason": (
                "The primary hotspot now has three distinct in-tree facts: the canonical Windows Software "
                "reference PNG is 131, the current Mac compose-boundary witness and answered Windows traced "
                "writeback both say 144, and the archived BT.709 candidate PNG says 145. That means the "
                "remaining KiraKira hotspot is not a single compose-math disagreement; it is at least partly "
                "a provenance/export/witness-placement lane."
            ),
            "forbidden_action": (
                "Do not retune BT.709, boxFilter, ray-helper, FUN_18114fd90 aggregation, merge-mode-1 screen "
                "compose, or final quantization from these hotspot artifacts alone."
            ),
            "next_allowed_action": (
                "Treat the traced hotspot algorithm lane as matched through current writeback, and only spend "
                "further effort here on canonical reference provenance, same-run export comparison, witness "
                "placement validation, or endgame control coverage."
            ),
        },
    }


def render_md(report: dict[str, Any]) -> str:
    art = report["artifacts"]
    role = report["role_matrix"]
    delta_rows = report["pairwise_deltas"]
    decision = report["decision"]
    lines = [
        "# OLMKiraKira Reference Provenance Audit",
        "",
        f"- Case: `{report['case_id']}`",
        f"- Hotspot: `{tuple(report['hotspot_xy'])}`",
        f"- Decision: `{decision['status']}`",
        f"- Reason: {decision['reason']}",
        f"- Forbidden action: {decision['forbidden_action']}",
        f"- Next allowed action: {decision['next_allowed_action']}",
        "",
        "## Artifact Hotspot Values",
        "",
        f"- canonical Windows reference PNG: `{art['canonical_reference_png']['hotspot_rgba']}`",
        f"- archived BT.709 candidate PNG: `{art['archived_bt709_candidate_png']['hotspot_rgba']}`",
        f"- current Mac compose-boundary witness: `{art['current_mac_compose_witness']['hotspot_rgba']}`",
        f"- answered Windows traced hotspot: `{art['windows_traced_hotspot']['hotspot_rgba']}`",
        "",
        "## Pairwise Deltas",
        "",
        f"- archived candidate minus canonical reference: `{delta_rows['archived_candidate_minus_reference']}`",
        f"- windows traced minus canonical reference: `{delta_rows['windows_traced_minus_reference']}`",
        f"- current Mac witness minus canonical reference: `{delta_rows['mac_witness_minus_reference']}`",
        f"- archived candidate minus windows traced: `{delta_rows['archived_candidate_minus_windows_traced']}`",
        "",
        "## Role Matrix",
        "",
        f"- canonical reference == windows traced: `{role['canonical_reference_vs_windows_traced']}`",
        f"- canonical reference == current Mac witness: `{role['canonical_reference_vs_mac_witness']}`",
        f"- canonical reference == archived candidate: `{role['canonical_reference_vs_archived_candidate']}`",
        f"- windows traced == current Mac witness: `{role['windows_traced_vs_mac_witness']}`",
        f"- windows traced == archived candidate: `{role['windows_traced_vs_archived_candidate']}`",
        f"- current Mac witness == archived candidate: `{role['mac_witness_vs_archived_candidate']}`",
        "",
        "## Reading",
        "",
        "- The canonical reference PNG is not the same artifact as the current traced/writeback-aligned hotspot.",
        "- The archived BT.709 candidate PNG is also not the same artifact as the current traced/writeback-aligned hotspot; it is one count brighter at the witness pixel.",
        "- So this lane should stay parked away from compose retuning. The current evidence supports provenance/export or witness-placement investigation first.",
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
