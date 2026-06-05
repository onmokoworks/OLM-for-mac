#!/usr/bin/env python3
"""AE-free OLM Distance Gradation reference CLI.

This mirrors the current mac/OLMDistanceGradation C++ core closely enough to
use the Windows PNG/manifest references as an algorithm regression target.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage


IN_OUT_INSIDE = 1
IN_OUT_OUTSIDE = 2
IN_OUT_BOTH = 3

RENDER_MODE_RGB = 1
RENDER_MODE_LAYER = 2

INTERP_CONSTANT = 1
INTERP_LINEAR = 2
INTERP_SPHERE = 3
INTERP_POWER = 4

BLUR_MODE_NONE = 1
BLUR_MODE_NO_SCALE = 2
BLUR_MODE_SCALE = 3


def key_for_name(name: str) -> str:
    return name.strip().lower().replace(" ", "_").replace("/", "_")


def read_effect_params(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    scope = data.get("params", data)
    effects = scope.get("effects", [])
    out: dict[str, object] = {}
    for effect in effects:
        if effect.get("match_name") != "OLM Distance Gradation" and effect.get("name") != "Distance Gradation":
            continue
        for param in effect.get("params", []):
            value = param.get("value")
            if value is None:
                continue
            out[key_for_name(param.get("name", ""))] = value
    return out


def color_param(value: object, fallback: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    if isinstance(value, list) and len(value) >= 3:
        alpha = float(value[3]) if len(value) >= 4 else 1.0
        return float(value[0]), float(value[1]), float(value[2]), alpha
    return fallback


def gaussian_kernel(ksize: int) -> np.ndarray:
    if ksize % 2 == 0:
        ksize += 1
    ksize = max(ksize, 1)
    sigma = 0.3 * ((ksize - 1) * 0.5 - 1.0) + 0.8
    half = ksize // 2
    xs = np.arange(ksize, dtype=np.float32) - half
    k = np.exp(-(xs * xs) / (2.0 * sigma * sigma)).astype(np.float32)
    return k / np.sum(k)


def blur_reflect101(field: np.ndarray, radius: int) -> np.ndarray:
    if radius <= 0:
        return field
    k = gaussian_kernel(2 * radius + 1)
    out = ndimage.convolve1d(field, k, axis=1, mode="mirror")
    out = ndimage.convolve1d(out, k, axis=0, mode="mirror")
    return out.astype(np.float32)


def dt_to_normalized(mask: np.ndarray, threshold: int, ds_scale: float) -> np.ndarray:
    dist = ndimage.distance_transform_edt(mask != 0).astype(np.float32)
    t = 1.0 if threshold == 0 else float(threshold) * ds_scale
    t = max(t, 1.0)
    dist = np.minimum(dist, t)
    raw_max = float(np.max(dist)) if dist.size else 0.0
    denom = raw_max if raw_max > 1.0 else 1.0
    return (dist / denom).astype(np.float32)


def render(input_rgba: np.ndarray, params: dict[str, object], ds_x: float, ds_y: float) -> np.ndarray:
    rgba = input_rgba.astype(np.float32) / 255.0
    alpha = rgba[..., 3]
    mask = (alpha > 0.0).astype(np.uint8)

    invert = bool(int(params.get("invert", 0)))
    in_out = int(params.get("in_out", IN_OUT_BOTH))
    inside_threshold = int(params.get("inside_threshold", 128))
    outside_threshold = int(params.get("outside_threshold", 128))
    render_mode = int(params.get("render_mode", RENDER_MODE_RGB))
    use_bg = bool(int(params.get("use_background_color", 0)))
    grad_color = color_param(params.get("gradation_color"), (1.0, 0.0, 0.0, 1.0))
    bg_color = color_param(params.get("bg_color"), (0.0, 0.0, 0.0, 1.0))
    interp_mode = int(params.get("interpolation_mode", INTERP_LINEAR))
    power = float(params.get("power", 5.0))
    blur_mode = int(params.get("blur_mode", BLUR_MODE_NONE))
    blur_size = int(params.get("blur_size", 0))

    d_alpha = mask.astype(np.float32)
    ds = (ds_x + ds_y) * 0.5
    if ds <= 0.0:
        ds = 1.0

    if in_out == IN_OUT_INSIDE:
        x = dt_to_normalized(mask, inside_threshold, ds)
    elif in_out == IN_OUT_OUTSIDE:
        x = dt_to_normalized(1 - mask, outside_threshold, ds)
    else:
        inside = dt_to_normalized(mask, inside_threshold, ds)
        outside = dt_to_normalized(1 - mask, outside_threshold, ds)
        x = np.maximum(inside, outside).astype(np.float32)

    constant_blur = interp_mode == INTERP_CONSTANT and blur_mode != BLUR_MODE_NONE and blur_size > 0
    if constant_blur:
        x = (x >= 1.0).astype(np.float32)

    if blur_mode != BLUR_MODE_NONE and blur_size > 0:
        radius = blur_size
        if blur_mode == BLUR_MODE_SCALE:
            radius = int(float(blur_size) * ds + 0.5)
        if constant_blur:
            radius *= 2
        x = blur_reflect101(x, max(radius, 1))

    if not invert:
        x = 1.0 - x

    if interp_mode == INTERP_SPHERE:
        t = 1.0 - x
        x = np.sqrt(np.maximum(1.0 - t * t, 0.0)).astype(np.float32)
    elif interp_mode == INTERP_POWER:
        x = np.power(x, power).astype(np.float32)
    elif interp_mode == INTERP_CONSTANT and not constant_blur:
        x = (x > 0.0).astype(np.float32)

    if in_out == IN_OUT_INSIDE:
        out_alpha_base = alpha
    elif in_out == IN_OUT_OUTSIDE:
        out_alpha_base = np.maximum(1.0 - alpha, 0.0)
    else:
        out_alpha_base = np.ones_like(alpha, dtype=np.float32)

    if render_mode == RENDER_MODE_RGB:
        ir = np.full_like(alpha, grad_color[0], dtype=np.float32)
        ig = np.full_like(alpha, grad_color[1], dtype=np.float32)
        ib = np.full_like(alpha, grad_color[2], dtype=np.float32)
    else:
        ir, ig, ib = rgba[..., 0], rgba[..., 1], rgba[..., 2]

    out = np.zeros_like(rgba, dtype=np.float32)
    if use_bg:
        one_x = 1.0 - x
        out[..., 0] = one_x * bg_color[0] + x * ir
        out[..., 1] = one_x * bg_color[1] + x * ig
        out[..., 2] = one_x * bg_color[2] + x * ib
        out[..., 3] = out_alpha_base
        out[..., 0] *= out[..., 3]
        out[..., 1] *= out[..., 3]
        out[..., 2] *= out[..., 3]
    else:
        out[..., 3] = out_alpha_base * x
        # AE's PNG reference output is premultiplied; the plug-in core writes
        # straight RGB into the AE world, but the exported reference stores
        # transparent pixels with RGB collapsed by alpha.
        out[..., 0] = ir * out[..., 3]
        out[..., 1] = ig * out[..., 3]
        out[..., 2] = ib * out[..., 3]

    return np.clip(np.floor(out * 255.0 + 0.5), 0, 255).astype(np.uint8)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--params", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--ds-x", type=float, default=1.0)
    parser.add_argument("--ds-y", type=float, default=1.0)
    args = parser.parse_args()

    image = Image.open(args.input).convert("RGBA")
    rgba = np.array(image, dtype=np.uint8)
    params = read_effect_params(Path(args.params))
    out = render(rgba, params, args.ds_x, args.ds_y)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(out, "RGBA").save(args.output)
    print(f"wrote: {args.output} (Distance Gradation Python CLI)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
