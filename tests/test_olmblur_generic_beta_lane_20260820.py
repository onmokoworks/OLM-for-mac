import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "mac/OLMBlur/OLMBlur.cpp"


class GenericBetaLaneTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text()

    def test_lane_precedes_exact_fixture_admission(self):
        generic = self.source.index("GenericBetaTuple(raw")
        exact = self.source.index("const bool public24", generic)
        self.assertLess(generic, exact)

    def test_arbitrary_source_and_independent_strides(self):
        body = re.search(
            r"static bool\s+GenericBetaWorld\(.*?\n\}", self.source, re.S
        ).group(0)
        self.assertNotIn("ExactPublicSource", body)
        self.assertIn("active <= (size_t)world->rowbytes", body)
        lane = self.source[self.source.index("// Generic beta lane."):]
        self.assertIn("GenericBetaWorld(input_world", lane)
        self.assertIn("GenericBetaWorld(output_world", lane)
        self.assertIn("BlurRender(in_data,input_world,output_world,bpc,&bp)", lane)

    def test_geometry_memory_and_work_limits_are_explicit(self):
        body = re.search(
            r"static bool\s+GenericBetaTuple\(.*?\n\}", self.source, re.S
        ).group(0)
        for contract in (
            "width > 4096",
            "height > 2160",
            "640u * 1024u * 1024u",
            "raw.amount > 1000.0",
            "raw.repeat > 10",
            "max_work=3600u*1000u*1000u",
        ):
            self.assertIn(contract, body)

    def test_exact_small_fixtures_remain_owned_by_exact_lane(self):
        self.assertIn("if (width <= 24 && height <= 24) return false;", self.source)


if __name__ == "__main__":
    unittest.main()
