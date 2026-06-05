#!/usr/bin/env python3
"""Experimental AE-free OLMRadialBlur CLI.

This is the first Rotation/no-noise slice, meant to produce measurable diffs
against the Windows references while the full polar-grid implementation is
being reconstructed from decomp/OLMRadialBlur.aex.c.txt.

Implemented slice:
  - Blur Type 2 (Rotation)
  - outer blur only by default; inner blur is a separate experimental probe
  - no Noise Variation / Size Variation
  - direct angular sampling around the scaled Center

It is intentionally not advertised as exact. See notes/OLMRadialBlur_RE.md.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image
from scipy import signal


def grouped_params(payload: dict[str, Any]) -> dict[str, Any]:
    params = payload.get("params", payload)
    effects = params.get("effects", []) if isinstance(params, dict) else []
    out: dict[str, Any] = {}
    for effect in effects:
        if effect.get("name") != "OLM RadialBlur" and effect.get("match_name") != "OLM RadialBlur":
            continue
        group = "root"
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
            if group in {"outer", "inner"} and name in {
                "Strength",
                "Offset Mode",
                "Offset",
                "Edge Fade",
            }:
                key = f"{group}_{key}"
            elif group == "noise" and name == "Offset":
                key = "noise_offset"
            if key:
                out[key] = param["value"]
    return out


def load_params(params_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    payload = json.loads(params_path.read_text())
    return grouped_params(payload), payload


def bilinear_premul(src: np.ndarray, x: np.ndarray, y: np.ndarray, repeat: bool) -> np.ndarray:
    h, w = src.shape[:2]
    if repeat:
        x = np.clip(x, 0.0, w - 1.0)
        y = np.clip(y, 0.0, h - 1.0)
        valid = np.ones(x.shape, dtype=bool)
    else:
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


def premultiply(arr: np.ndarray) -> np.ndarray:
    f = arr.astype(np.float32) / 255.0
    f[..., :3] *= f[..., 3:4]
    return f


def unpremultiply(arr: np.ndarray) -> np.ndarray:
    out = arr.copy()
    alpha = out[..., 3:4]
    mask = alpha[..., 0] > 1e-8
    out[..., :3][mask] /= alpha[mask]
    out = np.clip(out, 0.0, 1.0)
    return np.rint(out * 255.0).astype(np.uint8)


def quantize_rgba(arr: np.ndarray, mode: str = "round") -> np.ndarray:
    arr = np.clip(arr, 0.0, 1.0) * 255.0
    if mode == "floor":
        return np.floor(arr).astype(np.uint8)
    if mode == "ceil":
        return np.ceil(arr).astype(np.uint8)
    return np.rint(arr).astype(np.uint8)


def gaussian_weights(length: int) -> np.ndarray:
    """Match FUN_18000b680 + FUN_180001c90 Gaussian lookup."""
    if length <= 1:
        return np.ones(1, dtype=np.float32)
    table_len = 30000
    denom = float(table_len * table_len) * 2.0 * 0.111111119389534 + 1.0e-5
    inv_denom = 1.0 / denom
    idx_scale = int(table_len / length)
    weights = np.ones(length, dtype=np.float32)
    for i in range(1, length):
        table_index = int(float(i) * float(idx_scale))
        weights[i] = math.exp(-(table_index * table_index) * inv_denom)
    return weights


def zoom_gaussian_weights(length: int) -> np.ndarray:
    """Match Zoom's direct FUN_18000b680 lookup table."""
    if length <= 1:
        return np.ones(1, dtype=np.float32)
    denom = float(length * length) * 2.0 * 0.111111119389534 + 1.0e-5
    inv_denom = 1.0 / denom
    weights = np.ones(length, dtype=np.float32)
    for i in range(length):
        weights[i] = math.exp(-(i * i) * inv_denom)
    return weights


