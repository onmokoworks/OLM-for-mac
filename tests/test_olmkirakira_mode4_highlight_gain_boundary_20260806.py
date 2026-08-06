#!/usr/bin/env python3
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Mode4HighlightGainBoundaryTests(unittest.TestCase):
    def test_production_uses_direct_brightness_only_for_mode4_highlight(self) -> None:
        source = (ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp").read_text(encoding="utf-8")
        self.assertIn("const double highlight_scale = info.blur_mode == 4", source)
        self.assertIn("? info.brightness_gain", source)
        self.assertIn("AddColoredUnion(glow, highlight, info.highlight_color, highlight_scale);", source)
        self.assertIn("AddColoredUnion(glow, vertical, info.vertical_color, scale);", source)

    def test_observed_ratio_identifies_removed_scaffold_factor(self) -> None:
        evidence = json.loads((ROOT / "refs/conformance/olmkirakira_mode4_highlight_gain_pf32_20260806.json").read_text(encoding="utf-8"))
        self.assertEqual(evidence["status"], "mode4_highlight_gain_corrected_and_ae_verified")
        self.assertAlmostEqual(evidence["recovered_glow_alpha"]["windows_over_mac_median"], 1.0 / 0.62, places=5)
        self.assertLess(evidence["recovered_glow_alpha"]["channel_solution_max_median_delta"], 1e-5)
        self.assertEqual(evidence["production_change"]["scope"], "Mode4 fifth/highlight AddColoredUnion scale only")
        validation = evidence["production_validation"]
        self.assertEqual(validation["recovered_glow_alpha_windows_over_mac_median"], {"R": 1.0, "G": 1.0, "B": 1.0})
        self.assertLessEqual(validation["control_inverse_transfer"]["max_ulp"], 3)
        self.assertLessEqual(validation["effect_inverse_transfer"]["max_ulp"], 14)


if __name__ == "__main__": unittest.main()
