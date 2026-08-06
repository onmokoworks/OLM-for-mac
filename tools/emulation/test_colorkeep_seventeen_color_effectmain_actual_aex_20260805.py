#!/usr/bin/env python3
"""Seventeen-color four-unrolled-group proof through dynamic EffectMain."""

from __future__ import annotations

from pathlib import Path

import test_colorkeep_thirteen_color_effectmain_actual_aex_20260805 as proof

ROOT = Path(__file__).resolve().parents[2]
proof.REPORT = ROOT / "refs/conformance/colorkeep_seventeen_color_effectmain_actual_aex_20260805.json"
proof.COLORS = (
    (1.0, 0.0, 0.25, 0.5), (0.75, 0.25, 0.5, 0.75),
    (0.5, 0.5, 0.75, 1.0), (0.25, 0.75, 1.0, 0.0),
    (1.0, 1.0, 0.0, 0.25), (0.875, 0.125, 0.375, 0.625),
    (0.625, 0.375, 0.625, 0.875), (0.375, 0.625, 0.875, 0.125),
    (0.125, 0.875, 0.125, 0.375), (0.9375, 0.0625, 0.3125, 0.5625),
    (0.6875, 0.3125, 0.5625, 0.8125), (0.4375, 0.5625, 0.8125, 0.0625),
    (0.1875, 0.8125, 0.0625, 0.3125), (0.96875, 0.03125, 0.28125, 0.53125),
    (0.71875, 0.28125, 0.53125, 0.78125), (0.46875, 0.53125, 0.78125, 0.03125),
    (0.21875, 0.78125, 0.03125, 0.28125),
)
proof.SELECTED = (0, 3, 4, 7, 8, 11, 12, 15, 16)


if __name__ == "__main__":
    raise SystemExit(proof.main())
