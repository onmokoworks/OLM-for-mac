#!/usr/bin/env python3
"""Tests for the binary-grounded OLMKiraKira outer compose oracle."""

from __future__ import annotations

import importlib.util
import math
import struct
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ORACLE = (
    ROOT
    / "tools"
    / "emulation"
    / "olmkirakira_outer_compose_oracle_20260728.py"
)
SPEC = importlib.util.spec_from_file_location("olmkirakira_outer_compose_oracle", ORACLE)
assert SPEC is not None and SPEC.loader is not None
oracle = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(oracle)


def bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def rgba_bits(value: tuple[float, float, float, float]) -> tuple[int, ...]:
    return tuple(bits(component) for component in value)


class OLMKiraKiraOuterComposeOracleTests(unittest.TestCase):
    def test_raw_alpha_zero_gate_ignores_nonzero_rgb_and_opacities(self) -> None:
        actual = oracle.compose_pixel(
            (0.9, 0.8, 0.7, 0.25),
            (0.6, 0.5, 0.4, -0.25),
            glow_opacity=1.0,
            source_opacity=1.0,
            merge_mode=2,
        )
        self.assertEqual(rgba_bits(actual), (0, 0, 0, 0))

    def test_mode1_normalizes_and_mode2_keeps_direct_weighted_sums(self) -> None:
        inputs = dict(
            glow=(0.8, 0.2, 0.6, 0.25),
            source=(0.2, 0.6, 0.4, 0.5),
            glow_opacity=0.5,
            source_opacity=0.5,
        )
        mode1 = oracle.compose_pixel(**inputs, merge_mode=1)
        mode2 = oracle.compose_pixel(**inputs, merge_mode=2)
        self.assertEqual(
            tuple(f"{word:08x}" for word in rgba_bits(mode1)),
            ("3eccccce", "3eeeeef0", "3eeeeef0", "3ec00000"),
        )
        self.assertEqual(
            tuple(f"{word:08x}" for word in rgba_bits(mode2)),
            ("3e19999a", "3e333334", "3e333334", "3ec00000"),
        )
        self.assertNotEqual(rgba_bits(mode1), rgba_bits(mode2))

    def test_independent_scaled_alpha_and_output_channel_clamps(self) -> None:
        actual = oracle.compose_pixel(
            (4.0, -2.0, 0.25, 0.75),
            (4.0, 2.0, 0.25, 0.75),
            glow_opacity=2.0,
            source_opacity=-2.0,
            merge_mode=2,
        )
        self.assertEqual(rgba_bits(actual), rgba_bits((1.0, 0.0, 0.25, 1.0)))

    def test_mode1_scaled_zero_denominator_replays_divss_without_exception(self) -> None:
        actual = oracle.compose_pixel(
            (0.5, 0.5, 0.5, 0.25),
            (0.5, 0.5, 0.5, 0.25),
            glow_opacity=0.0,
            source_opacity=0.0,
            merge_mode=1,
        )
        self.assertTrue(all(math.isnan(channel) for channel in actual[:3]))
        self.assertEqual(bits(actual[3]), 0)

    def test_binary_scalar_steps_preserve_discriminating_float32_bits(self) -> None:
        actual = oracle.compose_pixel(
            (0.1, 0.3, 0.7, 0.2),
            (0.9, 0.4, 0.05, 0.3),
            glow_opacity=0.7,
            source_opacity=0.6,
            merge_mode=1,
        )
        self.assertEqual(
            tuple(f"{word:08x}" for word in rgba_bits(actual)),
            ("3f0ccccd", "3eb66667", "3eab3333", "3ea3d70a"),
        )

    def test_binary_formula_differs_from_screen_and_source_alpha_passthrough(self) -> None:
        glow = (0.8, 0.4, 0.2, 0.5)
        source = (0.25, 0.5, 0.75, 0.25)
        actual = oracle.compose_pixel(
            glow, source, glow_opacity=0.5, source_opacity=0.5, merge_mode=2
        )
        screen_red = oracle.f32(
            1.0 - oracle.f32(oracle.f32(1.0 - glow[0]) * oracle.f32(1.0 - source[0]))
        )
        self.assertNotEqual(bits(actual[0]), bits(screen_red))
        self.assertNotEqual(bits(actual[3]), bits(source[3]))

    def test_typed_writer_stages_argb_and_truncates_without_rounding(self) -> None:
        rgba = (
            oracle.f32(128.9 / 255.0),
            oracle.f32(1.9 / 255.0),
            oracle.f32(254.9 / 255.0),
            oracle.f32(64.9 / 255.0),
        )
        self.assertEqual(oracle.stage_typed_writer(rgba, depth="PF8"), bytes((64, 128, 1, 254)))

        rgba16 = tuple(oracle.f32(value / 32768.0) for value in (1024.9, 2.9, 32767.9, 4096.9))
        self.assertEqual(
            struct.unpack("<4H", oracle.stage_typed_writer(rgba16, depth="PF16")),
            (4096, 1024, 2, 32767),
        )

    def test_pf32_writer_preserves_raw_float32_words_in_argb_order(self) -> None:
        rgba = tuple(
            struct.unpack("<f", struct.pack("<I", word))[0]
            for word in (0x3DCCCCCD, 0x3E4CCCCD, 0x3E99999A, 0x3ECCCCCD)
        )
        packed = oracle.stage_typed_writer(rgba, depth="PF32")
        self.assertEqual(
            struct.unpack("<4I", packed),
            (0x3ECCCCCD, 0x3DCCCCCD, 0x3E4CCCCD, 0x3E99999A),
        )

    def test_rejects_unmodeled_modes_depths_and_shapes(self) -> None:
        with self.assertRaisesRegex(ValueError, "1 or 2"):
            oracle.compose_pixel(
                (0.0,) * 4,
                (0.0,) * 4,
                glow_opacity=1.0,
                source_opacity=1.0,
                merge_mode=3,
            )
        with self.assertRaisesRegex(ValueError, "exactly R, G, B, A"):
            oracle.stage_typed_writer((0.0,) * 3, depth="PF8")
        with self.assertRaisesRegex(ValueError, "PF8, PF16, or PF32"):
            oracle.stage_typed_writer((0.0,) * 4, depth="host")


if __name__ == "__main__":
    unittest.main()
