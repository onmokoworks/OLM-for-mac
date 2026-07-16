import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text()


class TestDirectional(unittest.TestCase):
    def test_mac_version_flags_and_pipl_match_decomp(self):
        header = read("mac/OLMDirectionalBlur/OLMDirectionalBlur.h")
        source = read("mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp")
        pipl = read("mac/OLMDirectionalBlur/OLMDirectionalBlurPiPL.r")
        decomp = read("decomp/OLMDirectionalBlur.aex.c.txt")

        self.assertIn("// program: OLMDirectionalBlur.aex", decomp)
        self.assertIn("fVar19 = fVar19 / fVar20", decomp)
        self.assertIn("LAB_18000122f", decomp)
        self.assertRegex(
            header,
            r"#define MAJOR_VERSION 1\s+#define MINOR_VERSION 1\s+"
            r"#define BUG_VERSION\s+1",
        )
        self.assertIn("out_data->out_flags  = 0x06000040;", source)
        self.assertIn("out_data->out_flags2 = 0x08001408;", source)
        self.assertIn("AE_Effect_Version { 559104", pipl)
        self.assertIn("AE_Effect_Global_OutFlags { 0x06000040 }", pipl)
        self.assertIn("AE_Effect_Global_OutFlags_2 { 0x08001408 }", pipl)

    def test_parameter_labels_match_mac_strings(self):
        source = read("mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp")
        strings = read("mac/OLMDirectionalBlur/OLMDirectionalBlur_Strings.cpp")

        for label in ("Blur Strength", "Alpha Fade", "Sharp Tail"):
            self.assertEqual(strings.count(f'"{label}"'), 2)
        self.assertNotIn("Front Blur Strength", strings)
        self.assertNotIn("Back Blur Strength", strings)
        self.assertIn("OLMDIRECTIONALBLUR_FRONT_STRENGTH", source)
        self.assertIn("OLMDIRECTIONALBLUR_BACK_STRENGTH", source)


class TestDistanceGradation(unittest.TestCase):
    def test_decomp_and_mac_sources_expose_distance_gradation(self):
        decomp = read("decomp/DistanceGradation.aex.c.txt")
        source = read("mac/OLMDistanceGradation/OLMDistanceGradation.cpp")
        pipl = read("mac/OLMDistanceGradation/OLMDistanceGradationPiPL.r")
        header = read("mac/OLMDistanceGradation/OLMDistanceGradation.h")

        self.assertIn("// program: DistanceGradation.aex", decomp)
        self.assertIn('"cv::distanceTransform"', decomp)
        self.assertIn('"cv::threshold"', decomp)
        self.assertIn("GlobalSetup", source)
        self.assertRegex(
            source,
            r"out_data->my_version\s*=\s*PF_VERSION\(MAJOR_VERSION,\s*"
            r"MINOR_VERSION,\s*BUG_VERSION,\s*STAGE_VERSION,\s*BUILD_VERSION\)",
        )
        self.assertRegex(
            header,
            r"#define MAJOR_VERSION 0\s+#define MINOR_VERSION 8\s+"
            r"#define BUG_VERSION\s+2\s+#define STAGE_VERSION PF_Stage_ALPHA\s+"
            r"#define BUILD_VERSION 0",
        )

        source_flags = re.search(
            r"out_data->out_flags\s*=\s*(0x[0-9a-f]+);\s*"
            r"out_data->out_flags2\s*=\s*(0x[0-9a-f]+);",
            source,
        )
        pipl_flags = re.search(
            r"AE_Effect_Global_OutFlags \{ (0x[0-9a-f]+) \}.*"
            r"AE_Effect_Global_OutFlags_2 \{ (0x[0-9a-f]+) \}",
            pipl,
            re.DOTALL,
        )
        self.assertIsNotNone(source_flags)
        self.assertIsNotNone(pipl_flags)
        self.assertEqual(source_flags.groups(), pipl_flags.groups())
        self.assertIn("AE_Effect_Version { 266752", pipl)
        self.assertIn("PF_VERSION(0, 8, 2, PF_Stage_ALPHA, 0)", pipl)


class TestRadial(unittest.TestCase):
    def test_override_choice_is_grounded_in_decomp_and_mac_contract(self):
        decomp = read("decomp/OLMRadialBlur.aex.c.txt")
        source = read("mac/OLMRadialBlur/OLMRadialBlur.cpp")
        pipl = read("mac/OLMRadialBlur/OLMRadialBlurPiPL.r")
        strings = read("mac/OLMRadialBlur/OLMRadialBlur_Strings.cpp")

        self.assertIn("// program: OLMRadialBlur.aex", decomp)
        self.assertIn("PTR_s_Add___Max___Override", decomp)
        for choice in ("Add", "Max", "Override"):
            self.assertIn(choice, decomp)
        self.assertIn('"Add|Max|Override"', strings)
        self.assertNotIn("Add|Max|Replace", decomp)
        self.assertNotIn("Add|Max|Replace", strings)
        self.assertIn("static float RadialF32Add", source)
        self.assertIn("out_data->out_flags  = 0x02000040;", source)
        self.assertIn("out_data->out_flags2 = 0x08001400;", source)
        self.assertIn("AE_Effect_Version { 622592", pipl)
        self.assertIn("AE_Effect_Global_OutFlags { 0x02000040 }", pipl)
        self.assertIn("AE_Effect_Global_OutFlags_2 { 0x08001400 }", pipl)


if __name__ == "__main__":
    unittest.main()
