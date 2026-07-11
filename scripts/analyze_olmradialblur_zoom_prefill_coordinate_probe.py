#!/usr/bin/env python3
"""Probe source-polar prefill coordinates around RadialBlur Zoom case_0009.

The final-sample probe rejected weight/sum precision as a standalone
explanation. This script asks the next narrower question: do the final-polar
cells around the Windows alpha=254 row contain nearby sub-one source alpha
cells that a small coordinate/cell-set difference could select?

It is analysis-only. It does not render output images or change the CLI.
"""

from __future__ import annotations

import argparse
import json
import math
import struct
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "refs" / "win_references" / "20260604_olm" / "OLMRadialBlur"
LOCUS_JSON = ROOT / "refs" / "conformance" / "olmradialblur_zoom_case0009_quantize_locus_20260709.json"
DEFAULT_JSON = ROOT / "refs" / "conformance" / "olmradialblur_zoom_case0009_prefill_coordinate_probe_20260709.json"
DEFAULT_MD = ROOT / "refs" / "conformance" / "olmradialblur_zoom_case0009_prefill_coordinate_probe_20260709.md"
TARGET_ALPHA254 = {6, 7, 12}
CONTROL_X = {5, 8, 9, 10, 11, 13}


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", float(value)))[0]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-id", default="case_0009")
    parser.add_argument("--locus-json", type=Path, default=LOCUS_JSON)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_MD)
    return parser.parse_args()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_case(case_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest = read_json(REFERENCE_DIR / "reference_manifest.json")
    for case in manifest["cases"]:
        if case.get("id") == case_id:
            return manifest, case
    raise RuntimeError(f"case not found: {case_id}")


def params_from_case(case: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    group = "root"
    effect = case["effects"][0]
    for param in effect.get("params", []):
        name = param.get("name") or ""
        if name == "Outer Blur":
            group = "outer"
            continue
        if name == "Inner Blur":
            group = "inner"
            continue
        if name == "Ellipse":
            group = "ellipse"
            continue
        if name == "Noise Parameters":
            group = "noise"
            continue
        if param.get("value") is None:
            continue
        key = name.lower().replace(" ", "_")
        if group in {"outer", "inner"} and name in {"Strength", "Offset Mode", "Offset", "Edge Fade"}:
            key = f"{group}_{key}"
        elif group == "noise" and name == "Offset":
            key = "noise_offset"
        out[key] = param["value"]
    return out


def bilinear_alpha_repeat_f32(alpha: np.ndarray, x: float, y: float) -> dict[str, Any]:
    h, w = alpha.shape
    xi = int(x)
    yi = int(y)
    fx = f32(x - float(xi))
    fy = f32(y - float(yi))
    x0 = max(0, min(w - 1, xi))
    x1 = max(0, min(w - 1, xi + 1))
    y0 = max(0, min(h - 1, yi))
    y1 = max(0, min(h - 1, yi + 1))
    w00 = f32(f32(1.0 - fx) * f32(1.0 - fy))
    w10 = f32(f32(1.0 - fy) * fx)
    w01 = f32(f32(1.0 - fx) * fy)
    w11 = f32(fy * fx)
    terms = [
        f32(w00 * float(alpha[y0, x0])),
        f32(w10 * float(alpha[y0, x1])),
        f32(w01 * float(alpha[y1, x0])),
        f32(w11 * float(alpha[y1, x1])),
    ]
    grouped = f32(f32(terms[0] + terms[1]) + f32(terms[2] + terms[3]))
    alpha_sum_f32 = 0.0
    for term in terms:
        # Match cli/OLMRadialBlur/main.cpp sample_rgba_aex_alpha:
        # alpha_sum_f32 = static_cast<float>(alpha_sum_f32 + alpha_weight_f32)
        alpha_sum_f32 = f32(alpha_sum_f32 + term)
    return {
        "alpha": alpha_sum_f32,
        "alpha_grouped_f32": grouped,
        "xy0": [x0, y0],
        "xy1": [x1, y1],
        "fx": fx,
        "fy": fy,
        "weights": [w00, w10, w01, w11],
        "source_alphas": [
            float(alpha[y0, x0]),
            float(alpha[y0, x1]),
            float(alpha[y1, x0]),
            float(alpha[y1, x1]),
        ],
    }


def source_xy_for_cell(
    ai: int,
    ri: int,
    min_r: int,
    step_rad: float,
    ratio: float,
    cx: float,
    cy: float,
    base_angle: float,
    mode: str,
) -> tuple[float, float]:
    cos_a = math.cos(base_angle)
    sin_a = math.sin(base_angle)
    if mode == "cpp-double":
        theta = float(ai) * step_rad
        r = float(min_r + ri)
        sx0 = r * math.cos(theta)
        sy0 = r * math.sin(theta) * ratio
        return f32(cx + cos_a * sx0 - sin_a * sy0), f32(cy + sin_a * sx0 + cos_a * sy0)
    if mode == "cpp-aex-float":
        theta_f = f32(f32(ai) * f32(step_rad))
        cos_t_f = f32(math.cos(theta_f))
        sin_t_f = f32(math.sin(theta_f))
        radius_f = f32(min_r + ri)
        sx0 = f32(radius_f * cos_t_f)
        sy0 = f32(f32(radius_f * sin_t_f) * f32(ratio))
        sx = f32(f32(f32(cos_a) * sx0) - f32(f32(sin_a) * sy0) + f32(cx))
        sy = f32(f32(f32(sin_a) * sx0) + f32(f32(cos_a) * sy0) + f32(cy))
        return sx, sy
    if mode == "python-prefill-f32":
        angle = f32(float(ai) * f32(step_rad))
        cos_v = f32(math.cos(angle))
        sin_v = f32(math.sin(angle))
        radius = float(min_r + ri)
        radius_x = f32(radius * cos_v)
        radius_y = f32(f32(radius * sin_v) * f32(ratio))
        sx = f32(f32(f32(cos_a) * radius_x) - f32(f32(sin_a) * radius_y) + f32(cx))
        sy = f32(f32(f32(sin_a) * radius_x) + f32(f32(cos_a) * radius_y) + f32(cy))
        return sx, sy
    raise ValueError(f"unknown mode: {mode}")


def geometry(manifest: dict[str, Any], case: dict[str, Any], params: dict[str, Any]) -> dict[str, Any]:
    image = Image.open(REFERENCE_DIR / case["before_effects_frame"]).convert("RGBA")
    w, h = image.size
    comp = case.get("comp") or manifest.get("comp") or {}
    comp_w = float(comp.get("width") or w)
    comp_h = float(comp.get("height") or h)
    center = params.get("center") or [comp_w * 0.5, comp_h * 0.5]
    cx = float(center[0]) * (w / comp_w)
    cy = float(center[1]) * (h / comp_h)
    ratio = float(params.get("ratio") or 1.0)
    base_angle = math.radians(float(params.get("angle") or 0.0))
    quality = float(params.get("quality") or 5.0)
    step_rad = math.radians(1.0 / quality if quality > 0 else 0.2)
    angular_count = int(360.0 / (1.0 / quality if quality > 0 else 0.2))
    min_dx = 0.0 if 0.0 <= cx < w else abs(cx if cx < 0.0 else cx - w)
    min_dy = 0.0 if 0.0 <= cy < h else abs(cy if cy < 0.0 else cy - h)
    max_dx = max(cx, w - cx) if 0.0 <= cx < w else (w - cx if cx < 0.0 else cx)
    max_dy = max(cy, h - cy) if 0.0 <= cy < h else (h - cy if cy < 0.0 else cy)
    min_r = max(0, int(math.sqrt(min_dx * min_dx + min_dy * min_dy) / ratio) - 2)
    max_r = int(math.sqrt(max_dx * max_dx + max_dy * max_dy)) + 2
    return {
        "image": image,
        "width": w,
        "height": h,
        "cx": cx,
        "cy": cy,
        "ratio": ratio,
        "base_angle": base_angle,
        "step_rad": step_rad,
        "angular_count": angular_count,
        "min_r": min_r,
        "max_r": max_r,
        "radius_count": max_r - min_r + 1,
    }


def cell_ids(point: dict[str, Any], angular_count: int, radius_count: int) -> list[list[int]]:
    radius_index = float(point["radius_index"])
    angle_index = float(point["angle_index"])
    ri0 = max(0, min(radius_count - 1, int(math.floor(radius_index))))
    ri1 = max(0, min(radius_count - 1, ri0 + 1))
    ai0 = int(math.floor(angle_index)) % angular_count
    ai1 = (ai0 + 1) % angular_count
    return [[ai0, ri0], [ai0, ri1], [ai1, ri0], [ai1, ri1]]


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    manifest, case = load_case(args.case_id)
    params = params_from_case(case)
    geom = geometry(manifest, case, params)
    alpha = np.asarray(geom["image"], dtype=np.uint8)[..., 3].astype(np.float32) / 255.0
    locus = read_json(args.locus_json)
    polar_rows = {row["x"]: row for row in locus["variants"]["polar_alpha"]["row"]}
    xs = sorted(TARGET_ALPHA254 | CONTROL_X)
    modes = ["cpp-double", "cpp-aex-float", "python-prefill-f32"]
    points: list[dict[str, Any]] = []
    for x in xs:
        row = polar_rows[x]
        cells = cell_ids(row, geom["angular_count"], geom["radius_count"])
        current_set: list[dict[str, Any]] = []
        nearby_subone: list[dict[str, Any]] = []
        for ai, ri in cells:
            mode_samples = {}
            for mode in modes:
                sx, sy = source_xy_for_cell(
                    ai,
                    ri,
                    geom["min_r"],
                    geom["step_rad"],
                    geom["ratio"],
                    geom["cx"],
                    geom["cy"],
                    geom["base_angle"],
                    mode,
                )
                mode_samples[mode] = {"src_xy": [sx, sy], **bilinear_alpha_repeat_f32(alpha, sx, sy)}
            current_set.append({"cell": [ai, ri], "samples": mode_samples})
        seen = set()
        for ai, ri in cells:
            for dai in (-1, 0, 1):
                for dri in (-1, 0, 1):
                    nai = (ai + dai) % geom["angular_count"]
                    nri = max(0, min(geom["radius_count"] - 1, ri + dri))
                    key = (nai, nri)
                    if key in seen:
                        continue
                    seen.add(key)
                    sx, sy = source_xy_for_cell(
                        nai,
                        nri,
                        geom["min_r"],
                        geom["step_rad"],
                        geom["ratio"],
                        geom["cx"],
                        geom["cy"],
                        geom["base_angle"],
                        "python-prefill-f32",
                    )
                    sample = bilinear_alpha_repeat_f32(alpha, sx, sy)
                    if sample["alpha"] < 0.99999999:
                        nearby_subone.append(
                            {
                                "cell": [nai, nri],
                                "delta_from_any_current_cell": [dai, dri],
                                "src_xy": [sx, sy],
                                "alpha": sample["alpha"],
                            }
                        )
        points.append(
            {
                "x": x,
                "target": x in TARGET_ALPHA254,
                "reference": row["reference"],
                "current_polar_alpha": row["alpha_float"],
                "current_cell_alpha": row["cell_alpha"],
                "final_cells": cells,
                "current_cell_source_samples": current_set,
                "nearby_subone_python_prefill_cells": sorted(nearby_subone, key=lambda item: item["alpha"])[:12],
            }
        )
    return {
        "kind": "olmradialblur_zoom_case0009_prefill_coordinate_probe",
        "schema": 1,
        "case_id": args.case_id,
        "source_locus": str(args.locus_json),
        "geometry": {
            key: geom[key]
            for key in ("width", "height", "cx", "cy", "ratio", "step_rad", "angular_count", "min_r", "max_r", "radius_count")
        },
        "target_alpha254": sorted(TARGET_ALPHA254),
        "control_x": sorted(CONTROL_X),
        "points": points,
        "interpretation": (
            "The known sub-one polar cells are reproduced by C++'s repeat-raw-f32 sampler "
            "operation order, not by input alpha itself. x=7 still has all current final cells "
            "at alpha 1.0, so the remaining local candidate is not late quantization but a "
            "sampled cell-set/coordinate difference that would select a sub-one repeat-sampler "
            "cell, or a Windows final-plane cell capture."
        ),
    }


def render_md(report: dict[str, Any]) -> str:
    lines = [
        "# OLMRadialBlur Zoom Prefill Coordinate Probe",
        "",
        f"- Case: `{report['case_id']}`",
        f"- Target Windows alpha=254 x positions: `{report['target_alpha254']}`",
        f"- Control x positions: `{report['control_x']}`",
        "",
        "## Point Summary",
        "",
        "| x | target | ref | final cells | current cell alpha | nearby sub-one cells |",
        "| ---: | --- | --- | --- | --- | --- |",
    ]
    for point in report["points"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(point["x"]),
                    "`yes`" if point["target"] else "`control`",
                    f"`{point['reference']}`",
                    f"`{point['final_cells']}`",
                    f"`{point['current_cell_alpha']}`",
                    f"`{point['nearby_subone_python_prefill_cells'][:4]}`",
                ]
            )
            + " |"
        )
    lines.extend(["", "## Target Cell Source Samples", ""])
    for point in report["points"]:
        if not point["target"]:
            continue
        lines.append(f"### x={point['x']}")
        for cell in point["current_cell_source_samples"]:
            lines.append(f"- cell `{cell['cell']}`")
            for mode, sample in cell["samples"].items():
                lines.append(f"  - `{mode}` src=`{sample['src_xy']}` alpha=`{sample['alpha']}`")
        lines.append("")
    lines.extend(["## Interpretation", "", report["interpretation"], ""])
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    report = build_report(args)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_md(report), encoding="utf-8")
    print(f"report_json={args.output_json}")
    print(f"report_md={args.output_md}")
    x7 = next(point for point in report["points"] if point["x"] == 7)
    print(f"x7_current_cell_alpha={x7['current_cell_alpha']}")
    print(f"x7_nearby_subone_count={len(x7['nearby_subone_python_prefill_cells'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
