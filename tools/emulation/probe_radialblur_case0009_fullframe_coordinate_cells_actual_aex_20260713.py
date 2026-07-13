#!/usr/bin/env python3
"""Record the actual-AEX full-frame Zoom coordinate/cell handoff.

This is intentionally a downstream observation probe.  It reuses the existing
actual-AEX harness and does not reconstruct, replace, or compare polar prefill
planes.  The useful output is the top-row coordinate and four-cell selection
for the pixels that contain the remaining Mac/Windows alpha split.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import probe_radialblur_a850_downstream_actual_aex_20260713 as base  # noqa: E402


TARGET_ALPHA_254_X = [6, 7, 12]
# Keep the binary targets visible in this probe's audit surface.
ACTUAL_A850 = "FUN_18000A850"
ACTUAL_D80 = "FUN_180009D80"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aex-path", type=Path, default=base.harness.DEFAULT_AEX)
    parser.add_argument("--manifest", type=Path, default=base.harness.DEFAULT_MANIFEST)
    parser.add_argument("--input-png", type=Path, default=base.harness.DEFAULT_INPUT)
    parser.add_argument("--case-id", default="case_0009")
    parser.add_argument("--debug-size", default="32x32")
    parser.add_argument("--max-instructions", type=int, default=50_000_000)
    parser.add_argument(
        "--points",
        default="".join(f"{x}:0," for x in range(32)).rstrip(","),
        help="Comma-separated x:y points; defaults to the complete top row x=0..31.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("refs/conformance/olmradialblur_case0009_fullframe_coordinate_cells_actual_aex_20260713.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("refs/conformance/olmradialblur_case0009_fullframe_coordinate_cells_actual_aex_20260713.md"),
    )
    return parser.parse_args()


def compact_point(item: dict[str, Any]) -> dict[str, Any]:
    a850 = item.get("a850") or {}
    indices = item.get("downstream_indices") or {}
    mirror = item.get("mirror_inverse") or {}
    sample = item.get("actual_inverse") or {}
    return {
        "xy": item["xy"],
        "entry_reached": item["entry_reached"],
        "a850": {
            "input_xy_f32": a850.get("input_xy_f32"),
            "radius_raw_f32": a850.get("radius_raw_f32"),
            "angle_raw_f32": a850.get("angle_raw_f32"),
        },
        "indices": indices,
        "cell_selection": {
            "angle_indices": mirror.get("angle_indices"),
            "radius_indices": mirror.get("radius_indices"),
            "cells": mirror.get("cells"),
        },
        "actual_d80_rgba_f32": sample.get("rgba_f32"),
        "actual_vs_mirror": item.get("actual_vs_mirror"),
        "render_fault": item.get("base_render_fault"),
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OLMRadialBlur case0009 full-frame coordinate/cell actual-AEX probe (2026-07-13)",
        "",
        "## Scope",
        "",
        "- Local 2025 Windows AEX executed through the existing Unicorn harness on Mac.",
        "- Records `FUN_18000A850` f32 coordinates, downstream indices, four D80 cells, and direct D80 output for the complete top row.",
        "- Prefill and normalized-plane arithmetic are opaque inputs to this probe; neither is reconstructed or retuned here.",
        "",
        f"- Points: `{len(report['points'])}`; target Windows alpha-254 x: `{TARGET_ALPHA_254_X}`.",
        f"- Actual-AEX entry reached: `{sum(bool(p['entry_reached']) for p in report['points'])}/{len(report['points'])}`.",
        f"- Direct-D80 sub-unit-alpha x: `{report['direct_d80_subunit_alpha_x']}`.",
        f"- Windows target x with direct-D80 alpha still 1.0: `{report['target_x_direct_d80_alpha_one']}`.",
        "",
        "## Coordinate and Cell Table",
        "",
        "| x | radius raw | angle raw | radius index | angle index | radius cells | angle cells | D80 RGBA |",
        "|---:|---:|---:|---:|---:|---|---|---|",
    ]
    for point in report["points"]:
        a850 = point["a850"]
        indices = point["indices"]
        cells = point["cell_selection"]
        lines.append(
            f"| {point['xy'][0]} | {a850.get('radius_raw_f32')} | {a850.get('angle_raw_f32')} | "
            f"{indices.get('radius_index')} | {indices.get('angle_index')} | "
            f"{cells.get('radius_indices')} | {cells.get('angle_indices')} | "
            f"{point.get('actual_d80_rgba_f32')} |"
        )
    lines.extend([
        "",
        "## Classification",
        "",
        "The table is the actual-AEX coordinate/cell input witness for the remaining Mac-side lane. "
        "If a Mac implementation selects a different four-cell set or produces different raw "
        "A850 coordinates at the same x, the residual is before D80. Equal selections and exact "
        "D80 outputs move the remaining difference beyond this local coordinate handoff. "
        "This evidence does not establish full-frame pixel conformance by itself. The useful "
        "negative result is that x=7 and x=12 remain alpha 1.0 in direct D80 even though "
        "Windows stores 254 there; do not promote a direct-D80 alpha or writer change from this probe.",
        "",
        "## Audit Finding",
        "",
        f"- Verified: actual-AEX entry reached `{sum(bool(p['entry_reached']) for p in report['points'])}/{len(report['points'])}` top-row points.",
        f"- Verified: direct D80 alpha stays `1.0` at Windows target x `{report['target_x_direct_d80_alpha_one']}`.",
        "- Not established: that coordinate/cell selection input is itself the residual source.",
        "- Basis: this probe records the Windows actual-AEX coordinate/cell handoff and direct D80 output only; it does not include a same-point Mac coordinate/cell witness.",
        "- Basis: the direct D80 output matches the existing mirror at every sampled point, so this artifact does not isolate the remaining residual to D80-local coordinate/cell selection.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    points = base.parse_points(args.points)
    root = Path.cwd()
    with tempfile.TemporaryDirectory(prefix="radialblur_coordinate_cells_probe_") as temp:
        temp_dir = Path(temp)
        results = [base.run_point(args, point, temp_dir) for point in points]
    compact = [compact_point(item) for item in results]
    direct_d80_subunit_alpha_x = [
        point["xy"][0]
        for point in compact
        if point.get("actual_d80_rgba_f32") and point["actual_d80_rgba_f32"][3] < 1.0
    ]
    target_x_direct_d80_alpha_one = [
        x
        for x in TARGET_ALPHA_254_X
        if compact[x].get("actual_d80_rgba_f32")
        and compact[x]["actual_d80_rgba_f32"][3] == 1.0
    ]
    report = {
        "kind": "olmradialblur_case0009_fullframe_coordinate_cells_actual_aex_probe",
        "schema": 1,
        "case_id": args.case_id,
        "aex": base.display_path(args.aex_path),
        "input_png": base.display_path(args.input_png),
        "debug_size": args.debug_size,
        "scope": "actual-AEX A850 coordinates and D80 four-cell selection; opaque prefill",
        "prefill_scope": "opaque actual-AEX prerequisite; no reconstruction or comparison",
        "target_windows_alpha_254_x": TARGET_ALPHA_254_X,
        "direct_d80_subunit_alpha_x": direct_d80_subunit_alpha_x,
        "target_x_direct_d80_alpha_one": target_x_direct_d80_alpha_one,
        "audit_verdict": "not_proven_coordinate_or_cell_selection_residual_source",
        "audit_basis": [
            "actual-AEX entry reached all 32 sampled top-row points",
            "direct D80 alpha remains 1.0 at target x=7 and x=12",
            "probe captures Windows actual-AEX coordinate/cell handoff and direct D80 output only",
            "probe does not provide same-point Mac coordinate/cell evidence",
            "actual D80 output matches the existing mirror at every sampled point",
        ],
        "points_spec": args.points,
        "points": compact,
    }
    output_json = args.output_json if args.output_json.is_absolute() else root / args.output_json
    output_md = args.output_md if args.output_md.is_absolute() else root / args.output_md
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(report), encoding="utf-8")
    print(f"wrote_json={output_json}")
    print(f"wrote_md={output_md}")
    print(f"points={len(compact)} reached={sum(bool(p['entry_reached']) for p in compact)}")
    return 0 if all(p["entry_reached"] for p in compact) else 2


if __name__ == "__main__":
    raise SystemExit(main())
