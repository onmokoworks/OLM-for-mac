#!/usr/bin/env python3
"""Typed mode-0 adapter fixture.

This is an ABI/plane differential harness, not Mac host/world proof.  It
exercises the exact typed source, component-map, prepass, scatter, denominator,
max-alpha, normalization, and final RGBA stages using the checked-in core
exports.  Production dispatch stays disabled until the Mac host boundary is
proven; no PNG-derived diagonal behavior is asserted here.
"""

from __future__ import annotations

import ctypes
import math
import struct
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def build() -> ctypes.CDLL:
    directory = Path(tempfile.mkdtemp(prefix="olm_dblur_mode0_"))
    library = directory / "libdblur_mode0.so"
    subprocess.run([
        "c++", "-std=c++17", "-O2", "-fno-fast-math", "-ffp-contract=off",
        "-fPIC", "-shared", str(ROOT / "core/dblur_rotate.cpp"),
        str(ROOT / "core/dblur_rowdriver.cpp"), "-o", str(library),
    ], cwd=ROOT, check=True)
    lib = ctypes.CDLL(str(library))
    float_p = ctypes.POINTER(ctypes.c_float)
    lib.olm_dblur_rotate_rgba_f32.argtypes = [float_p, float_p, ctypes.c_int,
                                               ctypes.c_int, ctypes.c_float]
    lib.olm_dblur_rowdriver_f32.argtypes = [
        ctypes.c_int, ctypes.c_int, float_p, float_p, ctypes.c_int, ctypes.c_int,
        ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float,
        ctypes.c_float, float_p, float_p, float_p, float_p, float_p, float_p,
        float_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
    ]
    return lib


def array(values: list[float]) -> ctypes.Array:
    return (ctypes.c_float * len(values))(*[f32(value) for value in values])


def main() -> int:
    lib = build()
    width = height = 5
    pixels = width * height
    source_values = []
    for y in range(height):
        for x in range(width):
            source_values += [0.10 + x * 0.03, 0.20 + y * 0.02,
                              0.30 + (x + y) * 0.01, 1.0]
    source = array(source_values)
    rotated = array([0.0] * (pixels * 4))
    lib.olm_dblur_rotate_rgba_f32(source, rotated, width, height,
                                  ctypes.c_float(math.pi / 2))

    # Mode-0 guard: no size variation/tails means every valid component has
    # area coefficient 1, with the unused map fields zeroed.
    comp_map = array(sum(([1.0, 0.0, 0.0, 1.0] for _ in range(pixels)), []))
    assert list(comp_map)[0:4] == [1.0, 0.0, 0.0, 1.0]
    assert all(comp_map[i * 4] == 1.0 and comp_map[i * 4 + 3] == 1.0
               for i in range(pixels))

    destination = array([0.0] * (pixels * 4))
    denominator = array([0.0] * pixels)
    alpha_max = array([0.0] * pixels)
    front = array([1.0, 0.75, 0.5, 0.25])
    empty = array([0.0])
    lib.olm_dblur_rowdriver_f32(
        0, height, rotated, destination, width, 0, ctypes.c_float(1.0),
        ctypes.c_float(0.0), ctypes.c_float(1.0), ctypes.c_float(0.0),
        ctypes.c_float(0.0), front, empty, empty, empty, denominator,
        alpha_max, comp_map, 4, 0, 0, 0)

    # Center prepass is source alpha; front scatter adds two in-row samples.
    center = 2 * width + 2
    # The rotated helper's strict interior validity leaves the center as the
    # prepass seed; the next valid columns receive front contributions.
    assert denominator[center] == f32(1.0 + 0.75)
    assert alpha_max[center] == 1.0
    target = center - 1
    assert denominator[target] == f32(1.0 + 0.75 + 0.5)
    assert alpha_max[target] == 1.0
    assert destination[target * 4 + 3] == 1.0

    normalized = array(list(destination))
    for pixel in range(pixels):
        if denominator[pixel] > 0.0:
            for channel in range(3):
                normalized[pixel * 4 + channel] = f32(
                    normalized[pixel * 4 + channel] / denominator[pixel])
    final = array([0.0] * (pixels * 4))
    lib.olm_dblur_rotate_rgba_f32(normalized, final, width, height,
                                  ctypes.c_float(-math.pi / 2))
    rgba = bytes(max(0, min(255, int(math.floor(float(final[i]) * 255.0 + 0.5))))
                 for i in range(pixels * 4))
    assert len(rgba) == pixels * 4
    assert any(rgba)
    print("PASS mode-0 typed adapter: source comp-map prepass scatter denominator alpha-max final-RGBA")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
