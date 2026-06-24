#!/usr/bin/env python3
"""Recompute the OLMRadialBlur Zoom witness against the Windows trace facts."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--reference-dir",
        type=Path,
        default=ROOT / "refs" / "win_references" / "20260604_olm" / "OLMRadialBlur",
    )
    parser.add_argument(
        "--trace-comparison-json",
        type=Path,
        default=ROOT / "refs" / "reports" / "runtime_trace_comparisons" / "olmradialblur_residual_witness_20260624.json",
    )
    parser.add_argument("--case-id", default="case_0009")
    parser.add_argument("--x", type=int, default=6)
    parser.add_argument("--y", type=int, default=0)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-md", type=Path, default=None)
    return parser.parse_args()


def load_radialblur_module() -> Any:
    path = ROOT / "refs" / "scripts" / "olmradialblur_cli.py"
    spec = importlib.util.spec_from_file_location("olmradialblur_cli", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def payload_for_case(reference_dir: Path, case_id: str) -> dict[str, Any]:
    manifest = read_json(reference_dir / "reference_manifest.json")
    for case in manifest.get("cases", []):
        if isinstance(case, dict) and case.get("id") == case_id:
            return {
                "case_id": case_id,
                "comp": manifest.get("comp") or case.get("comp") or {},
                "frame": case.get("frame") or f"{case_id}.png",
                "params": {"effects": case.get("effects") or []},
                "metadata": case.get("metadata") or {},
            }
    raise ValueError(f"case not found in manifest: {case_id}")


def grouped_params(rb: Any, payload: dict[str, Any]) -> dict[str, Any]:
    return rb.grouped_params(payload)


def windows_case(trace_comparison: dict[str, Any], case_id: str) -> dict[str, Any]:
    for case in trace_comparison.get("windows", {}).get("cases", []):
        if isinstance(case, dict) and case.get("case_id") == case_id:
            return case
    return {}


def compute_zoom_sample(rb: Any, image: Image.Image, params: dict[str, Any], payload: dict[str, Any], x: int, y: int) -> dict[str, Any]:
    rgba = np.asarray(image.convert("RGBA"), dtype=np.uint8).astype(np.float32) / 255.0
    height, width = rgba.shape[:2]
    comp = payload.get("comp") if isinstance(payload.get("comp"), dict) else {}
    comp_width = float(comp.get("width") or width)
    comp_height = float(comp.get("height") or height)
    scale_x = width / comp_width
    scale_y = height / comp_height
    center = params.get("center") or [comp_width * 0.5, comp_height * 0.5]
    cx = float(center[0]) * scale_x
    cy = float(center[1]) * scale_y
    ratio = float(params.get("ratio") or 1.0)
    base_angle = math.radians(float(params.get("angle") or 0.0))
    repeat = bool(params.get("repeat_border", 1))
    quality = float(params.get("quality") or 5.0)
    strength = int(float(params.get("outer_strength") or 0.0))
    outer_offset_mode = int(float(params.get("outer_offset_mode") or 1.0))
    outer_offset = int(float(params.get("outer_offset") or 0.0))

    step_deg = 1.0 / quality if quality > 0 else 0.2
    step_rad = math.radians(step_deg)
    angular_count = int(360.0 / step_deg)

    min_dx = 0.0 if 0.0 <= cx < width else abs(cx if cx < 0.0 else cx - width)
    min_dy = 0.0 if 0.0 <= cy < height else abs(cy if cy < 0.0 else cy - height)
    max_dx = max(cx, width - cx) if 0.0 <= cx < width else (width - cx if cx < 0.0 else cx)
    max_dy = max(cy, height - cy) if 0.0 <= cy < height else (height - cy if cy < 0.0 else cy)
    min_r = max(0, int(math.sqrt(min_dx * min_dx + min_dy * min_dy) / ratio) - 2)
    max_r = int(math.sqrt(max_dx * max_dx + max_dy * max_dy)) + 2
    radii = np.arange(min_r, max_r + 1, dtype=np.float32)

    theta = np.arange(angular_count, dtype=np.float32) * step_rad
    cos_t = np.cos(theta)
    sin_t = np.sin(theta)
    cos_a = math.cos(base_angle)
    sin_a = math.sin(base_angle)

    polar = np.empty((angular_count, len(radii), 4), dtype=np.float32)
    for ai in range(angular_count):
        sx0 = radii * cos_t[ai]
        sy0 = radii * sin_t[ai] * ratio
        sx = cx + cos_a * sx0 - sin_a * sy0
        sy = cy + sin_a * sx0 + cos_a * sy0
        polar[ai] = rb.bilinear_premul(rgba, sx, sy, repeat)

    alpha = polar[..., 3]
    outer_length = int(rb.zoom_effective_length(strength, outer_offset_mode, outer_offset))
    outer_length = max(0, min(outer_length, 3000))
    weights = rb.zoom_gaussian_weights(outer_length)
    weighted_rgb = rb.linear_scatter_sum(polar[..., :3] * alpha[..., None], weights, "forward")
    weighted_alpha = rb.linear_scatter_sum(alpha, weights, "forward")
    accum_alpha = rb.linear_scatter_sum(alpha, weights, "forward")

    blurred = np.zeros_like(polar)
    nz = weighted_alpha > 1e-8
    blurred[..., :3][nz] = weighted_rgb[nz] / weighted_alpha[nz, None]
    blurred[..., 3] = np.clip(accum_alpha, 0.0, 1.0)

    dx = float(x) - cx
    dy = float(y) - cy
    ex = cos_a * dx + sin_a * dy
    ey = (cos_a * dy - sin_a * dx) / ratio
    radius = math.sqrt(ex * ex + ey * ey)
    angle = math.atan2(ey, ex)
    if angle < 0.0:
        angle += math.tau
    radius_index = radius - float(min_r)
    angle_index = angle / step_rad
    sample = rb.sample_zoom_grid_alpha_normalized(
        blurred,
        np.array([[radius_index]], dtype=np.float32),
        np.array([[angle_index]], dtype=np.float32),
    )[0, 0]
    u8_floor = np.floor(np.clip(sample, 0.0, 1.0) * 255.0).astype(int)
    return {
        "geometry": {
            "width": width,
            "height": height,
            "center": [cx, cy],
            "min_r": min_r,
            "max_r": max_r,
            "quality": quality,
            "outer_strength": strength,
            "outer_length": outer_length,
            "radius_index": radius_index,
            "angle_index": angle_index,
        },
        "local_sample_float": [float(v) for v in sample],
        "local_floor_u8": [int(v) for v in u8_floor],
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    rb = load_radialblur_module()
    payload = payload_for_case(args.reference_dir, args.case_id)
    params = grouped_params(rb, payload)
    before = Image.open(args.reference_dir / f"{args.case_id}_before_effects.png")
    reference = np.asarray(Image.open(args.reference_dir / f"{args.case_id}.png").convert("RGBA"))
    rendered = rb.render_zoom_polar(before, params, payload)
    candidate = np.asarray(rendered.convert("RGBA"))
    local = compute_zoom_sample(rb, before, params, payload, args.x, args.y)
    comparison = read_json(args.trace_comparison_json)
    win = windows_case(comparison, args.case_id)
    win_float = win.get("aex_pre_writeback_rgba_float_or_hex")
    win_u8 = win.get("aex_final_rgba_u8")
    local_float = local["local_sample_float"]
    return {
        "kind": "olmradialblur_zoom_witness_audit",
        "schema": 1,
        "case_id": args.case_id,
        "xy": [args.x, args.y],
        "local": {
            **local,
            "candidate_rgba": [int(v) for v in candidate[args.y, args.x]],
            "reference_rgba": [int(v) for v in reference[args.y, args.x]],
            "candidate_minus_reference": [int(a) - int(b) for a, b in zip(candidate[args.y, args.x], reference[args.y, args.x])],
        },
        "windows_trace": {
            "pre_writeback_rgba_float": win_float,
            "final_rgba_u8": win_u8,
            "classification": win.get("classification"),
        },
        "deltas": {
            "local_minus_windows_float": (
                [float(a) - float(b) for a, b in zip(local_float, win_float)]
                if isinstance(win_float, list) and all(isinstance(v, (int, float)) for v in win_float)
                else None
            ),
            "local_floor_minus_windows_u8": (
                [int(a) - int(b) for a, b in zip(local["local_floor_u8"], win_u8)]
                if isinstance(win_u8, list) and all(isinstance(v, int) for v in win_u8)
                else None
            ),
        },
        "interpretation": (
            "RGB floats are essentially matched at the Zoom witness, but local alpha is clipped to 1.0 "
            "while the Windows trace returns 0.99999994. The remaining max=1 alpha residual is upstream "
            "of final byte packing and should be treated as sampler/alpha-normalization state, not a "
            "writeback conversion rule."
        ),
    }


def render_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# OLMRadialBlur Zoom Witness Audit",
            "",
            f"- Case: `{report['case_id']}`",
            f"- XY: `{report['xy']}`",
            f"- Local float: `{json.dumps(report['local']['local_sample_float'])}`",
            f"- Windows float: `{json.dumps(report['windows_trace']['pre_writeback_rgba_float'])}`",
            f"- Local floor u8: `{json.dumps(report['local']['local_floor_u8'])}`",
            f"- Windows final u8: `{json.dumps(report['windows_trace']['final_rgba_u8'])}`",
            f"- Candidate/reference: `{json.dumps(report['local']['candidate_rgba'])}` / `{json.dumps(report['local']['reference_rgba'])}`",
            f"- Delta float: `{json.dumps(report['deltas']['local_minus_windows_float'])}`",
            f"- Delta u8: `{json.dumps(report['deltas']['local_floor_minus_windows_u8'])}`",
            "",
            "## Interpretation",
            "",
            report["interpretation"],
            "",
        ]
    )


def main() -> int:
    args = parse_args()
    report = build_report(args)
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"report_json={args.output_json}")
    if args.output_md:
        args.output_md.parent.mkdir(parents=True, exist_ok=True)
        args.output_md.write_text(render_markdown(report), encoding="utf-8")
        print(f"report_md={args.output_md}")
    if not args.output_json and not args.output_md:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
