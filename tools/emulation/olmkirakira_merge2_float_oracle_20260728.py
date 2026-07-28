#!/usr/bin/env python3
"""Pure-float oracle for the bounded OLMKiraKira Merge Mode 2 aggregator.

The modeled boundary is only FUN_18114ffd0's per-pixel operation order:

* start with zero RGBA;
* visit exactly five layers in order;
* skip a layer unless its float32 ray is strictly greater than the caller's
  explicit skip threshold;
* add the selected float32 RGB directly and the raw float32 ray to alpha;
* after all five layers, clamp R, G, B, and A independently to [0, 1].

The skip threshold is deliberately required.  This module does not resolve
which threshold belongs to a later host lane, and it does not model source
composition, typed writeback, quantization, or AE output.
"""

from __future__ import annotations

import struct
from collections.abc import Sequence


RGBA = tuple[float, float, float, float]
RGB = tuple[float, float, float]
LAYER_COUNT = 5


def f32(value: float) -> float:
    """Round a Python number to an IEEE-754 binary32 value."""

    return struct.unpack("<f", struct.pack("<f", value))[0]


def clamp_fun_181156740(value: float) -> float:
    """Finite-value model of FUN_181156740, with a binary32 result."""

    value = f32(value)
    if value >= f32(1.0):
        value = f32(1.0)
    if value <= f32(0.0):
        value = f32(0.0)
    return value


def aggregate_pixel(
    ray_values: Sequence[float],
    selected_rgb: Sequence[Sequence[float]],
    *,
    skip_threshold: float,
) -> RGBA:
    """Replay FUN_18114ffd0's bounded five-layer aggregation for one pixel.

    ``selected_rgb`` is the already-selected RGB for each layer.  Ramp lookup
    and all producer-side behavior are intentionally outside this oracle.
    """

    if len(ray_values) != LAYER_COUNT:
        raise ValueError(f"ray_values must contain exactly {LAYER_COUNT} layers")
    if len(selected_rgb) != LAYER_COUNT:
        raise ValueError(f"selected_rgb must contain exactly {LAYER_COUNT} layers")
    if any(len(rgb) != 3 for rgb in selected_rgb):
        raise ValueError("each selected_rgb layer must contain exactly R, G, B")

    threshold = float(skip_threshold)
    out = [f32(0.0), f32(0.0), f32(0.0), f32(0.0)]

    for ray_input, rgb_input in zip(ray_values, selected_rgb):
        ray = f32(ray_input)
        if float(ray) <= threshold:
            continue

        out[0] = f32(f32(rgb_input[0]) + out[0])
        out[1] = f32(f32(rgb_input[1]) + out[1])
        out[2] = f32(f32(rgb_input[2]) + out[2])
        out[3] = f32(ray + out[3])

    return (
        clamp_fun_181156740(out[0]),
        clamp_fun_181156740(out[1]),
        clamp_fun_181156740(out[2]),
        clamp_fun_181156740(out[3]),
    )


__all__ = [
    "LAYER_COUNT",
    "RGB",
    "RGBA",
    "aggregate_pixel",
    "clamp_fun_181156740",
    "f32",
]
