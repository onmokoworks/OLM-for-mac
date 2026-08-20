from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts/olm_property_cases.py"
SPEC = importlib.util.spec_from_file_location("olm_property_cases", MODULE_PATH)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MOD
SPEC.loader.exec_module(MOD)


class PropertyCasesTest(unittest.TestCase):
    def test_geometry_is_reproducible_unique_and_broad(self):
        left = MOD.geometry_cases(12345, 100)
        self.assertEqual(left, MOD.geometry_cases(12345, 100))
        self.assertEqual(len(left), 100)
        self.assertEqual(len(set(left)), 100)
        self.assertIn((1, 1), left)
        self.assertIn((1920, 1080), left)
        self.assertIn((3840, 2160), left)
        self.assertTrue(any(w % 2 and h % 2 for w, h in left))

    def test_stride_has_tight_padding_and_alignment(self):
        strides = MOD.stride_cases(17, 16, 9)
        active = 17 * 8
        self.assertIn(active, strides)
        self.assertIn(active + 1, strides)
        self.assertTrue(any(value % 64 == 0 for value in strides))
        self.assertTrue(all(value >= active for value in strides))

    def test_toon_campaign_has_100_serializable_cases(self):
        cases = MOD.generate_cases("OLM Toon Dilate", MOD.TOON_DILATE_PARAMETERS, seed=7, count=100)
        campaign = MOD.manifest("OLM Toon Dilate", 7, cases)
        self.assertEqual(campaign["schema"], "olm.property-campaign/1")
        self.assertEqual(campaign["case_count"], 100)
        self.assertEqual({row["depth"] for row in campaign["cases"]}, {8, 16, 32})
        self.assertEqual({row["recipe"] for row in campaign["cases"]}, set(MOD.RECIPES))
        values = {row["parameters"]["ADBE OLMToonDilate-0001"] for row in campaign["cases"]}
        self.assertTrue({0.0, 13.0, 100.0}.issubset(values))
        json.dumps(campaign)

    def test_pixels_are_reproducible_and_bounded(self):
        for recipe in MOD.RECIPES:
            first = MOD.pixel_value(recipe, 2, 3, 7, 9, 88)
            self.assertEqual(first, MOD.pixel_value(recipe, 2, 3, 7, 9, 88))
            self.assertEqual(len(first), 4)
            self.assertTrue(all(0.0 <= value <= 1.0 for value in first))

    def test_write_cases_and_report_schema(self):
        cases = MOD.generate_cases("OLM Toon Dilate", MOD.TOON_DILATE_PARAMETERS, seed=91, count=5)
        campaign = MOD.manifest("OLM Toon Dilate", 91, cases)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = MOD.write_campaign(root, campaign)
            self.assertTrue(path.is_file())
            self.assertEqual(len(list((root / "cases").glob("*.json"))), 5)
            self.assertEqual(json.loads(path.read_text())["seed"], 91)
        results = [{"case_id": case.case_id, "status": "pass"} for case in cases]
        report = MOD.report(campaign, results)
        self.assertEqual(report["schema"], "olm.property-report/1")
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["failure_count"], 0)
        with tempfile.TemporaryDirectory() as temp:
            report_path = MOD.write_report(Path(temp), report)
            self.assertEqual(json.loads(report_path.read_text())["status"], "pass")
        failed = MOD.report(campaign, results[:-1])
        self.assertEqual(failed["status"], "fail")
        self.assertEqual(failed["missing_case_ids"], [cases[-1].case_id])


if __name__ == "__main__":
    unittest.main()
