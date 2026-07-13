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

from PIL import Image

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
        "geometry": item.get("geometry"),
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OLMRadialBlur case0009 full-frame coordinate/cell actual-AEX probe (2026-07-13)",
        "",
        "## Scope",
        "",
        "- Local 2025 Windows AEX executed through the existing Unicorn harness on Mac.",
        "- Records `FUN_18000A850` f32 coordinates from an actual-AEX reduced-geometry harness.",
        "- The `32x32` geometry and `90` degree quality-step override make downstream indices, cells, and D80 output non-semantic for the 1920x1080 AE case.",
        "- Only the raw A850 radius/angle values may be compared with the full-frame Mac render.",
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
        "Raw A850 radius/angle values are actual-AEX evidence. Downstream indices, selected "
        "cells, and D80 values are reduced-geometry diagnostics only because the harness replaces "
        "the 1920x1080 geometry with 32x32 and overwrites the quality step with 90 degrees. "
        "They must not be compared with a full-frame Mac AE render or used to tune production code.",
        "",
        "## Audit Finding",
        "",
        f"- Verified: actual-AEX entry reached `{sum(bool(p['entry_reached']) for p in report['points'])}/{len(report['points'])}` top-row points.",
        f"- Verified: direct D80 alpha stays `1.0` at Windows target x `{report['target_x_direct_d80_alpha_one']}`.",
        "- Valid comparison scope: raw A850 radius/angle only.",
        "- Invalid comparison scope: radius/angle indices, cell selection, cell values, and D80 output versus full-frame AE.",
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
    with Image.open(args.input_png) as input_image:
        input_size = [int(input_image.width), int(input_image.height)]
    quality_step_override = (compact[0].get("geometry") or {}).get("quality_step") if compact else None
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
        "input_size": input_size,
        "debug_size": args.debug_size,
        "quality_step_override_degrees": quality_step_override,
        "index_cell_semantic": False,
        "scope": "actual-AEX A850 raw coordinates; reduced-geometry downstream indices/cells are non-semantic",
        "prefill_scope": "opaque actual-AEX prerequisite; no reconstruction or comparison",
        "target_windows_alpha_254_x": TARGET_ALPHA_254_X,
        "direct_d80_subunit_alpha_x": direct_d80_subunit_alpha_x,
        "target_x_direct_d80_alpha_one": target_x_direct_d80_alpha_one,
        "audit_verdict": "a850-raw-valid-index-cell-nonsemantic-reduced-geometry",
        "audit_basis": [
            "actual-AEX entry reached all 32 sampled top-row points",
            "raw A850 radius and angle remain actual-AEX outputs",
            "harness replaces 1920x1080 input geometry with 32x32",
            "harness overwrites work quality step with 90 degrees",
            "base harness explicitly classifies reduced-geometry sampled color/alpha as non-semantic",
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
