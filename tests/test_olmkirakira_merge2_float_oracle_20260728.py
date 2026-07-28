#!/usr/bin/env python3
"""Tests for the isolated FUN_18114ffd0 pure-float aggregation oracle."""

from __future__ import annotations

import importlib.util
import struct
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ORACLE = (
    ROOT
    / "tools"
    / "emulation"
    / "olmkirakira_merge2_float_oracle_20260728.py"
)
SPEC = importlib.util.spec_from_file_location("olmkirakira_merge2_float_oracle", ORACLE)
assert SPEC is not None and SPEC.loader is not None
oracle = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(oracle)


def bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


BLACK = (0.0, 0.0, 0.0)


class OLMKiraKiraMerge2FloatOracleTests(unittest.TestCase):
    def test_zero_rgba_when_all_five_layers_skip(self) -> None:
        boundary = oracle.f32(0.001)
        actual = oracle.aggregate_pixel(
            [boundary] * 5,
            [(1.0, 1.0, 1.0)] * 5,
            skip_threshold=boundary,
        )
        self.assertEqual(tuple(map(bits, actual)), (0, 0, 0, 0))

    def test_threshold_is_explicit_and_strict(self) -> None:
        colors = [(0.25, 0.5, 0.75), BLACK, BLACK, BLACK, BLACK]
        at_boundary = oracle.aggregate_pixel(
            [0.25, 0.0, 0.0, 0.0, 0.0],
            colors,
            skip_threshold=0.25,
        )
        above_boundary = oracle.aggregate_pixel(
            [oracle.f32(0.25000003), 0.0, 0.0, 0.0, 0.0],
            colors,
            skip_threshold=0.25,
        )
        self.assertEqual(at_boundary, (0.0, 0.0, 0.0, 0.0))
        self.assertEqual(
            tuple(map(bits, above_boundary)),
            tuple(map(bits, (0.25, 0.5, 0.75, oracle.f32(0.25000003)))),
        )
        with self.assertRaises(TypeError):
            oracle.aggregate_pixel([0.0] * 5, [BLACK] * 5)

    def test_rgb_is_direct_and_alpha_is_raw_ray(self) -> None:
        actual = oracle.aggregate_pixel(
            [0.125, 0.0, 0.0, 0.0, 0.0],
            [(0.8, 0.4, 0.2), BLACK, BLACK, BLACK, BLACK],
            skip_threshold=0.0,
        )
        self.assertEqual(
            tuple(map(bits, actual)),
            tuple(map(bits, (0.8, 0.4, 0.2, 0.125))),
        )

    def test_all_five_layers_are_visited_in_order_with_float32_adds(self) -> None:
        actual = oracle.aggregate_pixel(
            [0.1] * 5,
            [
                (16_777_216.0, 0.1, 0.0),
                (-16_777_216.0, 0.2, 0.0),
                (1.0, 0.3, 0.0),
                (0.0, 0.4, 0.0),
                (0.0, 0.5, 0.0),
            ],
            skip_threshold=0.0,
        )
        self.assertEqual(bits(actual[0]), bits(1.0))
        self.assertEqual(bits(actual[1]), bits(1.0))
        self.assertEqual(bits(actual[2]), bits(0.0))
        self.assertEqual(bits(actual[3]), bits(oracle.f32(0.5)))

    def test_independent_clamps_run_after_aggregation(self) -> None:
        actual = oracle.aggregate_pixel(
            [0.4, 0.4, 0.4, 0.0, 0.0],
            [
                (0.8, -0.6, 0.2),
                (0.8, 0.1, 0.3),
                (0.8, 0.1, 0.4),
                BLACK,
                BLACK,
            ],
            skip_threshold=0.0,
        )
        self.assertEqual(
            tuple(map(bits, actual)),
            tuple(map(bits, (1.0, 0.0, 0.9, 1.0))),
        )

    def test_contract_rejects_non_five_layer_shapes(self) -> None:
        with self.assertRaisesRegex(ValueError, "exactly 5"):
            oracle.aggregate_pixel([0.0] * 4, [BLACK] * 5, skip_threshold=0.0)
        with self.assertRaisesRegex(ValueError, "exactly 5"):
            oracle.aggregate_pixel([0.0] * 5, [BLACK] * 4, skip_threshold=0.0)
        with self.assertRaisesRegex(ValueError, "exactly R, G, B"):
            oracle.aggregate_pixel(
                [0.0] * 5,
                [(0.0, 0.0)] + [BLACK] * 4,
                skip_threshold=0.0,
            )


if __name__ == "__main__":
    unittest.main()
