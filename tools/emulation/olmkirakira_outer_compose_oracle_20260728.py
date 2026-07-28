#!/usr/bin/env python3
"""Binary-grounded pure oracle for OLMKiraKira outer compose/writeback.

This models one pixel in the three depth-specific outer loops
FUN_18114ddc0/FUN_18114e110/FUN_18114e460.  Inputs and every scalar
MULSS/ADDSS/DIVSS result are materialized as IEEE-754 binary32.

The boundary ends at the proven typed writer leaves: PF8/PF16 scale the
already-clamped RGBA values and truncate toward zero, and PF32 preserves the
float words.  Returned writer bytes are ARGB.  This is not a model of an AE
host surface, export conversion, or production compatibility.
"""

from __future__ import annotations

import struct
import math
from collections.abc import Sequence


RGBA = tuple[float, float, float, float]
VALID_MODES = (1, 2)
VALID_DEPTHS = ("PF8", "PF16", "PF32")


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


def _reciprocal_f32(value: float) -> float:
    """Materialize the DIVSS 1.0f/value result, including a zero divisor."""

    value = f32(value)
    if value == 0.0:
        return f32(math.copysign(math.inf, value))
    return f32(f32(1.0) / value)


def _rgba(value: Sequence[float], name: str) -> RGBA:
    if len(value) != 4:
        raise ValueError(f"{name} must contain exactly R, G, B, A")
    return tuple(f32(component) for component in value)  # type: ignore[return-value]


def compose_pixel(
    glow: Sequence[float],
    source: Sequence[float],
    *,
    glow_opacity: float,
    source_opacity: float,
    merge_mode: int,
) -> RGBA:
    """Replay the binary outer-compose scalar steps for one RGBA pixel."""

    if merge_mode not in VALID_MODES:
        raise ValueError("merge_mode must be 1 or 2")
    glow32 = _rgba(glow, "glow")
    source32 = _rgba(source, "source")

    # The branch tests the unscaled input-alpha sum, not either scaled alpha.
    raw_alpha_sum = f32(glow32[3] + source32[3])
    if raw_alpha_sum == f32(0.0):
        return (f32(0.0), f32(0.0), f32(0.0), f32(0.0))

    glow_alpha = clamp_fun_181156740(f32(glow32[3] * f32(glow_opacity)))
    source_alpha = clamp_fun_181156740(
        f32(f32(source_opacity) * source32[3])
    )
    alpha_sum = f32(source_alpha + glow_alpha)

    weighted = tuple(
        f32(
            f32(source_alpha * source32[channel])
            + f32(glow_alpha * glow32[channel])
        )
        for channel in range(3)
    )

    if merge_mode == 1:
        reciprocal_alpha = _reciprocal_f32(alpha_sum)
        rgb = tuple(
            clamp_fun_181156740(f32(value * reciprocal_alpha))
            for value in weighted
        )
    else:
        rgb = tuple(clamp_fun_181156740(value) for value in weighted)

    return (rgb[0], rgb[1], rgb[2], clamp_fun_181156740(alpha_sum))


def stage_typed_writer(rgba: Sequence[float], *, depth: str) -> bytes:
    """Stage one proven typed writer result as packed ARGB bytes."""

    if depth not in VALID_DEPTHS:
        raise ValueError("depth must be PF8, PF16, or PF32")
    red, green, blue, alpha = _rgba(rgba, "rgba")
    argb = (alpha, red, green, blue)
    if depth == "PF32":
        return struct.pack("<4f", *argb)

    scale = f32(255.0 if depth == "PF8" else 32768.0)
    words = tuple(int(f32(value * scale)) for value in argb)
    if depth == "PF8":
        return struct.pack("<4B", *words)
    return struct.pack("<4H", *words)


__all__ = [
    "RGBA",
    "VALID_DEPTHS",
    "VALID_MODES",
    "clamp_fun_181156740",
    "compose_pixel",
    "f32",
    "stage_typed_writer",
]
