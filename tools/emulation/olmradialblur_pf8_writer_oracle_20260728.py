#!/usr/bin/env python3
"""Bounded static oracle for OLMRadialBlur's Windows PF8 writer.

This models only the statically established ``+0x7bb0`` internal-cell load
through the ``+0x7c14`` pack/store call.  It deliberately does not model the
direct sampler, host processing, or export.
"""

from __future__ import annotations

import math
import struct
from dataclasses import dataclass

F32_ONE_BITS = 0x3F800000


class UnsupportedSemantics(ValueError):
    """The static note does not establish behavior for this input."""


def float32_from_bits(word: int) -> float:
    if not 0 <= word <= 0xFFFFFFFF:
        raise ValueError("float32 word must be an unsigned 32-bit integer")
    return struct.unpack("<f", struct.pack("<I", word))[0]


def float32_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def _finite_nonnegative(word: int, name: str) -> float:
    value = float32_from_bits(word)
    if not math.isfinite(value):
        raise UnsupportedSemantics(
            f"{name}: NaN/Inf behavior is not established by the static boundary"
        )
    if value < 0.0:
        raise UnsupportedSemantics(
            f"{name}: no lower clamp or negative conversion semantics are established"
        )
    return value


def _mul_f32(left: float, right: float, name: str) -> float:
    try:
        result = float32_from_bits(float32_bits(left * right))
    except OverflowError as exc:
        raise UnsupportedSemantics(f"{name}: float32 overflow is unsupported") from exc
    if not math.isfinite(result):
        raise UnsupportedSemantics(f"{name}: non-finite product is unsupported")
    return result


def internal_cell_address(internal_base: int, x: int, y: int, width: int) -> int:
    """Address shared by the sampler destination and the +0x7bb0 load."""
    if min(internal_base, x, y, width) < 0 or width == 0 or x >= width:
        raise ValueError("invalid internal-frame geometry")
    return internal_base + 16 * (y * width + x)


def pf8_destination_address(
    data_pointer: int, rowbytes: int, x: int, y: int, width: int, height: int
) -> int:
    """PF-world address returned before the +0x7c14 call."""
    if min(data_pointer, rowbytes, x, y, width, height) < 0:
        raise ValueError("invalid PF8 world geometry")
    if width == 0 or height == 0 or x >= width or y >= height:
        raise ValueError("pixel lies outside the PF8 world")
    if rowbytes < width * 4:
        raise ValueError("PF8 rowbytes is smaller than width * 4")
    return data_pointer + y * rowbytes + x * 4


@dataclass(frozen=True)
class PF8WriterResult:
    """Raw boundary values and the concrete ARGB store."""

    internal_address: int
    destination_address: int
    cell_raw_rgba: tuple[int, int, int, int]
    gain_raw: int
    scale_raw: int
    call_raw_xmm0123: tuple[int, int, int, int]
    stored_argb: tuple[int, int, int, int]
    boundary: str = "OLMRadialBlur+0x7bb0 -> +0x7c14"


def evaluate_pf8_writer(
    *,
    cell_raw_rgba: tuple[int, int, int, int],
    gain_raw: int,
    scale_raw: int,
    internal_base: int,
    data_pointer: int,
    rowbytes: int,
    width: int,
    height: int,
    x: int,
    y: int,
    observed_sampler_destination: int | None = None,
    observed_writer_cell: int | None = None,
    observed_destination: int | None = None,
) -> PF8WriterResult:
    """Evaluate the proven PF8 writer subset, failing closed outside it.

    Inputs are raw float32 words so a witness can retain the exact bits.  RGB
    is multiplied by the float32 gain and upper-clamped to 1.0.  Alpha is
    passed to the packer unchanged.  All four packer arguments are multiplied
    by the observed float32 scale and truncated toward zero, then stored ARGB.
    """
    if len(cell_raw_rgba) != 4:
        raise ValueError("cell_raw_rgba must contain exactly four words")
    rgba = tuple(
        _finite_nonnegative(word, f"cell[{index}]")
        for index, word in enumerate(cell_raw_rgba)
    )
    gain = _finite_nonnegative(gain_raw, "brightness gain")
    scale = _finite_nonnegative(scale_raw, "PF8 scale")

    internal = internal_cell_address(internal_base, x, y, width)
    destination = pf8_destination_address(
        data_pointer, rowbytes, x, y, width, height
    )
    for name, observed, expected in (
        ("sampler destination", observed_sampler_destination, internal),
        ("+0x7bb0 writer cell", observed_writer_cell, internal),
        ("+0x7c14 destination", observed_destination, destination),
    ):
        if observed is not None and observed != expected:
            raise ValueError(f"{name} relation failed: {observed:#x} != {expected:#x}")

    rgb = tuple(
        min(_mul_f32(value, gain, f"RGB[{i}]"), 1.0)
        for i, value in enumerate(rgba[:3])
    )
    # Preserve alpha's loaded raw word: it bypasses gain and MINSS.
    call_raw = tuple(float32_bits(value) for value in rgb) + (cell_raw_rgba[3],)
    call_values = rgb + (rgba[3],)
    converted = []
    for index, value in enumerate(call_values):
        scaled = _mul_f32(value, scale, f"packer channel[{index}]")
        integer = math.trunc(scaled)
        if not 0 <= integer <= 255:
            raise UnsupportedSemantics(
                "byte overflow/wrap behavior is outside the established normalized PF8 subset"
            )
        converted.append(integer)
    r, g, b, a = converted
    return PF8WriterResult(
        internal_address=internal,
        destination_address=destination,
        cell_raw_rgba=tuple(cell_raw_rgba),
        gain_raw=gain_raw,
        scale_raw=scale_raw,
        call_raw_xmm0123=call_raw,
        stored_argb=(a, r, g, b),
    )


def export_oracle(*_args: object, **_kwargs: object) -> None:
    """Reject the tempting but unproven PF-world-to-export inference."""
    raise UnsupportedSemantics(
        "the static boundary proves a PF8 world store, not host/export bytes"
    )
