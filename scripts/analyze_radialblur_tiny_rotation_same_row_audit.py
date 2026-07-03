#!/usr/bin/env python3
"""Audit the current tiny-Rotation witness against same-row source usage."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DEBUG_JSON = ROOT / "handoff" / "ae_pixel_validation_20260618" / "requests" / "ae_single_radialblur_case_0010_probe_20260701" / "radialblur_debug_points.json"
DEFAULT_MANIFEST_JSON = ROOT / "handoff" / "ae_pixel_validation_20260618" / "requests" / "ae_single_radialblur_case_0010_probe_20260701" / "reference_manifest.json"
DEFAULT_OUTPUT_JSON = ROOT / "refs" / "conformance" / "olmradialblur_tiny_rotation_same_row_audit_20260701.json"
DEFAULT_OUTPUT_MD = ROOT / "refs" / "conformance" / "olmradialblur_tiny_rotation_same_row_audit_20260701.md"

POINTS = [(1612, 6), (1613, 6), (1614, 5), (1614, 6), (1614, 7)]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--debug-json", type=Path, default=DEFAULT_DEBUG_JSON)
    parser.add_argument("--manifest-json", type=Path, default=DEFAULT_MANIFEST_JSON)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUTPUT_MD)
    return parser.parse_args()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def find_param(effect: dict[str, Any], match_name: str) -> Any:
    for param in effect.get("params", []):
        if isinstance(param, dict) and param.get("match_name") == match_name:
            return param.get("value")
    raise KeyError(match_name)


def rotation_effective_length(strength: int, offset_mode: int, dynamic_offset: int) -> int:
    span = strength
    if offset_mode == 1:
        span = strength + dynamic_offset
    elif offset_mode == 2:
        span = max(strength, dynamic_offset)
    elif offset_mode == 3:
        span = dynamic_offset
    return max(0, min(span - 1, 3000))


def rotation_gaussian_weights(length: int) -> list[float]:
    if length <= 1:
        return [1.0]
    table_len = 30000
    denom = float(table_len) * float(table_len) * 2.0 * 0.111111119389534 + 1.0e-5
    inv_denom = 1.0 / denom
    idx_scale = table_len // length
    weights = [1.0] * length
    for i in range(1, length):
        table_index = int(float(i) * float(idx_scale))
        weights[i] = math.exp(-(table_index * table_index) * inv_denom)
    return weights


def same_row_source_taps(ai: int, angular_count: int, row_length: int) -> list[int]:
    return [((ai - (k % angular_count)) + angular_count) % angular_count for k in range(row_length)]


def build_report(debug: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    effect = manifest["cases"][0]["effects"][0]
    outer_strength = int(find_param(effect, "OLM RadialBlur-0004"))
    outer_offset_mode = int(find_param(effect, "OLM RadialBlur-0028"))
    outer_offset = int(find_param(effect, "OLM RadialBlur-0029"))
    quality = float(find_param(effect, "OLM RadialBlur-0015"))
    angular_count = int(360.0 / (1.0 / quality))
    dynamic_offset = 0 if outer_offset == 0 else outer_offset
    row_length = rotation_effective_length(outer_strength, outer_offset_mode, dynamic_offset)
    weights = rotation_gaussian_weights(row_length)

    points_by_xy = {
        (int(point["x"]), int(point["y"])): point
        for point in debug["points"]
        if point.get("kind") == "rotation"
    }
    rows: list[dict[str, Any]] = []
    for xy in POINTS:
        point = points_by_xy.get(xy)
        if point is None:
            continue
        x0, x1, y0, y1 = [int(v) for v in point["indices"]]
        cell_rows = [
            {"cell": "x0y0", "angle_index": x0, "radius_row": y0},
            {"cell": "x1y0", "angle_index": x1, "radius_row": y0},
            {"cell": "x0y1", "angle_index": x0, "radius_row": y1},
            {"cell": "x1y1", "angle_index": x1, "radius_row": y1},
        ]
        for cell, rgb, src in zip(cell_rows, point["cell_rgb"], point["src_cell_rgba"]):
            cell["same_row_source_taps"] = same_row_source_taps(cell["angle_index"], angular_count, row_length)
            cell["cell_rgb"] = rgb
            cell["src_cell_rgba"] = src
        rows.append(
            {
                "xy": list(xy),
                "sample_u8": point["sample_u8"],
                "validity_alpha_u8": point["validity_alpha_u8"],
                "radius_index": point["radius_index"],
                "angle_index": point["angle_index"],
                "indices": point["indices"],
                "cells": cell_rows,
            }
        )

    return {
        "kind": "olmradialblur_tiny_rotation_same_row_audit",
        "schema": 1,
        "debug_json": str(DEFAULT_DEBUG_JSON),
        "manifest_json": str(DEFAULT_MANIFEST_JSON),
        "case_id": "case_0010",
        "witness_xy": [1614, 6],
        "outer_strength": outer_strength,
        "outer_offset_mode": outer_offset_mode,
        "outer_offset": outer_offset,
        "quality": quality,
        "angular_count": angular_count,
        "row_length": row_length,
        "row_weights": weights,
        "rows": rows,
        "conclusion": {
            "summary": (
                "The current Mac Rotation path can only populate each blurred witness cell from "
                "same-radius-row angular taps. Around the tiny-Rotation witness, those direct "
                "source cells are all black while the surviving blurred cell_rgb values stay small "
                "or negative, so the missing bright lobe cannot come from those exact same-row "
                "direct source cells."
            ),
            "implication": (
                "This tightens the next proof boundary to upstream neighbor/contribution geometry, "
                "AEX prepass/scatter structure, or a substitute/fallback branch that the current "
                "same-row convolution does not model."
            ),
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OLMRadialBlur tiny Rotation Same-Row Audit",
        "",
        "Date: 2026-07-01",
        "",
        "Goal:",
        "",
        "- Tie the live Mac AE witness dump to the current `RenderRotation8` structure.",
        "- Make explicit which same-row angular source taps the current port can use for the",
        "  tiny-Rotation witness neighborhood.",
        "",
        "Current structural facts:",
        "",
        f"- `outer_strength={report['outer_strength']}`",
        f"- `outer_offset_mode={report['outer_offset_mode']}`",
        f"- `outer_offset={report['outer_offset']}`",
        f"- `quality={report['quality']}` -> `angular_count={report['angular_count']}`",
        f"- `row_length={report['row_length']}`",
        f"- `row_weights={report['row_weights']}`",
        "",
        "This means the current small-length Rotation path uses only same-radius-row angular taps",
        "for each blurred polar cell. There is no cross-row contribution in this branch.",
        "",
        "## Witness neighborhood",
        "",
        "| XY | sample_u8 | validity_alpha_u8 | indices | cell | same-row taps | cell_rgb | src_cell_rgba |",
        "| - | - | -: | - | - | - | - | - |",
    ]
    for row in report["rows"]:
        xy = tuple(row["xy"])
        first = True
        for cell in row["cells"]:
            prefix = (
                f"| `{xy}` | `{row['sample_u8']}` | {row['validity_alpha_u8']} | `{row['indices']}` | "
                if first
                else "|  |  |  |  | "
            )
            lines.append(
                prefix
                + f"`{cell['cell']}` | `{cell['same_row_source_taps']}` | "
                + f"`{cell['cell_rgb']}` | `{cell['src_cell_rgba']}` |"
            )
            first = False
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            report["conclusion"]["summary"],
            "",
            report["conclusion"]["implication"],
            "",
            "- At `(1614,6)`, all four direct `src_cell_rgba` values are black, yet the blurred",
            "  `cell_rgb` family is already small/negative. So the witness is not explained by",
            "  direct-source brightness being present and then masked away later.",
            "- Because the current branch uses only same-row angular taps, it also cannot express",
            "  any AEX rule that depends on neighboring radius rows or a separate substitute path",
            "  before the final inverse sample.",
            "- This does not prove the exact AEX rule yet, but it does make one thing safer:",
            "  broad final-sample validity or writeback tweaks are even less likely to be the real",
            "  fix than the current docs already suggested.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    report = build_report(load_json(args.debug_json), load_json(args.manifest_json))
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.output_md.write_text(render_markdown(report), encoding="utf-8")
    print(f"output_json={args.output_json}")
    print(f"output_md={args.output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