def sample_grid_alpha_normalized(grid: np.ndarray, x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Sample straight RGBA like FUN_180001000: wrap X, alpha-weight RGB."""
    h, w = grid.shape[:2]
    xi = np.floor(x).astype(np.int32)
    yi = np.floor(y).astype(np.int32)
    fx = (x - xi)[..., None]
    fy = (y - yi)[..., None]

    x0 = xi % w
    x1 = (xi + 1) % w
    y0 = np.clip(yi, 0, h - 1)
    y1 = np.clip(yi + 1, 0, h - 1)

    c00 = grid[y0, x0]
    c10 = grid[y0, x1]
    c01 = grid[y1, x0]
    c11 = grid[y1, x1]
    w00 = (1.0 - fx) * (1.0 - fy)
    w10 = fx * (1.0 - fy)
    w01 = (1.0 - fx) * fy
    w11 = fx * fy

    a00 = c00[..., 3:4] * w00
    a10 = c10[..., 3:4] * w10
    a01 = c01[..., 3:4] * w01
    a11 = c11[..., 3:4] * w11
    alpha = a00 + a10 + a01 + a11
    rgb = c00[..., :3] * a00 + c10[..., :3] * a10 + c01[..., :3] * a01 + c11[..., :3] * a11
    out = np.zeros((*x.shape, 4), dtype=np.float32)
    mask = alpha[..., 0] > 1e-8
    out[..., :3][mask] = rgb[mask] / alpha[mask]
    out[..., 3] = alpha[..., 0]
    return out


def sample_zoom_grid_alpha_normalized(grid: np.ndarray, radius_x: np.ndarray, angle_y: np.ndarray) -> np.ndarray:
    """Sample Zoom's angle-major polar grid like FUN_180009d80."""
    h, w = grid.shape[:2]
    xi = np.floor(radius_x).astype(np.int32)
    yi = np.floor(angle_y).astype(np.int32)
    fx = (radius_x - xi)[..., None]
    fy = (angle_y - yi)[..., None]

    x0 = np.clip(xi, 0, w - 1)
    x1 = np.clip(xi + 1, 0, w - 1)
    y0 = yi % h
    y1 = (yi + 1) % h

    c00 = grid[y0, x0]
    c10 = grid[y0, x1]
    c01 = grid[y1, x0]
    c11 = grid[y1, x1]
    w00 = (1.0 - fx) * (1.0 - fy)
    w10 = fx * (1.0 - fy)
    w01 = (1.0 - fx) * fy
    w11 = fx * fy

    a00 = c00[..., 3:4] * w00
    a10 = c10[..., 3:4] * w10
    a01 = c01[..., 3:4] * w01
    a11 = c11[..., 3:4] * w11
    alpha = a00 + a10 + a01 + a11
    rgb = c00[..., :3] * a00 + c10[..., :3] * a10 + c01[..., :3] * a01 + c11[..., :3] * a11
    out = np.zeros((*radius_x.shape, 4), dtype=np.float32)
    mask = alpha[..., 0] > 1e-8
    out[..., :3][mask] = rgb[mask] / alpha[mask]
    out[..., 3] = alpha[..., 0]
    return out


def circular_scatter_sum(values: np.ndarray, weights: np.ndarray, direction: str) -> np.ndarray:
    """Circular one-sided scatter along angle axis.

    For forward scatter this matches dest[j] = sum_i src[j-i] * weights[i].
    """
    if len(weights) <= 1:
        return values * float(weights[0])

    n = values.shape[1]
    kernel = np.zeros(n, dtype=np.float32)
    offsets = np.arange(len(weights), dtype=np.int32)
    if direction == "forward":
        np.add.at(kernel, offsets % n, weights)
    else:
        np.add.at(kernel, (-offsets) % n, weights)

    f_values = np.fft.rfft(values, axis=1)
    f_kernel = np.fft.rfft(kernel)
    out = np.fft.irfft(f_values * f_kernel.reshape((1, -1) + (1,) * (values.ndim - 2)), n=n, axis=1)
    return out.astype(np.float32, copy=False)


def linear_scatter_sum(values: np.ndarray, weights: np.ndarray, direction: str) -> np.ndarray:
    """One-sided non-wrapping scatter along the radius axis."""
    if len(weights) <= 1:
        return values * float(weights[0])
    if direction == "reverse":
        return linear_scatter_sum(values[:, ::-1], weights, "forward")[:, ::-1].copy()

    kernel = weights.reshape((1, len(weights)) + (1,) * (values.ndim - 2))
    full = signal.fftconvolve(values, kernel, mode="full", axes=(1,))
    return full[:, : values.shape[1]].astype(np.float32, copy=False)


def scatter_accumulate(
    straight: np.ndarray, alpha: np.ndarray, weights: np.ndarray, direction: str
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Accumulate angular scatter; exact roll path for small kernels."""
    if len(weights) < 64:
        accum_rgb = straight[..., :3] * alpha[..., None]
        accum_sum = alpha.copy()
        accum_alpha = alpha.copy()
        for i in range(1, len(weights)):
            shift = i if direction == "forward" else -i
            contribution = alpha * weights[i]
            rolled = np.roll(contribution, shift, axis=1)
            accum_rgb += np.roll(straight[..., :3] * contribution[..., None], shift, axis=1)
            accum_sum += rolled
            accum_alpha = np.maximum(accum_alpha, rolled)
        return accum_rgb, accum_sum, accum_alpha

    weighted_alpha = circular_scatter_sum(alpha, weights, direction)
    weighted_rgb = circular_scatter_sum(straight[..., :3] * alpha[..., None], weights, direction)
    return weighted_rgb, weighted_alpha, alpha.copy()


def combined_scatter_accumulate(
    straight: np.ndarray,
    alpha: np.ndarray,
    outer_weights: np.ndarray,
    inner_weights: np.ndarray,
    inner_alpha_mode: str = "max",
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Outer scatters forward; inner scatters backward. Count source once."""
    outer_rgb, outer_sum, outer_alpha = scatter_accumulate(straight, alpha, outer_weights, "forward")
    if len(inner_weights) <= 1:
        return outer_rgb, outer_sum, outer_alpha

    inner_rgb, inner_sum, inner_alpha = scatter_accumulate(straight, alpha, inner_weights, "reverse")
    source_rgb = straight[..., :3] * alpha[..., None]
    combined_sum = outer_sum + inner_sum - alpha
    if inner_alpha_mode == "sum":
        accum_alpha = np.clip(combined_sum, 0.0, 1.0)
    elif inner_alpha_mode == "outer":
        accum_alpha = outer_alpha
    elif inner_alpha_mode == "inner":
        accum_alpha = inner_alpha
    elif inner_alpha_mode == "input":
        accum_alpha = alpha.copy()
    else:
        accum_alpha = np.maximum(outer_alpha, inner_alpha)
    return (
        outer_rgb + inner_rgb - source_rgb,
        combined_sum,
        accum_alpha,
    )


def effective_length(base_strength: int, offset_mode: int, dynamic_offset: int) -> int:
    """FUN_180001c90 combines strength and the per-radius offset span."""
    if offset_mode == 1:
        span = base_strength + dynamic_offset
    elif offset_mode == 2:
        span = max(base_strength, dynamic_offset)
    elif offset_mode == 3:
        span = dynamic_offset
    else:
        span = base_strength
    # The source sample is accumulated separately; the blur tail is span - 1.
    return max(0, min(span - 1, 3000))


def zoom_effective_length(base_strength: int, offset_mode: int, offset: int) -> int:
    """Zoom uses the resulting radius span directly as its lookup length."""
    if offset_mode == 1:
        # case_0003..0005 fit the Windows reference only when Offset Mode=1
        # does not extend the radius-table length. The offset likely feeds a
        # separate pass detail that is still unmodeled for harder cases.
        span = base_strength
    elif offset_mode == 2:
        span = max(base_strength, offset)
    elif offset_mode == 3:
        span = offset
    else:
        span = base_strength
    return max(0, min(span, 3000))


def dynamic_offset_for_radius(radius_count: int, offset: int, radius_index: int) -> int:
    """Mirror FUN_1800024c0's radius-dependent offset argument."""
    if offset <= 0:
        return 0
    return int(float((radius_count // 2) * offset) / float(max(1, radius_index + 1)))


def variable_scatter_accumulate(
    straight: np.ndarray,
    alpha: np.ndarray,
    outer_strength: int,
    outer_offset_mode: int,
    outer_offset: int,
    inner_strength: int,
    inner_offset_mode: int,
    inner_offset: int,
    inner_alpha_mode: str = "max",
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Per-radius variant of combined_scatter_accumulate.

    Offset Mode uses a dynamic radius-dependent span in FUN_1800024c0 before
    FUN_180001c90 combines it with Strength. Rows without offsets share the
    same fast FFT path; rows with offsets are grouped by effective length.
    """
    rows = straight.shape[0]
    accum_rgb = np.zeros_like(straight[..., :3])
    accum_sum = np.zeros_like(alpha)
    accum_alpha = alpha.copy()
    weight_cache: dict[int, np.ndarray] = {}

    for ri in range(rows):
        outer_dynamic = dynamic_offset_for_radius(rows, outer_offset, ri)
        inner_dynamic = dynamic_offset_for_radius(rows, inner_offset, ri)
        outer_length = effective_length(outer_strength, outer_offset_mode, outer_dynamic)
        inner_length = effective_length(inner_strength, inner_offset_mode, inner_dynamic)

        outer_weights = weight_cache.get(outer_length)
        if outer_weights is None:
            outer_weights = gaussian_weights(outer_length)
            weight_cache[outer_length] = outer_weights
        inner_weights = weight_cache.get(inner_length)
        if inner_weights is None:
            inner_weights = gaussian_weights(inner_length)
            weight_cache[inner_length] = inner_weights

        rgb, sum_, alpha_max = combined_scatter_accumulate(
            straight[ri : ri + 1],
            alpha[ri : ri + 1],
            outer_weights,
            inner_weights,
            inner_alpha_mode,
        )
        accum_rgb[ri] = rgb[0]
        accum_sum[ri] = sum_[0]
        accum_alpha[ri] = alpha_max[0]

    return accum_rgb, accum_sum, accum_alpha


def render_rotation(
    image: Image.Image,
    params: dict[str, Any],
    payload: dict[str, Any],
    direction: str = "outer",
) -> Image.Image:
    rgba = np.asarray(image.convert("RGBA"), dtype=np.uint8)
    h, w = rgba.shape[:2]
    src = premultiply(rgba)

    comp = payload.get("comp") if isinstance(payload.get("comp"), dict) else {}
    comp_w = float(comp.get("width") or w)
    comp_h = float(comp.get("height") or h)
    scale_x = w / comp_w
    scale_y = h / comp_h

    center = params.get("center") or [comp_w * 0.5, comp_h * 0.5]
    cx = float(center[0]) * scale_x
    cy = float(center[1]) * scale_y
    ratio = float(params.get("ratio") or 1.0)
    base_angle = math.radians(float(params.get("angle") or 0.0))
    repeat = bool(params.get("repeat_border", 1))
    quality = float(params.get("quality") or 5.0)
    strength = float(params.get("outer_strength") or 0.0)
    inner_strength = float(params.get("inner_strength") or 0.0)

    if int(params.get("blur_type") or 0) != 2:
        raise SystemExit("olmradialblur_cli.py currently implements only Blur Type=2 (Rotation)")
    if float(params.get("noise_variation") or 0.0) != 0.0:
        raise SystemExit("olmradialblur_cli.py currently does not implement Noise Variation")
    if float(params.get("size_variation") or 0.0) != 0.0:
        raise SystemExit("olmradialblur_cli.py currently does not implement Size Variation")

    # AEX stores quality as 1 / Quality, builds an angular grid with that
    # degree step, then converts Strength into grid samples. So Strength=4 at
    # Quality=5 means 4 * 0.2deg, not 4deg.
    step_deg = 1.0 / quality if quality > 0 else 0.2
    forward_steps = np.arange(0, int(strength) + 1, dtype=np.float32)
    backward_steps = np.arange(1, int(inner_strength) + 1, dtype=np.float32)
    forward = forward_steps * step_deg
    backward = -backward_steps * step_deg
    if direction == "reverse-outer":
        forward = -forward
    elif direction == "symmetric-outer":
        forward = np.concatenate([-forward_steps[:0:-1] * step_deg, forward])
    offsets = np.concatenate([backward[::-1], forward])
    if offsets.size == 0:
        offsets = np.array([0.0], dtype=np.float32)

    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    dx = xx - cx
    dy = yy - cy
    cos_a = math.cos(base_angle)
    sin_a = math.sin(base_angle)
    # Rotate into the ellipse frame; angle=0 in the first target case.
    ex = cos_a * dx + sin_a * dy
    ey = (cos_a * dy - sin_a * dx) / ratio
    radius = np.sqrt(ex * ex + ey * ey)
    theta = np.arctan2(ey, ex)

    accum = np.zeros_like(src, dtype=np.float32)
    for deg in offsets:
        t = theta + math.radians(float(deg))
        sx0 = np.cos(t) * radius
        sy0 = np.sin(t) * radius * ratio
        sx = cx + cos_a * sx0 - sin_a * sy0
        sy = cy + sin_a * sx0 + cos_a * sy0
        accum += bilinear_premul(src, sx, sy, repeat)
    accum /= float(offsets.size)

    gain = float(params.get("brightness_gain") or 1.0)
    accum[..., :3] *= gain
    return Image.fromarray(unpremultiply(accum), "RGBA")


def render_rotation_polar(
    image: Image.Image,
    params: dict[str, Any],
    payload: dict[str, Any],
    polar_direction: str = "forward",
    quantize: str = "floor",
    ignore_offset: bool = False,
    ignore_inner: bool = False,
    experimental_inner: bool = False,
    inner_alpha_mode: str = "max",
    rotation_quality_scale: str = "none",
) -> Image.Image:
    """AEX-shaped Rotation experiment: polar grid, angular scatter, inverse lookup.

    This implements the simple case_0010 class: outer blur, no offset/no inner,
    no size/noise variation. It follows FUN_180004640 + FUN_180001c90 at a high
    level while leaving the more complex edge-fade/validity paths for later.
    """

    rgba = np.asarray(image.convert("RGBA"), dtype=np.uint8)
    h, w = rgba.shape[:2]
    src = rgba.astype(np.float32) / 255.0

    comp = payload.get("comp") if isinstance(payload.get("comp"), dict) else {}
    comp_w = float(comp.get("width") or w)
    comp_h = float(comp.get("height") or h)
    scale_x = w / comp_w
    scale_y = h / comp_h

    center = params.get("center") or [comp_w * 0.5, comp_h * 0.5]
    cx = float(center[0]) * scale_x
    cy = float(center[1]) * scale_y
    ratio = float(params.get("ratio") or 1.0)
    base_angle = math.radians(float(params.get("angle") or 0.0))
    repeat = bool(params.get("repeat_border", 1))
    quality = float(params.get("quality") or 5.0)
    quality_scale = quality / 5.0 if quality > 0 and rotation_quality_scale == "aex" else 1.0
    strength = int(float(params.get("outer_strength") or 0.0) * quality_scale)
    outer_offset_mode = int(float(params.get("outer_offset_mode") or 1.0))
    outer_offset = 0 if ignore_offset else int(float(params.get("outer_offset") or 0.0) * quality_scale)
    raw_inner_strength_ui = float(params.get("inner_strength") or 0.0)
    raw_inner_strength = int(raw_inner_strength_ui * quality_scale)
    if raw_inner_strength_ui != 0.0 and not (ignore_inner or experimental_inner):
        raise SystemExit("polar mode inner blur is not validated; pass --experimental-inner to probe it")
    inner_strength = 0 if ignore_inner else raw_inner_strength
    inner_offset_mode = int(float(params.get("inner_offset_mode") or 1.0))
    inner_offset = (
        0
        if ignore_offset or ignore_inner
        else int(float(params.get("inner_offset") or 0.0) * quality_scale)
    )

    if int(params.get("blur_type") or 0) != 2:
        raise SystemExit("polar mode currently implements only Blur Type=2")
    if float(params.get("noise_variation") or 0.0) != 0.0:
        raise SystemExit("polar mode currently does not implement Noise Variation")
    if float(params.get("size_variation") or 0.0) != 0.0:
        raise SystemExit("polar mode currently does not implement Size Variation")

    step_deg = 1.0 / quality if quality > 0 else 0.2
    angular_count = int(360.0 / step_deg)

    # FUN_180001bb0: radius bounds around the center, then min/ratio - 2 and
    # max + 2. For centered case_0010 this becomes 0..1103.
    left = max(0.0, -cx)
    right = max(0.0, cx - w, w - cx if cx <= w / 2 else cx)
    top = max(0.0, -cy)
    bottom = max(0.0, cy - h, h - cy if cy <= h / 2 else cy)
    min_r = max(0, int(math.sqrt(left * left + top * top) / ratio) - 2)
    max_r = int(math.sqrt(max(left, right) ** 2 + max(top, bottom) ** 2)) + 2
    radii = np.arange(min_r, max_r + 1, dtype=np.float32)

    theta = np.deg2rad(np.arange(angular_count, dtype=np.float32) * step_deg)
    cos_t = np.cos(theta)
    sin_t = np.sin(theta)
    cos_a = math.cos(base_angle)
    sin_a = math.sin(base_angle)

    polar = np.empty((len(radii), angular_count, 4), dtype=np.float32)
    for ri, r in enumerate(radii):
        sx0 = cos_t * r
        sy0 = sin_t * r * ratio
        sx = cx + cos_a * sx0 - sin_a * sy0
        sy = cy + sin_a * sx0 + cos_a * sy0
        polar[ri] = bilinear_premul(src, sx, sy, repeat)

    # The 8-bit AEX path stores straight RGB + alpha floats before the polar
    # scatter. The helper name is historical; here it is just bilinear RGBA.
    alpha = polar[..., 3]
    straight = polar

    if polar_direction == "forward":
        if outer_offset or inner_offset:
            weighted_rgb, weighted_alpha, accum_alpha = variable_scatter_accumulate(
                straight,
                alpha,
                strength,
                outer_offset_mode,
                outer_offset,
                inner_strength,
                inner_offset_mode,
                inner_offset,
                inner_alpha_mode,
            )
        else:
            # FUN_180001c90 handles the source sample separately; the Gaussian
            # lookup length used for additional angular samples is effectively
            # one less than the UI strength span. This is especially visible in
            # case_0010 where Strength=4 fits only with a 3-sample blur tail.
            outer_weights = gaussian_weights(effective_length(strength, outer_offset_mode, 0))
            inner_weights = gaussian_weights(effective_length(inner_strength, inner_offset_mode, 0))
            weighted_rgb, weighted_alpha, accum_alpha = combined_scatter_accumulate(
                straight, alpha, outer_weights, inner_weights, inner_alpha_mode
            )
    else:
        outer_weights = gaussian_weights(effective_length(strength, outer_offset_mode, 0))
        inner_weights = gaussian_weights(effective_length(inner_strength, inner_offset_mode, 0))
        weighted_rgb, weighted_alpha, accum_alpha = combined_scatter_accumulate(
            straight, alpha, inner_weights, outer_weights, inner_alpha_mode
        )

    blurred = np.zeros_like(straight)
    nz = weighted_alpha > 1e-8
    blurred[..., :3][nz] = weighted_rgb[nz] / weighted_alpha[nz, None]
    blurred[..., 3] = accum_alpha

    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    dx = xx - cx
    dy = yy - cy
    ex = cos_a * dx + sin_a * dy
    ey = (cos_a * dy - sin_a * dx) / ratio
    radius = np.sqrt(ex * ex + ey * ey)
    angle = np.arctan2(ey, ex)
    angle = np.where(angle < 0.0, angle + math.tau, angle)
    angle_index = angle / math.radians(step_deg)
    radius_index = radius - float(min_r)

    sampled = sample_grid_alpha_normalized(blurred, angle_index, radius_index)
    gain = float(params.get("brightness_gain") or 1.0)
    sampled[..., :3] *= gain
    return Image.fromarray(quantize_rgba(sampled, quantize), "RGBA")


def render_zoom_direct(
    image: Image.Image,
    params: dict[str, Any],
    payload: dict[str, Any],
    quantize: str = "floor",
) -> Image.Image:
    """First experimental Blur Type=1 Zoom probe.

    This is deliberately simpler than FUN_1800056f0. It samples inward along
    the center ray so Type=1 references can enter the AE-free harness while the
    true zoom/radial-grid path is reconstructed.
    """
    rgba = np.asarray(image.convert("RGBA"), dtype=np.uint8).astype(np.float32) / 255.0
    h, w = rgba.shape[:2]

    comp = payload.get("comp") if isinstance(payload.get("comp"), dict) else {}
    comp_w = float(comp.get("width") or w)
    comp_h = float(comp.get("height") or h)
    scale_x = w / comp_w
    scale_y = h / comp_h
    center = params.get("center") or [comp_w * 0.5, comp_h * 0.5]
    cx = float(center[0]) * scale_x
    cy = float(center[1]) * scale_y

    if int(params.get("blur_type") or 0) != 1:
        raise SystemExit("zoom-direct mode implements only Blur Type=1")
    if float(params.get("noise_variation") or 0.0) != 0.0:
        raise SystemExit("zoom-direct mode currently does not implement Noise Variation")
    if float(params.get("size_variation") or 0.0) != 0.0:
        raise SystemExit("zoom-direct mode currently does not implement Size Variation")
    if float(params.get("inner_strength") or 0.0) != 0.0:
        raise SystemExit("zoom-direct mode currently does not implement Inner Blur")

    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    dx = xx - cx
    dy = yy - cy

    # Empirical first slice for case_0009. The real AEX path maps Strength and
    # Quality through FUN_1800056f0/FUN_18000b150; this keeps the behavior in
    # the right family without claiming exactness.
    samples = 8
    zoom_span = 0.08
    accum = np.zeros_like(rgba)
    for i in range(samples):
        t = -zoom_span * (float(i) / float(samples - 1))
        accum += bilinear_premul(rgba, cx + dx * (1.0 + t), cy + dy * (1.0 + t), True)
    accum /= float(samples)
    gain = float(params.get("brightness_gain") or 1.0)
    accum[..., :3] *= gain
    return Image.fromarray(quantize_rgba(accum, quantize), "RGBA")


def render_zoom_polar(
    image: Image.Image,
    params: dict[str, Any],
    payload: dict[str, Any],
    quantize: str = "floor",
    zoom_direction: str = "forward",
    zoom_radius_offset: float = 0.0,
    zoom_angle_offset: float = 0.0,
    zoom_strength_scale: float = 1.0,
    ignore_size_variation: bool = False,
) -> Image.Image:
    """AEX-shaped Blur Type=1 probe using Zoom's angle/radius grid."""
    rgba = np.asarray(image.convert("RGBA"), dtype=np.uint8).astype(np.float32) / 255.0
    h, w = rgba.shape[:2]

    comp = payload.get("comp") if isinstance(payload.get("comp"), dict) else {}
    comp_w = float(comp.get("width") or w)
    comp_h = float(comp.get("height") or h)
    scale_x = w / comp_w
    scale_y = h / comp_h
    center = params.get("center") or [comp_w * 0.5, comp_h * 0.5]
    cx = float(center[0]) * scale_x
    cy = float(center[1]) * scale_y
    ratio = float(params.get("ratio") or 1.0)
    base_angle = math.radians(float(params.get("angle") or 0.0))
    repeat = bool(params.get("repeat_border", 1))
    quality = float(params.get("quality") or 5.0)
    strength = int(float(params.get("outer_strength") or 0.0))
    outer_offset_mode = int(float(params.get("outer_offset_mode") or 1.0))
    outer_offset = int(float(params.get("outer_offset") or 0.0))
    inner_strength = int(float(params.get("inner_strength") or 0.0))
    inner_offset_mode = int(float(params.get("inner_offset_mode") or 1.0))
    inner_offset = int(float(params.get("inner_offset") or 0.0))

    if int(params.get("blur_type") or 0) != 1:
        raise SystemExit("zoom-polar mode implements only Blur Type=1")
    if float(params.get("noise_variation") or 0.0) != 0.0:
        raise SystemExit("zoom-polar mode currently does not implement Noise Variation")
    if float(params.get("size_variation") or 0.0) != 0.0 and not ignore_size_variation:
        raise SystemExit("zoom-polar mode currently does not implement Size Variation")
    if inner_strength != 0:
        raise SystemExit("zoom-polar mode currently does not implement Inner Blur")

    step_deg = 1.0 / quality if quality > 0 else 0.2
    step_rad = math.radians(step_deg)
    angular_count = int(360.0 / step_deg)

    # FUN_18000a8f0: min/max distance from Center to image bounds, then
    # min/radius-ratio - 2 and max + 2.
    min_dx = 0.0 if 0.0 <= cx < w else abs(cx if cx < 0.0 else cx - w)
    min_dy = 0.0 if 0.0 <= cy < h else abs(cy if cy < 0.0 else cy - h)
    if 0.0 <= cx < w:
        max_dx = max(cx, w - cx)
    else:
        max_dx = w - cx if cx < 0.0 else cx
    if 0.0 <= cy < h:
        max_dy = max(cy, h - cy)
    else:
        max_dy = h - cy if cy < 0.0 else cy
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
        polar[ai] = bilinear_premul(rgba, sx, sy, repeat)

    alpha = polar[..., 3]
    # Zoom's radius blur length follows the UI Strength value itself. The
    # angular grid still uses Quality, but FUN_18000a9d0 consumes a radius
    # table whose effective length matches Strength for case_0009.
    outer_length = int(zoom_effective_length(strength, outer_offset_mode, outer_offset) * zoom_strength_scale)
    inner_length = int(zoom_effective_length(inner_strength, inner_offset_mode, inner_offset) * zoom_strength_scale)
    outer_length = max(0, min(outer_length, 3000))
    inner_length = max(0, min(inner_length, 3000))
    outer_weights = zoom_gaussian_weights(outer_length)
    inner_weights = zoom_gaussian_weights(inner_length)

    outer_direction = "reverse" if zoom_direction == "reverse-outer" else "forward"
    weighted_rgb = linear_scatter_sum(polar[..., :3] * alpha[..., None], outer_weights, outer_direction)
    weighted_alpha = linear_scatter_sum(alpha, outer_weights, outer_direction)
    accum_alpha = linear_scatter_sum(alpha, outer_weights, outer_direction)
    if inner_length > 1:
        weighted_rgb += linear_scatter_sum(polar[..., :3] * alpha[..., None], inner_weights, "reverse")
        weighted_alpha += linear_scatter_sum(alpha, inner_weights, "reverse")
        accum_alpha = np.maximum(accum_alpha, linear_scatter_sum(alpha, inner_weights, "reverse"))

    blurred = np.zeros_like(polar)
    nz = weighted_alpha > 1e-8
    blurred[..., :3][nz] = weighted_rgb[nz] / weighted_alpha[nz, None]
    blurred[..., 3] = np.clip(accum_alpha, 0.0, 1.0)

    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    dx = xx - cx
    dy = yy - cy
    ex = cos_a * dx + sin_a * dy
    ey = (cos_a * dy - sin_a * dx) / ratio
    radius = np.sqrt(ex * ex + ey * ey)
    angle = np.arctan2(ey, ex)
    angle = np.where(angle < 0.0, angle + math.tau, angle)
    radius_index = radius - float(min_r) + zoom_radius_offset
    angle_index = angle / step_rad + zoom_angle_offset

    sampled = sample_zoom_grid_alpha_normalized(blurred, radius_index, angle_index)
    gain = float(params.get("brightness_gain") or 1.0)
    sampled[..., :3] *= gain
    return Image.fromarray(quantize_rgba(sampled, quantize), "RGBA")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--params", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--direction",
        choices=["outer", "reverse-outer", "symmetric-outer"],
        default="reverse-outer",
        help="experimental Rotation direction probe",
    )
    parser.add_argument(
        "--algorithm",
        choices=["direct", "polar", "zoom-direct", "zoom-polar"],
        default="direct",
        help="experimental implementation path",
    )
    parser.add_argument(
        "--polar-direction",
        choices=["forward", "reverse"],
        default="forward",
        help="experimental polar scatter direction",
    )
    parser.add_argument(
        "--quantize",
        choices=["round", "floor", "ceil"],
        default="floor",
        help="experimental 8-bit output conversion",
    )
    parser.add_argument("--ignore-offset", action="store_true")
    parser.add_argument("--ignore-inner", action="store_true")
    parser.add_argument("--experimental-inner", action="store_true")
    parser.add_argument(
        "--inner-alpha-mode",
        choices=["max", "sum", "outer", "inner", "input"],
        default="max",
        help="experimental Rotation inner-blur alpha accumulator",
    )
    parser.add_argument(
        "--rotation-quality-scale",
        choices=["none", "aex"],
        default="none",
        help="experimental Rotation Strength/Offset scaling by Quality/5",
    )
    parser.add_argument(
        "--zoom-direction",
        choices=["forward", "reverse-outer"],
        default="forward",
        help="experimental Zoom radial scatter direction",
    )
    parser.add_argument("--zoom-radius-offset", type=float, default=0.0)
    parser.add_argument("--zoom-angle-offset", type=float, default=0.0)
    parser.add_argument("--zoom-strength-scale", type=float, default=1.0)
    parser.add_argument("--ignore-size-variation", action="store_true")
    args = parser.parse_args()

    params, payload = load_params(Path(args.params))
    if args.algorithm == "polar":
        out = render_rotation_polar(
            Image.open(args.input),
            params,
            payload,
            args.polar_direction,
            args.quantize,
            args.ignore_offset,
            args.ignore_inner,
            args.experimental_inner,
            args.inner_alpha_mode,
            args.rotation_quality_scale,
        )
    elif args.algorithm == "zoom-direct":
        out = render_zoom_direct(Image.open(args.input), params, payload, args.quantize)
    elif args.algorithm == "zoom-polar":
        out = render_zoom_polar(
            Image.open(args.input),
            params,
            payload,
            args.quantize,
            args.zoom_direction,
            args.zoom_radius_offset,
            args.zoom_angle_offset,
            args.zoom_strength_scale,
            args.ignore_size_variation,
        )
    else:
        out = render_rotation(Image.open(args.input), params, payload, args.direction)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.save(out_path)
    print(f"wrote: {out_path} (experimental {args.algorithm} slice)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
