#!/usr/bin/env python3
"""Focused regression for the production DirectionalBlur dynamic UI path."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp"
HARNESS = ROOT / "tools/emulation/test_olmdirectionalblur_update_params_ui_actual_aex_20260810.py"
REPORT = ROOT / "refs/conformance/olmdirectionalblur_update_params_ui_actual_aex_20260810.json"


class DirectionalBlurUpdateParamsUITest(unittest.TestCase):
    def test_actual_aex_contract_and_production_route(self) -> None:
        run = subprocess.run(
            [sys.executable, str(HARNESS)], cwd=ROOT, capture_output=True, text=True
        )
        self.assertEqual(run.returncode, 0, run.stderr)
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "exact_contract_fixed")
        for value in (0, 1, 2, 4):
            self.assertEqual(
                report["cases"][str(value)]["hidden_by_param_index"],
                {"17": True, "18": False, "19": False, "20": False},
            )
        self.assertEqual(
            report["cases"]["3"]["hidden_by_param_index"],
            {"17": False, "18": True, "19": True, "20": True},
        )

        source = SOURCE.read_text(encoding="utf-8")
        self.assertRegex(
            source,
            r"case PF_Cmd_UPDATE_PARAMS_UI:\s*err = UpdateParamsUI\(in_data\);",
        )
        self.assertIn("noise_type_param.u.pd.value == 3", source)
        ordered = [
            source.index("{OLMDIRECTIONALBLUR_NOISE_LAYER,"),
            source.index("{OLMDIRECTIONALBLUR_SEED, layer_mode}"),
            source.index("{OLMDIRECTIONALBLUR_NOISE_OFFSET, layer_mode}"),
            source.index("{OLMDIRECTIONALBLUR_THICKNESS, layer_mode}"),
        ]
        self.assertEqual(ordered, sorted(ordered))
        self.assertIn(
            "stream, AEGP_DynStreamFlag_HIDDEN, FALSE, control.hidden", source
        )
        self.assertIn("streams->AEGP_DisposeStream(stream)", source)
        self.assertIn("effects->AEGP_DisposeEffect(effect)", source)


if __name__ == "__main__":
    unittest.main()
