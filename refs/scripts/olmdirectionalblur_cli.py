#!/usr/bin/env python3
"""Experimental AE-free OLMDirectionalBlur CLI.

Implemented slice:
  - front blur only
  - no noise
  - direct one-sided sampling along Angle

This is a measurement scaffold for the first DirectionalBlur slice, not an
exact port. See notes/PORTING_BOARD.md.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


def grouped_params(payload: dict[str, Any]) -> dict[str, Any]:
    params = payload.get("params", payload)
    effects = params.get("effects", []) if isinstance(params, dict) else []
    out: dict[str, Any] = {}
    for effect in effects:
        if effect.get("name") != "OLM DirectionalBlur" and effect.get("match_name") != "OLM Directional Blur":
            continue
        group = "root"
        sharp_count = {"front": 0, "back": 0}
        for param in effect.get("params", []):
            name = param.get("name") or ""
            if name == "Front Blur Parameters":
                group = "front"
                continue
            if name == "Back Blur Parameters":
                group = "back"
                continue
            if name == "Noise Parameters":
                group = "noise"
                continue
            if param.get("value") is None:
                continue

            key = name.lower().replace(" ", "_")
            if group in {"front", "back"} and name in {"Blur Strength", "Alpha Fade"}:
                key = f"{group}_{key}"
            elif group in {"front", "back"} and name == "Sharp Tail":
                sharp_count[group] += 1
                key = f"{group}_sharp_tail_{sharp_count[group]}"
            elif group == "noise" and name == "Offset":
                key = "noise_offset"
            out[key] = param["value"]
    return out


def load_params(params_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    payload = json.loads(params_path.read_text())
    return grouped_params(payload), payload


def bilinear(src: np.ndarray, x: np.ndarray, y: np.ndarray) -> np.ndarray:
    h, w = src.shape[:2]
    valid = (x >= 0.0) & (x <= w - 1.0) & (y >= 0.0) & (y <= h - 1.0)
    x = np.clip(x, 0.0, w - 1.0)
    y = np.clip(y, 0.0, h - 1.0)

    x0 = np.floor(x).astype(np.int32)
    y0 = np.floor(y).astype(np.int32)
    x1 = np.clip(x0 + 1, 0, w - 1)
    y1 = np.clip(y0 + 1, 0, h - 1)
    fx = (x - x0)[..., None]
    fy = (y - y0)[..., None]

    c00 = src[y0, x0]
    c10 = src[y0, x1]
    c01 = src[y1, x0]
    c11 = src[y1, x1]
    top = c00 * (1.0 - fx) + c10 * fx
    bottom = c01 * (1.0 - fx) + c11 * fx
    out = top * (1.0 - fy) + bottom * fy
    out[~valid] = 0.0
    return out


def gaussian_weights(length: int) -> np.ndarray:
    """Match FUN_180001830's broad Gaussian table shape."""
    if length <= 1:
        return np.ones(1, dtype=np.float32)
    denom = 2.0 * (float(length) / 0.5) * (float(length) / 0.5) + 1.0e-5
    idx = np.arange(length, dtype=np.float32)
    return np.exp(-(idx * idx) / denom).astype(np.float32)


def quantize_rgba(arr: np.ndarray, mode: str) -> np.ndarray:
    arr = np.clip(arr, 0.0, 1.0) * 255.0
    if mode == "floor":
        return np.floor(arr).astype(np.uint8)
    if mode == "ceil":
        return np.ceil(arr).astype(np.uint8)
    return np.rint(arr).astype(np.uint8)


