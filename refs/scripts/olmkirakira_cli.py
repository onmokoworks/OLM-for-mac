#!/usr/bin/env python3
"""Experimental AE-free OLMKiraKira CLI.

Implemented slice:
  - white vertical/horizontal/diagonal rays
  - no ramps
  - no highlight radius

This is a measurement scaffold for the first KiraKira reference, not an exact
port. See notes/PORTING_BOARD.md.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


def grouped_params(payload: dict[str, Any]) -> dict[str, Any]:
    params = payload.get("params", payload)
    effects = params.get("effects", []) if isinstance(params, dict) else []
    out: dict[str, Any] = {}
    for effect in effects:
        if effect.get("name") != "OLM Kira Kira" and effect.get("match_name") != "OLM OLM Kira Kira":
            continue
        for param in effect.get("params", []):
            if param.get("value") is None:
                continue
            name = param.get("name") or ""
            match = param.get("match_name") or ""
            key = name.lower().replace(" ", "_")
            if match.endswith("-0001"):
                key = "glow_rotation"
            elif match.endswith("-0002"):
                key = "brightness_gain"
            elif match.endswith("-0003"):
                key = "vertical_length"
            elif match.endswith("-0004"):
                key = "horizontal_length"
            elif match.endswith("-0005"):
                key = "diagonal_length"
            elif match.endswith("-0006"):
                key = "highlight_radius"
            elif match.endswith("-0007"):
                key = "glow_opacity"
            elif match.endswith("-0008"):
                key = "channel"
            elif match.endswith("-0009"):
                key = "blur_mode"
            elif match.endswith("-0010"):
                key = "approximated_input"
            elif match.endswith("-0011"):
                key = "strength_multiplier"
            elif match.endswith("-0012"):
                key = "source_opacity"
            elif match.endswith("-0013"):
                key = "vertical_color"
            elif match.endswith("-0014"):
                key = "horizontal_color"
            elif match.endswith("-0015"):
                key = "diagonal_color"
            elif match.endswith("-0016"):
                key = "highlight_color"
            elif match.endswith("-0017"):
                key = "merge_mode"
            elif match.endswith("-0018"):
                key = "vertical_use_ramp"
            elif match.endswith("-0020"):
                key = "horizontal_use_ramp"
            elif match.endswith("-0022"):
                key = "diagonal_use_ramp"
            elif match.endswith("-0024"):
                key = "highlight_use_ramp"
            elif match.endswith("-0026"):
                key = "diagonal2_length"
            elif match.endswith("-0027"):
                key = "fade_out"
            elif match.endswith("-0028"):
                key = "diagonal2_color"
            elif match.endswith("-0035"):
                key = "diagonal2_use_ramp"
            out[key] = param["value"]
    return out


def load_params(params_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    payload = json.loads(params_path.read_text())
    return grouped_params(payload), payload


def float_param(params: dict[str, Any], key: str, default: float) -> float:
    value = params.get(key)
    if value is None:
        return default
    return float(value)


def quantize_rgba(arr: np.ndarray, mode: str) -> np.ndarray:
    arr = np.clip(arr, 0.0, 1.0) * 255.0
    if mode == "floor":
        return np.floor(arr).astype(np.uint8)
    if mode == "ceil":
        return np.ceil(arr).astype(np.uint8)
    return np.rint(arr).astype(np.uint8)


def channel_seed(rgba: np.ndarray, channel: int, mode: str, brightness_gain: float = 1.0) -> np.ndarray:
    rgb = rgba[..., :3]
    alpha = rgba[..., 3]
    if mode == "aex":
        if channel == 1:
            seed = np.power(alpha, max(1.0e-6, brightness_gain))
            return seed
        if channel == 2:
            luma = rgb[..., 0] * 0.299 + rgb[..., 1] * 0.587 + rgb[..., 2] * 0.114
            seed = np.power(luma, max(1.0e-6, brightness_gain))
            return seed * alpha
        if channel == 4:
            seed = np.power(np.max(rgb, axis=2), max(1.0e-6, brightness_gain))
            return seed * alpha
        seed = np.max(np.power(rgb, max(1.0e-6, brightness_gain)), axis=2)
        return seed * alpha
    if mode == "luma":
        seed = rgb[..., 0] * 0.299 + rgb[..., 1] * 0.587 + rgb[..., 2] * 0.114
    elif mode == "max":
        seed = np.max(rgb, axis=2)
    elif mode == "brightness":
        seed = np.power(np.max(rgb, axis=2), max(1.0e-6, brightness_gain))
    elif mode == "alpha":
        seed = alpha
    else:
        idx = max(0, min(2, channel))
        seed = rgb[..., idx]
    return seed * alpha


def ray(seed: np.ndarray, length: int, dx: int, dy: int, falloff: str) -> np.ndarray:
    if length <= 0:
        return np.zeros_like(seed)
    out = np.zeros_like(seed, dtype=np.float32)
    h, w = seed.shape
    for i in range(1, length + 1):
        if falloff == "linear":
            weight = 1.0 - (i / (length + 1.0))
        elif falloff == "inverse":
            weight = 1.0 / (i + 1.0)
        else:
            weight = 1.0

        sx0 = max(0, -dx * i)
        sx1 = min(w, w - dx * i)
        sy0 = max(0, -dy * i)
        sy1 = min(h, h - dy * i)
        dx0 = max(0, dx * i)
        dx1 = min(w, w + dx * i)
        dy0 = max(0, dy * i)
        dy1 = min(h, h + dy * i)
        out[dy0:dy1, dx0:dx1] += seed[sy0:sy1, sx0:sx1] * weight
    return out / max(1.0, float(length))


def ray_axis(seed: np.ndarray, length: int, dx: int, dy: int, falloff: str, bidirectional: bool) -> np.ndarray:
    out = ray(seed, length, dx, dy, falloff)
    if not bidirectional:
        return out
    out += ray(seed, length, -dx, -dy, falloff)
    return out * 0.5


def one_dimensional_kernel(length: int, falloff: str, include_center: bool) -> np.ndarray:
    if length <= 0:
        return np.ones(1, dtype=np.float32)
    x = np.arange(-length, length + 1, dtype=np.float32)
    d = np.abs(x)
    if falloff == "flat":
        weights = np.ones_like(x)
    elif falloff == "inverse":
        weights = 1.0 / (d + 1.0)
    else:
        sigma = max(1.0, float(length) / 3.0)
        weights = np.exp(-(d * d) / (2.0 * sigma * sigma))
    if not include_center:
        weights[length] = 0.0
    total = float(weights.sum())
    if total > 0.0:
        weights /= total
    return weights.astype(np.float32)


def crop_center(arr: np.ndarray, height: int, width: int, offset_y: int = 0, offset_x: int = 0) -> np.ndarray:
    y0 = max(0, (arr.shape[0] - height) // 2 + offset_y)
    x0 = max(0, (arr.shape[1] - width) // 2 + offset_x)
    cropped = arr[y0 : y0 + height, x0 : x0 + width]
    if cropped.shape == (height, width):
        return cropped
    out = np.zeros((height, width), dtype=arr.dtype)
    out[: cropped.shape[0], : cropped.shape[1]] = cropped
    return out


def rotated_axis_blur(
    seed: np.ndarray,
    length: int,
    angle: float,
    falloff: str,
    include_center: bool,
    filter_border: str,
    crop_offset_y: int,
    crop_offset_x: int,
    rotate_order: int,
    rotate_prefilter: bool,
) -> np.ndarray:
    from scipy import ndimage

    height, width = seed.shape
    box_passes = 3 if falloff.startswith("box3") else 1 if falloff.startswith("box1") else 0

    def blur_axis(arr: np.ndarray, axis: int) -> np.ndarray:
        if box_passes:
            out = arr
            size = max(1, length * 2 + 1) if falloff.endswith("-radius") else max(1, length)
            for _ in range(box_passes):
                out = ndimage.uniform_filter1d(out, size=size, axis=axis, mode=filter_border, cval=0.0)
            if not include_center and length > 0:
                # Keep this switch comparable to the kernel path; the AEX mode-2
                # path itself includes the source sample.
                out = out - arr / float(size ** box_passes)
            return out
        kernel = one_dimensional_kernel(length, falloff, include_center)
        return ndimage.convolve1d(arr, kernel, axis=axis, mode=filter_border, cval=0.0)

    if angle == 0.0:
        return blur_axis(seed, axis=1)
    if angle == 90.0:
        return blur_axis(seed, axis=0)

    rotated = ndimage.rotate(seed, angle, reshape=True, order=rotate_order, mode="constant", cval=0.0, prefilter=rotate_prefilter)
    blurred = blur_axis(rotated, axis=1)
    restored = ndimage.rotate(blurred, -angle, reshape=True, order=rotate_order, mode="constant", cval=0.0, prefilter=rotate_prefilter)
    return crop_center(restored, height, width, crop_offset_y, crop_offset_x)


def axis_rotate_rays(
    seed: np.ndarray,
    params: dict[str, Any],
    falloff: str,
    include_center: bool,
    filter_border: str,
    length_scale: float,
    crop_offset_y: int,
    crop_offset_x: int,
    rotate_order: int,
    rotate_prefilter: bool,
) -> list[np.ndarray]:
    def scaled_length(key: str) -> int:
        return max(0, int(round(float_param(params, key, 0.0) * length_scale)))

    glow_rotation = float_param(params, "glow_rotation", 0.0)
    return [
        rotated_axis_blur(
            seed, scaled_length("vertical_length"), 90.0 + glow_rotation, falloff, include_center, filter_border,
            crop_offset_y, crop_offset_x, rotate_order, rotate_prefilter
        ),
        rotated_axis_blur(
            seed, scaled_length("horizontal_length"), glow_rotation, falloff, include_center, filter_border,
            crop_offset_y, crop_offset_x, rotate_order, rotate_prefilter
        ),
        rotated_axis_blur(
            seed, scaled_length("diagonal_length"), 45.0 + glow_rotation, falloff, include_center, filter_border,
            crop_offset_y, crop_offset_x, rotate_order, rotate_prefilter
        ),
        rotated_axis_blur(
            seed, scaled_length("diagonal2_length"), -45.0 + glow_rotation, falloff, include_center, filter_border,
            crop_offset_y, crop_offset_x, rotate_order, rotate_prefilter
        ),
    ]


def add_colored(glow: np.ndarray, amount: np.ndarray, color: Any) -> None:
    c = np.array(color if isinstance(color, list) else [1.0, 1.0, 1.0, 1.0], dtype=np.float32)
    if c.max() > 1.0:
        c = c / 255.0
    glow[..., :3] += amount[..., None] * c[:3]
    glow[..., 3] = np.maximum(glow[..., 3], amount * c[3])


def add_colored_union(glow: np.ndarray, amount: np.ndarray, color: Any) -> None:
    c = np.array(color if isinstance(color, list) else [1.0, 1.0, 1.0, 1.0], dtype=np.float32)
    if c.max() > 1.0:
        c = c / 255.0
    alpha = np.clip(amount * c[3], 0.0, 1.0)
    glow[..., :3] += alpha[..., None] * c[:3]
    glow[..., 3] = glow[..., 3] + alpha - glow[..., 3] * alpha


def normalize_glow(glow: np.ndarray) -> None:
    alpha = glow[..., 3]
    mask = alpha > 1.0e-6
    glow[..., :3][mask] /= alpha[mask, None]


def compose_simple(rgba: np.ndarray, glow: np.ndarray, source_opacity: float) -> np.ndarray:
    out = rgba * source_opacity
    out[..., :3] += glow[..., :3]
    out[..., 3] = np.maximum(out[..., 3], glow[..., 3])
    return out


def compose_aex_premul(rgba: np.ndarray, glow: np.ndarray, source_opacity: float, glow_opacity: float) -> np.ndarray:
    src_alpha = np.clip(rgba[..., 3] * source_opacity, 0.0, 1.0)
    glow_alpha = np.clip(glow[..., 3] * glow_opacity, 0.0, 1.0)
    denom = src_alpha + glow_alpha
    out_rgb = np.zeros_like(rgba[..., :3])
    mask = denom > 1.0e-6
    out_rgb[mask] = (
        rgba[..., :3][mask] * src_alpha[mask, None] + glow[..., :3][mask] * glow_alpha[mask, None]
    ) / denom[mask, None]
    out_alpha = np.clip(denom, 0.0, 1.0)
    return np.dstack([out_rgb, out_alpha])


def render_kirakira(
    image: Image.Image,
    params: dict[str, Any],
    quantize: str = "round",
    seed_mode: str = "channel",
    falloff: str = "linear",
    gain_scale: float = 1.0,
    bidirectional: bool = False,
    ray_mode: str = "shift",
    compose_mode: str = "simple",
    include_center: bool = False,
    strength_override: float | None = None,
    scale_mode: str = "brightness-strength",
    scale_override: float | None = None,
    seed_exponent_override: float | None = None,
    filter_border: str = "constant",
    length_scale: float = 1.0,
    auto_length_scale: bool = False,
    comp_width: float = 1920.0,
    crop_offset_y: int = 0,
    crop_offset_x: int = 0,
    rotate_order: int = 1,
    rotate_prefilter: bool = False,
) -> Image.Image:
    rgba = np.asarray(image.convert("RGBA"), dtype=np.uint8).astype(np.float32) / 255.0
    if auto_length_scale:
        length_scale = float(image.width) / comp_width if comp_width > 0.0 else 1.0
    channel = int(float_param(params, "channel", 0.0))
    brightness_gain = float_param(params, "brightness_gain", 1.0)
    strength_percent = float_param(params, "strength_multiplier", 100.0)
    if strength_override is not None:
        strength_percent = strength_override
    strength = strength_percent / 100.0
    seed_exponent = strength if seed_exponent_override is None else seed_exponent_override
    seed = channel_seed(rgba, channel, seed_mode, seed_exponent)
    glow_opacity = float_param(params, "glow_opacity", 100.0) / 100.0
    source_opacity = float_param(params, "source_opacity", 100.0) / 100.0

    glow = np.zeros_like(rgba)
    if ray_mode == "axis-rotate":
        vertical, horizontal, diagonal, diagonal2 = axis_rotate_rays(
            seed, params, falloff, include_center, filter_border, length_scale, crop_offset_y, crop_offset_x,
            rotate_order, rotate_prefilter
        )
    else:
        vertical = ray_axis(seed, int(float_param(params, "vertical_length", 0.0)), 0, 1, falloff, bidirectional)
        horizontal = ray_axis(seed, int(float_param(params, "horizontal_length", 0.0)), 1, 0, falloff, bidirectional)
        diagonal = ray_axis(seed, int(float_param(params, "diagonal_length", 0.0)), 1, 1, falloff, bidirectional)
        diagonal2 = ray_axis(seed, int(float_param(params, "diagonal2_length", 0.0)), 1, -1, falloff, bidirectional)

    if scale_mode == "aex":
        # Ghidra shows Brightness Gain as the final premul aggregation scale.
        # Keep the existing empirical gain for normal strength cases, but do
        # not let Strength=0 zero out the glow path.
        scale = brightness_gain * (1.0 if strength <= 1.0e-6 else gain_scale)
    elif scale_mode == "brightness":
        scale = brightness_gain * gain_scale
    elif scale_mode == "strength":
        scale = strength * gain_scale
    else:
        scale = brightness_gain * strength * gain_scale
    if scale_override is not None:
        scale = scale_override
    if compose_mode == "aex-premul":
        add_colored_union(glow, np.clip(vertical * scale, 0.0, 1.0), params.get("vertical_color"))
        add_colored_union(glow, np.clip(horizontal * scale, 0.0, 1.0), params.get("horizontal_color"))
        add_colored_union(glow, np.clip(diagonal * scale, 0.0, 1.0), params.get("diagonal_color"))
        add_colored_union(glow, np.clip(diagonal2 * scale, 0.0, 1.0), params.get("diagonal2_color"))
        normalize_glow(glow)
        out = compose_aex_premul(rgba, glow, source_opacity, glow_opacity)
    else:
        add_colored(glow, vertical, params.get("vertical_color"))
        add_colored(glow, horizontal, params.get("horizontal_color"))
        add_colored(glow, diagonal, params.get("diagonal_color"))
        add_colored(glow, diagonal2, params.get("diagonal2_color"))
        glow *= scale * glow_opacity
        out = compose_simple(rgba, glow, source_opacity)
    return Image.fromarray(quantize_rgba(out, quantize), "RGBA")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--params", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--quantize", choices=["round", "floor", "ceil"], default="round")
    parser.add_argument("--seed-mode", choices=["aex", "channel", "luma", "max", "brightness", "alpha"], default="aex")
    parser.add_argument(
        "--falloff",
        choices=["linear", "inverse", "flat", "gaussian", "box1", "box3", "box1-radius", "box3-radius"],
        default="linear",
    )
    parser.add_argument("--gain-scale", type=float, default=1.0)
    parser.add_argument("--bidirectional", action="store_true")
    parser.add_argument("--ray-mode", choices=["shift", "axis-rotate"], default="shift")
    parser.add_argument("--compose-mode", choices=["simple", "aex-premul"], default="simple")
    parser.add_argument("--include-center", action="store_true")
    parser.add_argument(
        "--filter-border",
        choices=["constant", "reflect", "mirror", "nearest", "wrap"],
        default="constant",
        help="Experimental border mode for the post-rotation 1D blur.",
    )
    parser.add_argument(
        "--length-scale",
        type=float,
        default=1.0,
        help="Experimental scale applied to the four ray lengths before axis blur.",
    )
    parser.add_argument(
        "--auto-length-scale",
        action="store_true",
        help="Scale ray lengths by input_width / comp_width before axis blur.",
    )
    parser.add_argument(
        "--comp-width",
        type=float,
        default=1920.0,
        help="Composition width used by --auto-length-scale.",
    )
    parser.add_argument(
        "--crop-offset-y",
        type=int,
        default=0,
        help="Experimental post-rotate crop Y offset for axis-rotate mode.",
    )
    parser.add_argument(
        "--crop-offset-x",
        type=int,
        default=0,
        help="Experimental post-rotate crop X offset for axis-rotate mode.",
    )
    parser.add_argument(
        "--rotate-order",
        type=int,
        choices=[0, 1, 3],
        default=1,
        help="Experimental scipy.ndimage.rotate interpolation order for axis-rotate mode.",
    )
    parser.add_argument(
        "--rotate-prefilter",
        action="store_true",
        help="Enable scipy.ndimage.rotate prefilter for experimental higher-order rotation probes.",
    )
    parser.add_argument(
        "--strength-override",
        type=float,
        default=None,
        help="Experimental percent override for probing KiraKira's unresolved Strength=0/Brightness path.",
    )
    parser.add_argument(
        "--scale-mode",
        choices=["brightness-strength", "brightness", "strength", "aex"],
        default="brightness-strength",
        help="Experimental final aggregation scale model.",
    )
    parser.add_argument(
        "--scale-override",
        type=float,
        default=None,
        help="Experimental direct final aggregation scale override.",
    )
    parser.add_argument(
        "--seed-exponent-override",
        type=float,
        default=None,
        help="Experimental override for the seed brightness exponent.",
    )
    args = parser.parse_args()

    params, _payload = load_params(Path(args.params))
    out = render_kirakira(
        Image.open(args.input),
        params,
        args.quantize,
        args.seed_mode,
        args.falloff,
        args.gain_scale,
        args.bidirectional,
        args.ray_mode,
        args.compose_mode,
        args.include_center,
        args.strength_override,
        args.scale_mode,
        args.scale_override,
        args.seed_exponent_override,
        args.filter_border,
        args.length_scale,
        args.auto_length_scale,
        args.comp_width,
        args.crop_offset_y,
        args.crop_offset_x,
        args.rotate_order,
        args.rotate_prefilter,
    )
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.save(out_path)
    print(f"wrote: {out_path} (experimental kirakira slice)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
