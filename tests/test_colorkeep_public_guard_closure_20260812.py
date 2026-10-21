#!/usr/bin/env python3
"""Regression gates for the bounded ColorKeep public-owner closure."""

from __future__ import annotations

import hashlib
import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "mac/ColorKeep/ColorKeep.cpp"
OWNER = ROOT / "refs/conformance/colorkeep_installed_public_covering_matrix_20260812.json"
CLOSURE = ROOT / "refs/conformance/colorkeep_public_guard_closure_20260812.json"
GENERATOR = ROOT / "tools/emulation/test_colorkeep_public_guard_closure_20260812.py"
OWNER_GENERATOR = ROOT / "tools/emulation/test_colorkeep_installed_public_covering_matrix_20260812.py"
AEX = ROOT / "aex/OLMColorKeep/Plugins/64/2025/ColorKeep.aex"
WORKER = Path("/Users/onmk/Documents/Projects/Personal/04_Tools/AEXCompat-issue1135-typed-iterate-suites/guest/target/release/aex-guest-worker")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ColorKeepPublicGuardClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.owner = json.loads(OWNER.read_text())
        cls.closure = json.loads(CLOSURE.read_text())

    def test_actual_exported_and_installed_owner_matrix_is_bound(self):
        owner = self.owner
        self.assertEqual(owner["status"], "installed_public_six_cell_raw_exact")
        self.assertEqual(owner["actual_aex_sha256"], sha(AEX))
        self.assertEqual(owner["aexcompat_worker"]["sha256"], sha(WORKER))
        self.assertEqual(owner["aexcompat_worker"]["commit"],
                         "0ee278943751b968ea2b0d5a0e0f483b70c0090d")
        self.assertEqual(len(owner["cells"]), 6)
        self.assertEqual({(row["enabled_count"], row["depth"]) for row in owner["cells"]},
                         {(count, depth) for count in (5, 100)
                          for depth in ("PF8", "PF16", "PF32")})
        for row in owner["cells"]:
            self.assertEqual(row["status"], "raw_exact")
            self.assertEqual(row["actual_exported_owner_sha256"],
                             row["installed_active_sha256"])
            self.assertTrue(row["smart_pre_render"]["completed"])
            self.assertTrue(row["smart_render"]["completed"])
        self.assertTrue(owner["input_complete_buffer_unchanged"])
        self.assertTrue(owner["input_padding_preserved"])
        self.assertTrue(owner["output_padding_preserved"])
        self.assertTrue(owner["world_headers_unchanged"])
        self.assertEqual(owner["mac_lifecycle_per_cell"]["parameter_checkouts"], 101)
        self.assertEqual(owner["mac_lifecycle_per_cell"]["parameter_checkins"], 101)

    def test_candidate_and_guard_cardinality_are_closed(self):
        closure = self.closure
        self.assertEqual(closure["status"],
                         "exact_bounded_public_owner_and_fail_closed_guards")
        self.assertEqual(closure["production_source_sha256"], sha(SOURCE))
        self.assertEqual(closure["owner_report_sha256"], sha(OWNER))
        self.assertEqual(closure["owner_cells"], 6)
        self.assertTrue(closure["candidate_matches_actual_exported_owner"])
        self.assertEqual(closure["candidate_active_sha256"],
                         [row["actual_exported_owner_sha256"]
                          for row in self.owner["cells"]])
        self.assertTrue(closure["candidate_classic_matches_corresponding_exported_smart_owner"])
        self.assertEqual(closure["candidate_classic_active_sha256"],
                         [self.owner["cells"][index]["actual_exported_owner_sha256"]
                          for index in (0, 1, 3, 4)])
        guards = closure["guards"]
        self.assertEqual((guards["smart_one_away_rejects"],
                          guards["classic_one_away_rejects"],
                          guards["total_rejects"]), (38, 24, 62))
        self.assertTrue(guards["all_rejected_before_iteration"])
        self.assertTrue(guards["input_and_headers_unchanged"])
        self.assertTrue(guards["output_unchanged"])
        self.assertEqual(guards["smart_parameter_phases"], {
            "order": "checkout_all_then_convert_all_then_checkin_all",
            "full_path_counts": [101, 100, 101],
            "first_checkin_error": {
                "error_position": 17, "first_error_preserved": True,
                "counts": [101, 100, 101],
            },
            "color_error": {
                "error_position": 17, "first_error_preserved": True,
                "counts": [101, 17, 101],
            },
            "missing_color_suite_cleanup_counts": [101, 0, 101],
        })
        self.assertEqual(closure["admission"]["geometry"], [11, 7])
        self.assertEqual(closure["admission"]["enabled_color_counts"], [5, 100])
        self.assertEqual(closure["admission"]["classic_pf32"], "fail_closed")

    def test_isolated_build_is_universal_and_identity_bound(self):
        build = self.closure["isolated_universal_build"]
        bundle = Path(build["bundle"])
        binary = Path(build["binary"])
        self.assertEqual(binary, bundle / "Contents/MacOS/ColorKeep")
        self.assertTrue(binary.is_file())
        self.assertEqual(build["binary_sha256"], sha(binary))
        self.assertEqual(build["info_plist_sha256"],
                         sha(bundle / "Contents/Info.plist"))
        self.assertEqual(build["resource_sha256"],
                         sha(bundle / "Contents/Resources/ColorKeep.rsrc"))
        self.assertEqual(build["build_log_sha256"], sha(Path(build["build_log"])))
        actual_archs = subprocess.check_output(["lipo", "-archs", str(binary)],
                                               text=True).split()
        self.assertEqual(actual_archs, build["architectures"])
        self.assertEqual(set(actual_archs), {"arm64", "x86_64"})
        self.assertEqual(build["codesign_verify"], "pass")
        verify = subprocess.run(["codesign", "--verify", "--deep", "--strict",
                                 "--verbose=2", str(bundle)],
                                capture_output=True, text=True)
        self.assertEqual(verify.returncode, 0, verify.stdout + verify.stderr)

    def test_source_contains_the_bounded_admission_and_lifecycle_guards(self):
        source = SOURCE.read_text()
        required = [
            "kColorKeepPublicWidth = 11", "kColorKeepPublicHeight = 7",
            "kColorKeepPublicPadding = 12", "count == 5 || count == COLORKEEP_MAX_COLORS",
            "ColorKeepPublicPaletteMatches", "ColorKeepValidateWorldPair",
            "input->extent_hint.right != expected_width",
            "input->world_flags != expected_flags", "input->origin_x != 0",
            "input_begin < output_end",
            "input_format != output_format", "case PF_PixelFormat_ARGB64",
            "input_format != expected_format", "output_format != expected_format",
            "default: return PF_Err_BAD_CALLBACK_PARAM",
            "const bool input_checked_out = err == PF_Err_NONE",
            "if (input_checked_out && extra->cb->checkin_layer_pixels)",
            "if (!err) err = checkin_err",
            "catch (PF_Err &thrown_err)",
            "for (A_long i = 0; i < COLORKEEP_MAX_COLORS && !err; ++i)",
            "for (A_long i = 0; i <= COLORKEEP_MAX_COLORS; ++i)",
            "checked_out[i] = false",
        ]
        for token in required:
            self.assertIn(token, source)
        self.assertIn("ColorKeepPublicPaletteMatches(info, COLORKEEP_MAX_COLORS)", source)

    def test_validate_only_is_green(self):
        result = subprocess.run(["python3", str(GENERATOR), "--validate-only"],
                                cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS", result.stdout)
        self.assertTrue(OWNER_GENERATOR.is_file())


if __name__ == "__main__":
    unittest.main()
