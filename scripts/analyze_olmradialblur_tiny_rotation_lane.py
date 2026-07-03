#!/usr/bin/env python3
"""Consolidate the current OLMRadialBlur tiny-Rotation hard lane."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

SAME_ROW_JSON = ROOT / "refs/conformance/olmradialblur_tiny_rotation_same_row_audit_20260701.json"
SOURCE_POLAR_JSON = ROOT / "refs/conformance/olmradialblur_tiny_rotation_source_polar_probe_20260701.json"
ROW_COUPLING_JSON = ROOT / "refs/conformance/olmradialblur_tiny_rotation_row_coupling_probe_20260701.json"
PROP_VALIDITY_JSON = ROOT / "refs/conformance/olmradialblur_outer_propagated_validity_probe_20260701.json"
PENDING_JSON = ROOT / "refs/reports/pending_runtime_trace_packages.json"
OUT_JSON = ROOT / "refs/conformance/olmradialblur_tiny_rotation_lane_audit_20260701.json"
OUT_MD = ROOT / "refs/conformance/olmradialblur_tiny_rotation_lane_audit_20260701.md"
REQUEST_ID = "olmradialblur_tiny_rotation_anchor_context_watch_followup_20260702"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--same-row-json", type=Path, default=SAME_ROW_JSON)
    parser.add_argument("--source-polar-json", type=Path, default=SOURCE_POLAR_JSON)
    parser.add_argument("--row-coupling-json", type=Path, default=ROW_COUPLING_JSON)
    parser.add_argument("--propagated-validity-json", type=Path, default=PROP_VALIDITY_JSON)
    parser.add_argument("--pending-json", type=Path, default=PENDING_JSON)
    parser.add_argument("--output-json", type=Path, default=OUT_JSON)
    parser.add_argument("--output-md", type=Path, default=OUT_MD)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def pending_row(report: dict[str, Any]) -> dict[str, Any]:
    for row in report["requests"]:
        if row.get("request_id") == REQUEST_ID:
            return row
    raise KeyError(f"missing pending request {REQUEST_ID}")


def point_by_xy(points: list[dict[str, Any]], x: int, y: int) -> dict[str, Any]:
    for point in points:
        xy = point.get("xy")
        if isinstance(xy, list) and len(xy) == 2 and int(xy[0]) == x and int(xy[1]) == y:
            return point
    raise KeyError(f"missing point ({x},{y})")


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    same_row = read_json(args.same_row_json)
    source_polar = read_json(args.source_polar_json)
    row_coupling = read_json(args.row_coupling_json)
    prop_validity = read_json(args.propagated_validity_json)
    pending = pending_row(read_json(args.pending_json))

    witness = point_by_xy(same_row["rows"], 1614, 6)
    same_row_cells = witness["cells"]
    direct_source_zero = all(cell["src_cell_rgba"][:3] == [0.0, 0.0, 0.0] for cell in same_row_cells)
    row843_cluster = source_polar["dominant_local_positive_cluster"]
    reference_bright_count = int(row_coupling["reference"]["bright_count"])
    baseline_variant = next(v for v in row_coupling["variants"] if v["name"] == "baseline")
    brightless_variants = all(int(v["bright_count"]) == 0 for v in row_coupling["variants"])

    report = {
        "kind": "olmradialblur_tiny_rotation_lane_audit",
        "schema": 1,
        "case_id": "case_0010",
        "witness_xy": [1614, 6],
        "current_candidate_rgba": baseline_variant["witness_rgba"],
        "windows_reference_rgba": row_coupling["reference"]["witness_rgba"],
        "same_row_structure": {
            "row_length": same_row["row_length"],
            "row_weights": same_row["row_weights"],
            "witness_same_row_cells": same_row_cells,
            "direct_source_cells_all_black": direct_source_zero,
        },
        "source_polar_structure": {
            "witness_sample_rgba": source_polar["witness_sample_rgba"],
            "witness_sample_u8": source_polar["witness_sample_u8"],
            "dominant_local_positive_cluster": row843_cluster,
            "strongest_positive": source_polar["strongest_positive"],
            "strongest_negative": source_polar["strongest_negative"],
            "direct_source_cells": source_polar["direct_source_cells"],
        },
        "row_coupling_probe": {
            "reference_bright_count": reference_bright_count,
            "reference_patch_r": row_coupling["reference"]["patch_r"],
            "variants": row_coupling["variants"],
            "all_variants_keep_bright_count_zero": brightless_variants,
        },
        "propagated_validity_probe": {
            "reading": prop_validity["reading"]["tiny_rotation"],
        },
        "pending_windows_followup": {
            "request_id": pending["request_id"],
            "status": pending["status"],
            "package": pending["package"],
            "acceptance_note": pending["acceptance_note"],
            "stop_condition": pending["stop_condition"],
        },
        "decision": {
            "status": "tiny-rotation-pending-upstream-rgb-or-substitute-proof",
            "reason": (
                "The current Mac branch already rejects final-byte tuning and validity-only explanations. "
                "At the max witness `(1614,6)`, all four direct same-row source cells are black, the surviving "
                "cell_rgb values are small or negative, the dominant local positive source-polar family sits one "
                "row above at row 843 / angles 1601..1602, and the tested row-coupled surrogates still leave the "
                "reference bright-lobe count at 17 versus 0 locally. So the remaining lane stays upstream in "
                "neighboring-row contribution ownership or an AEX substitute/fallback branch before final inverse sampling."
            ),
            "forbidden_action": (
                "Do not promote global validity-alpha policy, final byte conversion, broad row-coupling tweaks, "
                "or a plain same-row support rewrite from the current local evidence alone."
            ),
            "next_windows_requirement": (
                "Use the stable `+0x4eb9/+0x4ec8` anchor only as the entry point; the required witness is now the "
                "first retained promotion branch with stack/pointer or watchpoint context around the sampled cell "
                "and neighboring rows."
            ),
        },
    }
    return report


def render_md(report: dict[str, Any]) -> str:
    lines = [
        "# OLMRadialBlur tiny Rotation Lane Audit",
        "",
        f"- Case: `{report['case_id']}`",
        f"- Witness: `{tuple(report['witness_xy'])}`",
        f"- Current candidate RGBA: `{report['current_candidate_rgba']}`",
        f"- Windows reference RGBA: `{report['windows_reference_rgba']}`",
        f"- Decision: `{report['decision']['status']}`",
        f"- Reason: {report['decision']['reason']}",
        f"- Forbidden action: {report['decision']['forbidden_action']}",
        f"- Next Windows requirement: {report['decision']['next_windows_requirement']}",
        "",
        "## Same-Row Boundary",
        "",
        f"- row_length: `{report['same_row_structure']['row_length']}`",
        f"- row_weights: `{report['same_row_structure']['row_weights']}`",
        f"- direct same-row source cells all black: `{report['same_row_structure']['direct_source_cells_all_black']}`",
        "",
        "| Cell | cell_rgb | src_cell_rgba |",
        "| --- | --- | --- |",
    ]
    for cell in report["same_row_structure"]["witness_same_row_cells"]:
        lines.append(f"| `{cell['cell']}` | `{cell['cell_rgb']}` | `{cell['src_cell_rgba']}` |")
    lines.extend(
        [
            "",
            "## Source-Polar Boundary",
            "",
            f"- witness sample RGBA: `{report['source_polar_structure']['witness_sample_rgba']}`",
            f"- witness sample U8: `{report['source_polar_structure']['witness_sample_u8']}`",
            f"- dominant local positive cluster: `{report['source_polar_structure']['dominant_local_positive_cluster']}`",
            f"- strongest negative source-polar cells: `{report['source_polar_structure']['strongest_negative']}`",
            "",
            "## Row-Coupling Rejection",
            "",
            f"- reference bright count in 25x25 window: `{report['row_coupling_probe']['reference_bright_count']}`",
            f"- all tested variants keep local bright count at zero: `{report['row_coupling_probe']['all_variants_keep_bright_count_zero']}`",
            "",
            "| Variant | mean_diff | bright_count | witness_rgba |",
            "| --- | ---: | ---: | --- |",
        ]
    )
    for row in report["row_coupling_probe"]["variants"]:
        diff = row["diff"]
        lines.append(
            f"| `{row['label']}` | `{diff['mean_diff']:.9f}` | `{row['bright_count']}` | `{row['witness_rgba']}` |"
        )
    lines.extend(
        [
            "",
            "## Propagated-Validity Rejection",
            "",
            f"- {report['propagated_validity_probe']['reading']}",
            "",
            "## Pending Windows Follow-up",
            "",
            f"- Request: `{report['pending_windows_followup']['request_id']}`",
            f"- Status: `{report['pending_windows_followup']['status']}`",
            f"- Package: `{report['pending_windows_followup']['package']}`",
            f"- Acceptance: `{report['pending_windows_followup']['acceptance_note']}`",
            f"- Stop condition: {report['pending_windows_followup']['stop_condition']}",
            "",
            "## Reading",
            "",
            "- The witness is no longer well described as an alpha problem or a final-sample byte problem.",
            "- A plain same-row support model cannot generate the missing white lobe from the four direct source cells now visible in the local dump.",
            "- The surviving local clue is the positive source-polar family one row above the witness rows, but the current row-coupled surrogates are still too weak to promote into the port.",
            "- The next acceptable move still requires the pending Windows typed upstream RGB/substitute-path witness.",
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
