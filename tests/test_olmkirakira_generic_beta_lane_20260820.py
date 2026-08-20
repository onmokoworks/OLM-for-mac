import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp"
HARNESS = ROOT / "tests/olmkirakira_generic_beta_sanitizer_harness.cpp"


class KiraKiraGenericBetaLaneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = SOURCE.read_text(encoding="utf-8")

    def function_body(self, name: str) -> str:
        match = re.search(rf"static [^\n]+ {name}\([^{{]+\)\n\{{", self.source)
        self.assertIsNotNone(match, name)
        start = match.end()
        depth = 1
        for index in range(start, len(self.source)):
            if self.source[index] == "{":
                depth += 1
            elif self.source[index] == "}":
                depth -= 1
                if depth == 0:
                    return self.source[start:index]
        self.fail(f"unterminated function {name}")

    def test_beta_tuple_is_bounded_to_modes_one_and_two(self) -> None:
        body = self.function_body("IsGenericBetaMode12Tuple")
        self.assertIn("info.blur_mode == 1 || info.blur_mode == 2", body)
        self.assertIn("ClassicClosureSourceFamilyForTuple(info)", body)

    def test_beta_geometry_excludes_tiny_fixture_leaves(self) -> None:
        body = self.function_body("IsGenericBetaFullFrameDimensions")
        self.assertIn("width >= 9", body)
        self.assertIn("height >= 7", body)

    def test_classic_retains_exact_closure_and_adds_generic_lane(self) -> None:
        body = self.function_body("Render")
        self.assertIn("ClassicClosureSourceMatches", body)
        self.assertIn("IsGenericBetaTupleForGeometry", body)
        self.assertIn("IsGenericBetaClassicLayout", body)
        self.assertIn("if (!exact_closure && !generic_beta)", body)

    def test_modes_three_and_four_use_core_geometry_admission(self) -> None:
        ray = self.function_body("GenericBetaDirectionalRayIsAdmitted")
        self.assertIn("mode3_gaussian_admitted", ray)
        self.assertIn("mode4_rotated_scalar_admitted", ray)
        tuple_body = self.function_body("IsGenericBetaMode34TupleForGeometry")
        self.assertIn("ClassicClosureSourceFamilyForTuple", tuple_body)
        self.assertEqual(tuple_body.count("GenericBetaDirectionalRayIsAdmitted"), 4)

    def test_smart_generic_lane_requires_full_frame_and_nonoverlap(self) -> None:
        body = self.function_body("SmartGenericBetaWorldPairIsFullFrame")
        self.assertIn("extent_hint.left == 0", body)
        self.assertIn("extent_hint.right == width", body)
        self.assertIn("WorldStorageRangesDoNotOverlap", body)
        smart = self.function_body("SmartRender")
        self.assertIn("SmartGenericBetaWorldPairIsFullFrame", smart)
        self.assertIn("IsGenericBetaTupleForGeometry", smart)

    def test_generic_request_is_normalized_to_authoritative_render_dimensions(self) -> None:
        admission = self.function_body("SmartOutputRequestIsAdmitted")
        self.assertIn("rect.left == 0 && rect.top == 0", admission)
        prerender = self.function_body("SmartPreRender")
        self.assertIn("request_contains_generic_full_frame", prerender)
        self.assertIn("PF_LRect{0, 0, generic_render_width, generic_render_height}", prerender)
        self.assertIn("const A_long expected_width = full_rect.right", prerender)

    def test_partial_roi_contract_is_explicitly_fail_closed(self) -> None:
        prerender = self.function_body("SmartPreRender")
        self.assertIn("Keep generic ROI/tile requests closed", prerender)
        self.assertIn("passes * radius", prerender)
        self.assertIn("bidirectional IIR", prerender)
        self.assertIn("request_contains_generic_full_frame", prerender)
        harness = HARNESS.read_text(encoding="utf-8")
        self.assertIn('"--partial-guard"', harness)
        self.assertIn('"--downsample-guard"', harness)
        self.assertIn('"--overscan-matrix"', harness)


if __name__ == "__main__":
    unittest.main()
