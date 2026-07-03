#!/usr/bin/env python3
"""Freeze the stable inverse-sampler anchor that the current anchor-watch request starts from."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SAME_ROW_JSON = ROOT / "refs/conformance/olmradialblur_tiny_rotation_same_row_audit_20260701.json"
SOURCE_POLAR_JSON = ROOT / "refs/conformance/olmradialblur_tiny_rotation_source_polar_probe_20260701.json"
ACTIVE_CONTRACT_MD = ROOT / "refs/conformance/olmradialblur_tiny_rotation_anchor_watch_followup_contract_20260701.md"
HISTORICAL_CONTRACT_MD = ROOT / "refs/conformance/olmradialblur_tiny_rotation_backstep_followup_contract_20260701.md"
OUT_JSON = ROOT / "refs/conformance/olmradialblur_tiny_rotation_backstep_anchor_audit_20260701.json"
OUT_MD = ROOT / "refs/conformance/olmradialblur_tiny_rotation_backstep_anchor_audit_20260701.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--same-row-json", type=Path, default=SAME_ROW_JSON)
    parser.add_argument("--source-polar-json", type=Path, default=SOURCE_POLAR_JSON)
    parser.add_argument("--active-contract-md", type=Path, default=ACTIVE_CONTRACT_MD)
    parser.add_argument("--historical-contract-md", type=Path, default=HISTORICAL_CONTRACT_MD)
    parser.add_argument("--output-json", type=Path, default=OUT_JSON)
    parser.add_argument("--output-md", type=Path, default=OUT_MD)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def witness_row(payload: dict[str, Any], *, x: int, y: int) -> dict[str, Any]:
    for row in payload.get("rows", []):
        if row.get("xy") == [x, y]:
            return row
    raise KeyError(f"missing witness row ({x},{y})")


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    same_row = read_json(args.same_row_json)
    source_polar = read_json(args.source_polar_json)
    witness = witness_row(same_row, x=1614, y=6)
    direct_cells = source_polar["direct_source_cells"]
    dominant_cluster = source_polar["dominant_local_positive_cluster"]
    strongest_positive = source_polar["strongest_positive"]
    strongest_negative = source_polar["strongest_negative"]
    same_row_black = all(cell["src_cell_rgba"][:3] == [0.0, 0.0, 0.0] for cell in witness["cells"])
    supporting_rows = sorted({int(cell["radius_row"]) for cell in witness["cells"]})
    dominant_rows = sorted({int(row["xy"][1]) for row in dominant_cluster})
    dominant_angles = sorted({int(row["xy"][0]) for row in dominant_cluster})

    report = {
        "kind": "olmradialblur_tiny_rotation_backstep_anchor_audit",
        "schema": 1,
        "case_id": "case_0010",
        "witness_xy": [1614, 6],
        "inverse_sampler_anchor": {
            "angle_index": witness["angle_index"],
            "radius_index": witness["radius_index"],
            "indices": witness["indices"],
            "sample_u8": witness["sample_u8"],
            "validity_alpha_u8": witness["validity_alpha_u8"],
            "witness_sample_rgba": source_polar["witness_sample_rgba"],
            "witness_sample_u8": source_polar["witness_sample_u8"],
        },
        "direct_support": {
            "supporting_rows": supporting_rows,
            "same_row_direct_source_cells_all_black": same_row_black,
            "cells": witness["cells"],
            "direct_source_cells": direct_cells,
        },
        "upstream_candidate_family": {
            "dominant_local_positive_cluster": dominant_cluster,
            "dominant_cluster_rows": dominant_rows,
            "dominant_cluster_angles": dominant_angles,
            "strongest_positive": strongest_positive,
            "strongest_negative": strongest_negative,
        },
        "backstep_reading": {
            "status": "anchor-stable-upstream-branch-still-missing",
            "reason": (
                "The anchored inverse sampler for `case_0010 (1614,6)` is locally stable: "
                "it samples rows 844/845 at angle indices 1603/1604, all direct source cells are black, "
                "and the current witness remains near-black before final U8 conversion. The nearest positive "
                "family that could still plausibly explain the missing white lobe sits one row above at row 843 "
                "around angles 1601..1602, so the next Windows proof still needs the first upstream branch that "
                "decides how that family is included, substituted, or discarded before final inverse sampling."
            ),
            "why_anchor_is_useful": (
                "This anchor removes ambiguity about the last observed sample point. The remaining uncertainty is "
                "not where the final bilinear sample lands, but which earlier branch populates or promotes the RGB "
                "feeding that sample."
            ),
            "next_windows_hook": (
                "Start from the reliable inverse-sampler hit near `(angle=1603.83948, radius=844.317505)` for "
                "`case_0010 (1614,6)`, then step backward until one typed upstream branch/value explains how the "
                "pixel can move from near-black to the final white Windows byte."
            ),
        },
        "wanted_chain": ["+0xf252", "+0xf250", "+0xe"],
        "active_contract_path": str(args.active_contract_md.relative_to(ROOT)),
        "historical_predecessor_contract_path": str(args.historical_contract_md.relative_to(ROOT)),
    }
    return report


def render_md(report: dict[str, Any]) -> str:
    anchor = report["inverse_sampler_anchor"]
    lines = [
        "# OLMRadialBlur tiny Rotation Backstep Anchor Audit",
        "",
        f"- Case: `{report['case_id']}`",
        f"- Witness: `{tuple(report['witness_xy'])}`",
        f"- Active contract: `{report['active_contract_path']}`",
        f"- Historical predecessor contract: `{report['historical_predecessor_contract_path']}`",
        f"- Decision: `{report['backstep_reading']['status']}`",
        f"- Reason: {report['backstep_reading']['reason']}",
        f"- Why this anchor matters: {report['backstep_reading']['why_anchor_is_useful']}",
        "",
        "## Inverse-Sampler Anchor",
        "",
        f"- angle_index: `{anchor['angle_index']}`",
        f"- radius_index: `{anchor['radius_index']}`",
        f"- indices: `{anchor['indices']}`",
        f"- witness sample RGBA: `{anchor['witness_sample_rgba']}`",
        f"- witness sample U8: `{anchor['witness_sample_u8']}`",
        f"- current output U8: `{anchor['sample_u8']}`",
        f"- validity alpha U8: `{anchor['validity_alpha_u8']}`",
        "",
        "## Direct Support At The Anchor",
        "",
        f"- supporting rows: `{report['direct_support']['supporting_rows']}`",
        f"- same-row direct source cells all black: `{report['direct_support']['same_row_direct_source_cells_all_black']}`",
        "",
        "| Cell | radius_row | same_row_source_taps | cell_rgb | src_cell_rgba |",
        "| --- | ---: | --- | --- | --- |",
    ]
    for cell in report["direct_support"]["cells"]:
        lines.append(
            f"| `{cell['cell']}` | `{cell['radius_row']}` | `{cell['same_row_source_taps']}` | "
            f"`{cell['cell_rgb']}` | `{cell['src_cell_rgba']}` |"
        )
    lines.extend(
        [
            "",
            "## Nearest Upstream Positive Family",
            "",
            f"- dominant cluster rows: `{report['upstream_candidate_family']['dominant_cluster_rows']}`",
            f"- dominant cluster angles: `{report['upstream_candidate_family']['dominant_cluster_angles']}`",
            f"- dominant local positive cluster: `{report['upstream_candidate_family']['dominant_local_positive_cluster']}`",
            f"- strongest positive cells: `{report['upstream_candidate_family']['strongest_positive']}`",
            f"- strongest negative cells: `{report['upstream_candidate_family']['strongest_negative']}`",
            "",
            "## Windows Anchor-Watch Ask",
            "",
            f"- {report['backstep_reading']['next_windows_hook']}",
            f"- Preferred retained caller-side chain: `{report['wanted_chain']}`",
            "",
            "## Reading",
            "",
            "- The final sample point is no longer the ambiguous part.",
            "- The witness is already near-black at the anchored inverse-sampler point, with direct source support on rows 844/845 only.",
            "- The closest positive family lives one row above at row 843, so the remaining question is the upstream inclusion/substitute path, not final byte conversion.",
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
    print(f"decision={report['backstep_reading']['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
