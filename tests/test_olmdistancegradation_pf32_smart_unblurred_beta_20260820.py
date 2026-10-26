import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "mac/OLMDistanceGradation/OLMDistanceGradation.cpp"


class DistanceGradationPF32SmartUnblurredBeta(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text()
        for include in ("DistanceFilters.inc", "BilateralFilters.inc", "DistanceField.inc", "PixelCompose.inc", "Admission.inc"):
            cls.source = cls.source.replace('#include "' + include + '"', SOURCE.with_name(include).read_text())

    def test_beta_lane_is_limited_to_unblurred_constant_linear_or_sphere(self):
        body = self.source.split(
            "static bool is_admitted_pf32_smart_unblurred_beta", 1
        )[1].split("\n}", 1)[0]
        self.assertIn("p.blur_mode == BLUR_MODE_NONE", body)
        self.assertIn("p.interp_mode == INTERP_CONSTANT", body)
        self.assertIn("p.interp_mode == INTERP_LINEAR", body)
        self.assertIn("p.interp_mode == INTERP_SPHERE", body)
        self.assertNotIn("INTERP_POWER", body)
        self.assertNotIn("BLUR_MODE_BILATERAL", body)

    def test_exact_power_and_mode5_lane_remains_independent(self):
        self.assertIn("is_admitted_pf32_smart_exported_matrix", self.source)
        self.assertIn("is_admitted_pf32_power_source", self.source)
        self.assertIn("p.pf32_smart_matrix_admitted && p.power == 2.25f", self.source)
        self.assertIn("p.pf32_smart_matrix_admitted || p.pf32_smart_oracle_profile_admitted", self.source)

    def test_pf32_admission_is_union_of_exact_and_beta_lanes(self):
        self.assertIn(
            "if (!p.pf32_smart_matrix_admitted && !unblurred_beta && !blurred_beta &&", self.source
        )

    def test_blurred_beta_retains_controls_without_work_caps(self):
        body = self.source.split(
            "static bool is_admitted_pf32_smart_blurred_beta", 1
        )[1].split("static bool pf32_smart_worlds_are_bounded_sdr", 1)[0]
        self.assertIn("p.interp_mode != INTERP_CONSTANT", body)
        self.assertIn("p.interp_mode != INTERP_LINEAR", body)
        self.assertIn("p.interp_mode != INTERP_SPHERE", body)
        self.assertIn("p.blur_mode > BLUR_MODE_MEDIAN", body)
        self.assertIn("p.blur_size < 1 || p.blur_size > (p.blur_mode == BLUR_MODE_MEDIAN ? 500 : 4096)", body)
        # F41b merge 7a0cd797d52c9564c1f89191488f095c73f11b02.
        self.assertNotIn("kSeparableWorkBudget", body)
        self.assertNotIn("kMedianWorkBudget", body)
        self.assertIn("w <= 0 || h <= 0", body)
        self.assertNotIn("BLUR_MODE_BILATERAL", body)
        self.assertNotIn("INTERP_POWER", body)

    def test_oracle_profile_removes_only_source_and_geometry(self):
        body = self.source.split(
            "static bool is_admitted_pf32_smart_oracle_profile", 1
        )[1].split("static bool checked_pixel_count", 1)[0]
        self.assertIn("p.power == 2.25f", body)
        self.assertIn("p.blur_size == 1", body)
        self.assertIn("p.interp_mode <= INTERP_POWER", body)
        self.assertNotIn("w != 17", body)
        self.assertNotIn("alpha", body)
        self.assertIn("PF32_POWER_GENERIC_MAX_ULP = 1", self.source)

    def test_pixel_count_is_checked_before_frame_allocation(self):
        checked = self.source.index("if (!checked_pixel_count(w, h, &pixel_count))")
        allocated = self.source.index("std::vector<float> alpha(pixel_count")
        self.assertLess(checked, allocated)
        self.assertIn("std::numeric_limits<size_t>::max() / sh", self.source)

    def test_pf32_smart_world_contract_is_bounded_aligned_disjoint_and_sdr(self):
        body = self.source.split(
            "static bool pf32_smart_worlds_are_bounded_sdr", 1
        )[1].split("static constexpr uint32_t PF32_POWER_GENERIC_MAX_ULP", 1)[0]
        # F41b retains checked storage products, replacing the beta area cap.
        self.assertIn("width > std::numeric_limits<size_t>::max() / height", body)
        self.assertIn("width * height > std::vector<long>().max_size()", body)
        self.assertNotIn("input->width > 4096", body)
        self.assertNotIn("4096u * 2160u / height", body)
        self.assertIn("alignof(PF_PixelFloat)", body)
        self.assertIn("require_disjoint", body)
        self.assertIn("!std::isfinite(value)", body)
        self.assertIn("value < 0.0f || value > 1.0f", body)


if __name__ == "__main__":
    unittest.main()
