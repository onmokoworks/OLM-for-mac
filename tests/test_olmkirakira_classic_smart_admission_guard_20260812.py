import json
import hashlib
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/emulation/test_olmkirakira_classic_smart_admission_guard_20260812.py"
REPORT = ROOT / "refs/conformance/olmkirakira_classic_smart_admission_guard_20260812.json"
SMART_REPORT = ROOT / "refs/conformance/olmkirakira_public_smart_bounded_closure_20260812.json"


class KiraClassicSmartAdmissionGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run(
            ["python3", str(SCRIPT), "--validate-only"], cwd=ROOT, check=True
        )
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))

    def test_validate_only_is_read_only(self) -> None:
        before = REPORT.read_bytes()
        subprocess.run(
            ["python3", str(SCRIPT), "--validate-only"], cwd=ROOT, check=True
        )
        self.assertEqual(REPORT.read_bytes(), before)

    def test_classic_map_is_fixed_and_mutations_fail_closed(self) -> None:
        self.assertEqual(self.report["status"], "exact_bounded_admission")
        self.assertEqual(self.report["classic"]["dimensions"], [5, 3])
        self.assertEqual(self.report["classic"]["row_padding_bytes"], 12)
        self.assertEqual(self.report["classic"]["admitted_declared_tuples"], 14)
        self.assertEqual(self.report["classic"]["rejected_mutations"], 7)
        self.assertEqual(
            self.report["classic"]["source_content_mutations_rejected"], 25
        )
        self.assertEqual(
            self.report["classic"]["layout_format_depth_mutations_rejected"], 22
        )
        self.assertEqual(
            set(self.report["classic"]["source_families"]),
            {"semi_transparent_color", "alpha_gradient"},
        )

    def test_smart_is_linked_to_canonical_bounded_closure(self) -> None:
        smart_evidence = json.loads(SMART_REPORT.read_text(encoding="utf-8"))
        self.assertEqual(
            self.report["smart"]["status"],
            "linked_raw_exact_bounded_public_smart",
        )
        self.assertEqual(smart_evidence["status"], "raw_exact_bounded_public_smart")
        self.assertEqual(self.report["smart"]["positive_cell_count"], 42)
        self.assertEqual(
            self.report["smart"]["canonical_cells_sha256"],
            smart_evidence["canonical_cells_sha256"],
        )
        self.assertEqual(
            self.report["smart"]["canonical_negative_rows_sha256"],
            smart_evidence["canonical_negative_rows_sha256"],
        )
        self.assertEqual(
            self.report["smart"]["evidence_sha256"],
            hashlib.sha256(SMART_REPORT.read_bytes()).hexdigest(),
        )
        self.assertTrue(self.report["smart"]["optional_pixel_checkin"])
        self.assertTrue(self.report["smart"]["all_negative_outputs_untouched"])
        checks = self.report["static_checks"]
        self.assertTrue(checks["smart_calls_checked_parameter_decoder"])
        self.assertTrue(checks["smart_calls_numeric_owner"])
        self.assertTrue(checks["smart_has_no_unconditional_bad_callback"])
        self.assertTrue(checks["smart_format_matches_declared_depth"])
        self.assertTrue(checks["smart_pixel_checkin_is_optional"])

    def test_mode3_32x18_is_separately_bounded(self) -> None:
        closure = self.report["mode3_32x18"]
        self.assertEqual(
            closure["status"], "linked_raw_exact_bounded_public_classic_and_smart"
        )
        self.assertEqual(closure["positive_cell_count"], 3)
        self.assertEqual(closure["dimensions"], [32, 18])
        self.assertEqual(closure["row_padding_bytes"], 12)
        self.assertIn("Rotation0", closure["tuple"])

    def test_world_pair_checks_format_layout_and_checkout_lifecycle(self) -> None:
        checks = self.report["static_checks"]
        self.assertTrue(checks["world_pair_validates_both_formats"])
        self.assertTrue(checks["layout_checks_active_rowbytes"])
        self.assertTrue(checks["classic_fixed_layout"])
        self.assertTrue(checks["classic_source_content_gate"])
        self.assertTrue(checks["smart_pixel_checkin_is_optional"])

    def test_isolated_build_is_universal_signed_and_not_installed(self) -> None:
        build = self.report["universal_isolated_build"]
        self.assertEqual(set(build["architectures"]), {"arm64", "x86_64"})
        self.assertTrue(build["codesign_verify_strict"])
        self.assertTrue(build["isolated_temp_product"])
        self.assertFalse(build["installed"])


if __name__ == "__main__":
    unittest.main()
