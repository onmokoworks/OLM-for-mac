#!/usr/bin/env python3
"""Fail-closed regression for the exact DistanceGradation dynamic UI contract."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "mac/OLMDistanceGradation/OLMDistanceGradation.cpp").read_text(encoding="utf-8")
REPORT = json.loads((ROOT / "refs/conformance/olmdistancegradation_update_params_ui_actual_aex_20260810.json").read_text())


class DistanceGradationUpdateParamsUITest(unittest.TestCase):
    def test_actual_aex_full_public_matrix_is_exact(self) -> None:
        self.assertEqual(REPORT["status"], "exact")
        self.assertEqual(REPORT["case_count"], 144)
        self.assertEqual(REPORT["update_order"], [10, 4, 3, 7, 8, 12])
        self.assertEqual(REPORT["disabled_bit"], 0x20)
        self.assertEqual(len(REPORT["cases"]), 144)
        self.assertTrue(all(len(row["updates"]) == 6 for row in REPORT["cases"]))

    def test_production_dispatch_and_all_actual_predicates_remain_connected(self) -> None:
        self.assertIn("case PF_Cmd_UPDATE_PARAMS_UI:", SOURCE)
        self.assertIn("err = UpdateParamsUI(in_data);", SOURCE)
        for predicate in (
            "interp_mode != INTERP_POWER",
            "in_out == IN_OUT_INSIDE",
            "in_out == IN_OUT_OUTSIDE",
            "render_mode != RENDER_MODE_RGB",
            "!use_bg",
            "blur_mode == BLUR_MODE_NONE",
        ):
            self.assertIn(predicate, SOURCE)
        self.assertIn("copy.ui_flags = disabled ? PF_PUI_DISABLED : 0;", SOURCE)


if __name__ == "__main__":
    unittest.main()