def render_directional(
    image: Image.Image,
    params: dict[str, Any],
    payload: dict[str, Any],
    algorithm: str = "direct",
    quantize: str = "round",
    direction: str = "front",
    ignore_size_variation: bool = False,
    ignore_noise_variation: bool = False,
    angle_sign: float = 1.0,
    sample_sign: float = 1.0,
    strength_scale: float | None = None,
    rgb_normalize: str = "alpha-sum",
) -> Image.Image:
    rgba = np.asarray(image.convert("RGBA"), dtype=np.uint8).astype(np.float32) / 255.0
    h, w = rgba.shape[:2]

    angle = math.radians(float(params.get("angle") or 0.0) * angle_sign)
    brightness_gain = float(params.get("brightness_gain") or 1.0)
    size_variation = 0.0 if ignore_size_variation else float(params.get("size_variation") or 0.0) / 100.0
    if strength_scale is None:
        comp = payload.get("comp") if isinstance(payload.get("comp"), dict) else {}
        frame_rate = float(comp.get("frame_rate") or 0.0)
        strength_scale = 1.0 / frame_rate if frame_rate > 0.0 else 1.0
    front_strength = int(float(params.get("front_blur_strength") or 0.0) * strength_scale)
    back_strength = int(float(params.get("back_blur_strength") or 0.0) * strength_scale)
    front_sharp_tail = float(params.get("front_sharp_tail_1") or 0.0) / 100.0
    back_sharp_tail = float(params.get("back_sharp_tail_1") or 0.0) / 100.0
    noise_variation = float(params.get("noise_variation") or 0.0)

    if noise_variation != 0.0 and not ignore_noise_variation:
        raise SystemExit("olmdirectionalblur_cli.py currently does not implement Noise Variation")
    if back_strength != 0 and direction != "both":
        raise SystemExit("back blur is not validated; pass --direction both to probe it")

    if algorithm == "rotated":
        return render_directional_rotated(
            rgba,
            angle,
            brightness_gain,
            front_strength,
            back_strength if direction == "both" else 0,
            front_sharp_tail,
            back_sharp_tail if direction == "both" else 0.0,
            quantize,
            sample_sign,
        )

    # AEX rotates the intermediate buffer by Angle, scatters along its X axis,
    # then rotates back. Direct image-space sampling with this vector gives the
    # same first-order direction while we reconstruct the padded buffers.
    vx = math.cos(angle)
    vy = math.sin(angle)

    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    accum_rgb = rgba[..., :3] * rgba[..., 3:4]
    accum_alpha_sum = rgba[..., 3].copy()
    accum_alpha_max = rgba[..., 3].copy()

    def sharp_tail_map(sharp_tail: float) -> np.ndarray | None:
        if sharp_tail <= 0.0:
            return None
        # FUN_1800028e0 builds a per-pixel component map, and FUN_1800038d0
        # uses its center/span fields to reduce the effective blur length.
        # This approximates the no-noise, fully-opaque reference cases with a
        # single image-height component until the exact rotated map is ported.
        center = (float(h) - 1.0) * 0.5
        span = max(center, 1.0)
        return np.maximum(0.0, 1.0 - np.abs(yy - center) * sharp_tail / span).astype(np.float32)

    def apply_one_sided(strength: int, sign: float, sharp_tail: float) -> None:
        nonlocal accum_rgb, accum_alpha_sum, accum_alpha_max
        if strength <= 1:
            return
        weights = gaussian_weights(strength)
        tail = sharp_tail_map(sharp_tail)
        for i in range(1, strength):
            sx = xx + sign * vx * i
            sy = yy + sign * vy * i
            sample = bilinear(rgba, sx, sy)
            if tail is None:
                alpha = sample[..., 3] * float(weights[i])
            else:
                active = i < (strength * tail)
                idx = np.clip((i / np.maximum(tail, 1.0e-6)).astype(np.int32), 0, strength - 1)
                alpha = sample[..., 3] * weights[idx] * active
            # Size Variation affects per-pixel blur scale in the AEX. This
            # first probe keeps the effect monotonic without emulating the
            # source-position table yet.
            if size_variation:
                alpha *= np.power(np.clip(sample[..., 3], 0.0, 1.0), size_variation)
            accum_rgb += sample[..., :3] * alpha[..., None]
            accum_alpha_sum += alpha
            accum_alpha_max = np.maximum(accum_alpha_max, alpha)

    apply_one_sided(front_strength, sample_sign, front_sharp_tail)
    if direction == "both":
        apply_one_sided(back_strength, -sample_sign, back_sharp_tail)

    out = np.zeros_like(rgba)
    if rgb_normalize == "alpha-sum":
        mask = accum_alpha_sum > 1.0e-8
        out[..., :3][mask] = accum_rgb[mask] / accum_alpha_sum[mask, None]
    elif rgb_normalize == "front-strength":
        out[..., :3] = accum_rgb / max(float(front_strength), 1.0)
    elif rgb_normalize == "total-strength":
        out[..., :3] = accum_rgb / max(float(front_strength + (back_strength if direction == "both" else 0)), 1.0)
    elif rgb_normalize == "kernel-sum":
        denom = max(float(np.sum(gaussian_weights(max(front_strength, 1)))), 1.0e-8)
        out[..., :3] = accum_rgb / denom
    else:
        raise ValueError(f"unknown rgb_normalize mode: {rgb_normalize}")
    out[..., 3] = accum_alpha_max
    out[..., :3] *= brightness_gain
    return Image.fromarray(quantize_rgba(out, quantize), "RGBA")


