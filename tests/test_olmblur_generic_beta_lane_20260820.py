import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "mac/OLMBlur/OLMBlur.cpp"


class GenericBetaLaneTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text()


    def test_arbitrary_source_and_independent_strides(self):
        body = re.search(
            r"static bool\s+GenericBetaWorld\(.*?\n\}", self.source, re.S
        ).group(0)
        self.assertNotIn("ExactPublicSource", body)
        self.assertIn("active <= (size_t)world->rowbytes", body)
        lane = self.source[self.source.index("// Generic beta lane."):]
        self.assertIn("GenericBetaWorld(input_world", lane)
        self.assertIn("GenericBetaWorld(output_world", lane)
        self.assertIn("olm::world_safety::TightStaging staging", lane)
        self.assertIn("BlurRender(in_data,&staged_input,&staged_output,bpc,&bp)", lane)
        self.assertIn("staging.commit()", lane)
        self.assertLess(lane.index("checkin_layer_pixels"), lane.index("staging.commit()"))

    def test_geometry_representation_and_control_limits_are_explicit(self):
        body = re.search(
            r"static const char \*\s+GenericBetaTupleRefusal\(.*?\n\}", self.source, re.S
        ).group(0)
        # F41b merge 7a0cd797d52c9564c1f89191488f095c73f11b02: AEX has no work/size cap.
        for contract in (
            "width <= 0 || height <= 0",
            "usize_width > ((size_t)-1) / usize_height",
            "pixels > std::vector<float>().max_size() / 4u",
            "raw.amount > 1000.0",
            "raw.repeat > 10",

        ):
            self.assertIn(contract, body)
        for obsolete in ("width > 4096", "height > 2160", "max_work", "640u * 1024u * 1024u"):
            self.assertNotIn(obsolete, body)



if __name__ == "__main__":
    unittest.main()
