import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "refs/conformance/colorkeep_windows_mac_ae_boundary_20260806.json"
RUNNER = ROOT / "scripts/intake_colorkeep_windows_boundary_20260806.py"


class ColorKeepWindowsMacBoundaryTests(unittest.TestCase):
    def test_report_keeps_raw_mismatch_and_plugin_relation_separate(self):
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "host_color_transform_boundary_plugin_relation_exact")
        self.assertFalse(report["raw_cross_host_pixel_exact"])
        self.assertTrue(report["plugin_relation_exact_after_same_host_control"])
        self.assertEqual([row["depth"] for row in report["rows"]], [8, 16, 32])
        for row in report["rows"]:
            relation = row["same_host_control_relation"]
            self.assertFalse(row["pixel_exact"])
            self.assertTrue(relation["plugin_relation_exact"])
            self.assertEqual(relation["pixel_count"], 1920 * 1080)
            self.assertEqual(relation["retained_pixels"], 307500)
            self.assertEqual(relation["rejected_pixels"], 1766100)
            self.assertEqual(relation["cross_host_keep_mask_mismatches"], 0)
            self.assertEqual(relation["cross_host_no_effect_alpha_mismatches"], 0)
            self.assertEqual(relation["cross_host_effect_on_alpha_mismatches"], 0)
            self.assertEqual(relation["windows_effect_is_exact_control_or_zero_mismatches"], 0)
            self.assertEqual(relation["mac_effect_is_exact_control_or_zero_mismatches"], 0)
            self.assertEqual(relation["cross_effect_values_explained_by_retained_control_rgb_difference"], 307500 * 3)
            self.assertEqual(relation["cross_effect_values_unexplained_by_control_or_keep_mask"], 0)

    def test_runner_is_fail_closed_and_repeatable(self):
        source = RUNNER.read_text(encoding="utf-8")
        self.assertIn("verify_windows_ae_release_boundary_minimal_20260806.py", source)
        self.assertIn("vmmap", source)
        self.assertIn("app.beginSuppressDialogs()", source)
        self.assertIn("fresh-host gate failed", source)
        self.assertIn("host_color_transform_boundary_plugin_relation_exact", source)


if __name__ == "__main__":
    unittest.main()