def render_directional_rotated(
    rgba: np.ndarray,
    angle: float,
    brightness_gain: float,
    front_strength: int,
    back_strength: int,
    front_sharp_tail: float,
    back_sharp_tail: float,
    quantize: str,
    sample_sign: float,
) -> Image.Image:
    """AEX-shaped rotated-buffer experiment.

    FUN_180003c90 expands to a diagonal-sized buffer, rotates the source into
    that buffer, scatters horizontally, normalizes, then rotates back.
    """
    h, w = rgba.shape[:2]
    diag = int(math.ceil(math.sqrt(w * w + h * h))) + 4
    pad_w = diag
    pad_h = diag

    yy, xx = np.mgrid[0:pad_h, 0:pad_w].astype(np.float32)
    dx = xx - pad_w / 2.0
    dy = yy - pad_h / 2.0
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    # Match FUN_180001ec0's coordinate form at a high level.
    src_x = dx * cos_a - dy * sin_a + w / 2.0
    src_y = dx * sin_a + dy * cos_a + h / 2.0
    rotated = bilinear(rgba, src_x, src_y)

    accum_rgb = rotated[..., :3] * rotated[..., 3:4]
    accum_sum = rotated[..., 3].copy()
    accum_alpha = rotated[..., 3].copy()

    def rotated_sharp_tail_map(sharp_tail: float) -> np.ndarray | None:
        if sharp_tail <= 0.0:
            return None
        valid_y = np.nonzero(rotated[..., 3] > 0.0)[0]
        if valid_y.size == 0:
            return None
        center = (float(valid_y.min()) + float(valid_y.max())) * 0.5
        span = max((float(valid_y.max()) - float(valid_y.min())) * 0.5, 1.0)
        yy_only = np.arange(pad_h, dtype=np.float32)[:, None]
        return np.maximum(0.0, 1.0 - np.abs(yy_only - center) * sharp_tail / span).astype(np.float32)

    def scatter_horizontal(strength: int, sign: float, sharp_tail: float) -> None:
        nonlocal accum_rgb, accum_sum, accum_alpha
        if strength <= 1:
            return
        weights = gaussian_weights(strength)
        source_rgb = rotated[..., :3] * rotated[..., 3:4]
        source_alpha = rotated[..., 3]
        tail = rotated_sharp_tail_map(sharp_tail)
        for i in range(1, strength):
            if tail is None:
                alpha = source_alpha * float(weights[i])
                rgb = source_rgb * float(weights[i])
            else:
                active = i < (strength * tail)
                idx = np.clip((i / np.maximum(tail, 1.0e-6)).astype(np.int32), 0, strength - 1)
                weight = weights[idx] * active
                alpha = source_alpha * weight
                rgb = source_rgb * weight[..., None]
            shift = int(sign * sample_sign) * i
            if shift > 0:
                accum_rgb[:, shift:] += rgb[:, :-shift]
                accum_sum[:, shift:] += alpha[:, :-shift]
                accum_alpha[:, shift:] = np.maximum(accum_alpha[:, shift:], alpha[:, :-shift])
            else:
                nshift = -shift
                accum_rgb[:, :-nshift] += rgb[:, nshift:]
                accum_sum[:, :-nshift] += alpha[:, nshift:]
                accum_alpha[:, :-nshift] = np.maximum(accum_alpha[:, :-nshift], alpha[:, nshift:])

    scatter_horizontal(front_strength, 1.0, front_sharp_tail)
    scatter_horizontal(back_strength, -1.0, back_sharp_tail)

    blurred = np.zeros_like(rotated)
    mask = accum_sum > 1.0e-8
    blurred[..., :3][mask] = accum_rgb[mask] / accum_sum[mask, None]
    blurred[..., 3] = accum_alpha

    out_y, out_x = np.mgrid[0:h, 0:w].astype(np.float32)
    odx = out_x - w / 2.0
    ody = out_y - h / 2.0
    # Inverse of the rotation above.
    bx = odx * cos_a + ody * sin_a + pad_w / 2.0
    by = -odx * sin_a + ody * cos_a + pad_h / 2.0
    out = bilinear(blurred, bx, by)
    out[..., :3] *= brightness_gain
    return Image.fromarray(quantize_rgba(out, quantize), "RGBA")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--params", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--algorithm", choices=["direct", "rotated"], default="direct")
    parser.add_argument("--quantize", choices=["round", "floor", "ceil"], default="round")
    parser.add_argument("--direction", choices=["front", "both"], default="front")
    parser.add_argument("--ignore-size-variation", action="store_true")
    parser.add_argument("--ignore-noise-variation", action="store_true")
    parser.add_argument("--angle-sign", choices=["1", "-1"], default="1")
    parser.add_argument("--sample-sign", choices=["1", "-1"], default="1")
    parser.add_argument(
        "--strength-scale",
        default="auto",
        help="numeric scale or 'auto' (= 1 / manifest comp.frame_rate)",
    )
    parser.add_argument(
        "--rgb-normalize",
        choices=["alpha-sum", "front-strength", "total-strength", "kernel-sum"],
        default="alpha-sum",
        help="direct-mode RGB normalization probe",
    )
    args = parser.parse_args()

    params, payload = load_params(Path(args.params))
    strength_scale = None if args.strength_scale == "auto" else float(args.strength_scale)
    out = render_directional(
        Image.open(args.input),
        params,
        payload,
        args.algorithm,
        args.quantize,
        args.direction,
        args.ignore_size_variation,
        args.ignore_noise_variation,
        float(args.angle_sign),
        float(args.sample_sign),
        strength_scale,
        args.rgb_normalize,
    )
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.save(out_path)
    print(f"wrote: {out_path} (experimental directional slice)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
