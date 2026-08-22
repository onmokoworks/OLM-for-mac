import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "mac/OLMBlur/OLMBlur.cpp"
PROBE = ROOT / "tools/emulation/probe_olmblur_generic_beta_sanitized_20260820.cpp"


class OLMBlurGenericClassicBetaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text()
        start = cls.source.index("Render(PF_InData")
        end = cls.source.index("SmartPreRender(PF_InData", start)
        cls.render = cls.source[start:end]

    def test_classic_preserves_windows_copy_only_tuple_and_pf32_boundary(self):
        self.assertIn("blur_amount != 5.0", self.render)
        self.assertIn("blur_smoothness != 100 * 65536", self.render)
        self.assertIn("repeat != 2", self.render)
        self.assertIn("case PF_PixelFormat_ARGB128:", self.render)
        self.assertNotIn("BlurRender(in_data, input, output", self.render)

    def test_general_geometry_independent_strides_and_transactional_copy(self):
        helper = re.search(
            r"ClassicCopyGeometry\(.*?\n\}", self.source, re.S
        ).group(0)
        self.assertIn("input->width > 4096", helper)
        self.assertIn("input->height > 2160", helper)
        self.assertIn("width * height > 3840u * 2160u", helper)
        self.assertNotIn("rowbytes", helper)
        self.assertNotIn("input->rowbytes != output->rowbytes", self.render)
        self.assertIn("olm::world_safety::TightStaging staging", self.render)
        self.assertIn("staging.prepare", self.render)
        self.assertIn("staging.commit()", self.render)

    def test_sanitizer_probe_covers_classic_pf8_pf16_sd_through_uhd(self):
        probe = PROBE.read_text()
        for token in (
            "run_classic_copy<PF_Pixel8>(8,65,33)",
            "run_classic_copy<PF_Pixel16>(16,720,480)",
            "run_classic_copy<PF_Pixel8>(8,1920,1080)",
            "run_classic_copy<PF_Pixel16>(16,3840,2160)",
            "overlap!=PF_Err_NONE&&input==input_before",
        ):
            self.assertIn(token, probe)


if __name__ == "__main__":
    unittest.main()
