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
        self.assertIn("width <= 4096", body)
        self.assertIn("height <= 4096", body)
        self.assertIn("kMaxGenericPixels", body)

    def test_mode3_generic_uses_full_visible_ui_length_without_widening_exact_tuple(self) -> None:
        generic = self.function_body("IsGenericBetaMode3HorizontalTuple")
        self.assertIn("info.horizontal_length < 1", generic)
        self.assertIn("info.horizontal_length > 300", generic)
        self.assertIn("owner_tuple.horizontal_length = 50", generic)
        exact = self.function_body("ClassicClosureSourceFamilyForTuple")
        self.assertIn("info.horizontal_length == 50", exact)
        closure32 = self.function_body("IsMode3Closure32x18Tuple")
        self.assertIn("info.horizontal_length == 50", closure32)

    def test_mode3_generic_has_checked_memory_and_work_budget(self) -> None:
        budget = self.function_body("IsGenericBetaMode3BudgetAdmitted")
        self.assertIn("KiraCheckedMultiply", budget)
        self.assertIn("KiraCheckedAdd", budget)
        self.assertIn("kMaxPluginOwnedBytes", budget)
        self.assertIn("kMaxMode3WorkUnits", budget)
        self.assertIn("kernel_taps", budget)
        self.assertIn("reflect_fold", budget)

    def test_classic_retains_exact_closure_and_adds_generic_lane(self) -> None:
        body = self.function_body("Render")
        self.assertIn("ClassicClosureSourceMatches", body)
        self.assertIn("IsGenericBetaTupleForGeometry", body)
        self.assertIn("IsGenericBetaClassicLayout", body)
        self.assertIn("if (!exact_closure && !generic_beta)", body)
        self.assertIn("!exact_closure", body)
        self.assertIn("GenericBetaInputIsFiniteSDR", body)

    def test_modes_three_and_four_use_core_geometry_admission(self) -> None:
        ray = self.function_body("GenericBetaDirectionalRayIsAdmitted")
        self.assertIn("mode3_gaussian_admitted", ray)
        self.assertIn("mode4_rotated_scalar_admitted", ray)
        tuple_body = self.function_body("IsGenericBetaMode34TupleForGeometry")
        self.assertIn("IsGenericBetaMode3BudgetAdmitted", tuple_body)
        self.assertIn("ClassicClosureSourceFamilyForTuple", tuple_body)
        self.assertEqual(tuple_body.count("GenericBetaDirectionalRayIsAdmitted"), 4)
        budget = self.function_body("IsGenericBetaMode3BudgetAdmitted")
        self.assertIn("IsGenericBetaMode3HorizontalTuple", budget)

    def test_generic_storage_authority_ignores_content_extent_and_requires_nonoverlap(self) -> None:
        body = self.function_body("SmartGenericBetaWorldPairIsFullFrame")
        self.assertNotIn("extent_hint", body)
        self.assertIn("input->origin_x == 0", body)
        self.assertIn("WorldStorageRangesDoNotOverlap", body)
        classic = self.function_body("IsGenericBetaClassicLayout")
        self.assertNotIn("extent_hint", classic)
        self.assertIn("input->origin_x == 0", classic)
        self.assertIn("WorldStorageRangesDoNotOverlap", classic)
        smart = self.function_body("SmartRender")
        self.assertIn("SmartGenericBetaWorldPairIsFullFrame", smart)
        self.assertIn("exact_world_layout &&", smart)
        self.assertIn("GenericBetaInputIsFiniteSDR", smart)
        self.assertIn("IsGenericBetaTupleForGeometry", smart)

    def test_generic_request_is_normalized_to_authoritative_render_dimensions(self) -> None:
        admission = self.function_body("SmartOutputRequestIsAdmitted")
        self.assertIn("rect.left == 0 && rect.top == 0", admission)
        prerender = self.function_body("SmartPreRender")
        self.assertIn("request_contains_generic_full_frame", prerender)
        self.assertIn("PF_LRect{0, 0, generic_render_width, generic_render_height}", prerender)
        self.assertIn("const A_long expected_width = full_rect.right", prerender)
        self.assertIn("!generic_beta_request && !exact_checkout_rects_are_full", prerender)
        self.assertIn("result_rect/max_result_rect describe content", prerender)

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
