from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/run_colorkeep_pf8_mac_validation_20260805.py"
SPEC = importlib.util.spec_from_file_location("colorkeep_pf8_mac_runner", RUNNER)
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


class ColorKeepPF8MacRunnerContractTests(unittest.TestCase):
    def test_runtime_and_distribution_versions_are_separate(self) -> None:
        self.assertEqual(runner.EXPECTED_AE_VERSION, "26.3.0")
        self.assertEqual(runner.EXPECTED_AE_APP_VERSION, "26.3x87")
        source = runner.jsx_source({"runtime_ae_version": "ignored"})
        self.assertIn('spec.runtime_ae_version', source)
        self.assertIn('"runtime_ae_version":"26.3x87"', source)

    def test_ae_minimum_comp_preserves_the_source_footprint(self) -> None:
        source = runner.jsx_source({})
        self.assertIn('addComp(spec.case.id,4,4,1,1,1)', source)
        self.assertIn('position.setValue([2,1.5])', source)
        self.assertIn('"source_footprint":[4,3]', source)
        self.assertIn('"host_comp":[4,4]', source)

    def test_png_boundary_accepts_only_ae_hidden_rgb_normalization(self) -> None:
        expected = Image.new("RGBA", (4, 3), (0, 0, 0, 0))
        expected.putpixel((0, 0), (12, 34, 56, 255))
        expected.putpixel((1, 0), (90, 80, 70, 0))
        observed = Image.new("RGBA", (4, 4), (0, 0, 0, 0))
        observed.putpixel((0, 0), (12, 34, 56, 255))
        runner.verify_host_export_pixels(observed, expected)
        observed.putpixel((0, 0), (13, 34, 56, 255))
        with self.assertRaisesRegex(RuntimeError, "opaque RGBA"):
            runner.verify_host_export_pixels(observed, expected)

    def test_png_boundary_rejects_alpha_and_padding_changes(self) -> None:
        expected = Image.new("RGBA", (4, 3), (0, 0, 0, 0))
        observed = Image.new("RGBA", (4, 4), (0, 0, 0, 0))
        observed.putpixel((0, 0), (0, 0, 0, 1))
        with self.assertRaisesRegex(RuntimeError, "alpha differs"):
            runner.verify_host_export_pixels(observed, expected)
        observed.putpixel((0, 0), (0, 0, 0, 0))
        observed.putpixel((0, 3), (1, 0, 0, 0))
        with self.assertRaisesRegex(RuntimeError, "padding row"):
            runner.verify_host_export_pixels(observed, expected)


if __name__ == "__main__":
    unittest.main()
