#!/usr/bin/env python3
"""Keep the concise beta capability table tied to production predicates."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/BETA_SUPPORT.md"
README = ROOT / "README.md"

SOURCES = {
    "ColorKeep": ROOT / "mac/ColorKeep/ColorKeep.cpp",
    "OLMBlur": ROOT / "mac/OLMBlur/OLMBlur.cpp",
    "OLMColorKey": ROOT / "mac/OLMColorKey/OLMColorKey.cpp",
    "OLMDirectionalBlur": ROOT / "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp",
    "OLMDistanceGradation": ROOT / "mac/OLMDistanceGradation/OLMDistanceGradation.cpp",
    "OLMKiraKira": ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp",
    "OLMRadialBlur": ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp",
    "OLMSmoother": ROOT / "mac/OLMSmoother/Mac/OLMSmoother_port.cpp",
    "OLMSmoother2": ROOT / "mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp",
    "OLMToonDilate": ROOT / "mac/OLMToonDilate/OLMToonDilate.cpp",
}


class BetaSupportDocumentationContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.doc = DOC.read_text(encoding="utf-8")
        cls.readme = README.read_text(encoding="utf-8")
        cls.sources = {
            name: path.read_text(encoding="utf-8") for name, path in SOURCES.items()
        }

    def test_table_has_exactly_the_ten_shipped_plugins(self) -> None:
        rows = re.findall(r"^\| (?!プラグイン|---)([^|]+?) \|", self.doc, re.MULTILINE)
        self.assertEqual(rows, list(SOURCES))

    def test_depth_and_route_claims_are_anchored_in_dispatch_code(self) -> None:
        required_tokens = {
            "ColorKeep": ("Iterate8Suite2", "Iterate16Suite2", "IterateFloatSuite2"),
            "OLMBlur": ("bpc==8?4u:(bpc==16?8u:(bpc==32?16u:0u))", "SmartRender("),
            "OLMColorKey": ("RenderTyped<PF_Pixel8>", "RenderTyped<PF_Pixel16>", "RenderTyped<PF_PixelFloat>"),
            "OLMDirectionalBlur": ("CanUseGenericFrontOnly8", "RenderGenericFrontOnly16", "RenderGenericFrontOnly32"),
            "OLMDistanceGradation": ("RenderBits<PF_Pixel8>", "RenderBits<PF_Pixel16>", "RenderBits<PF_PixelFloat>"),
            "OLMKiraKira": ("IsGenericBetaMode12Tuple", "IsGenericBetaMode34TupleForGeometry", "BitDepthForFormat"),
            "OLMRadialBlur": ("IsGenericBaselineWorldPair<PixelT>", "RenderZoomTyped<PF_PixelFloat>"),
            "OLMSmoother": ("if (depth == 8 || depth == 16) return true", "V1ClassicAdmission"),
            "OLMSmoother2": ("V2GenericBetaAdmission", "depth != 8 && depth != 16 && depth != 32"),
            "OLMToonDilate": ("ValidateToonBetaAdmission<PF_Pixel8>", "ValidateToonBetaAdmission<PF_PixelFloat>"),
        }
        for plugin, tokens in required_tokens.items():
            for token in tokens:
                self.assertIn(token, self.sources[plugin], f"{plugin}: source claim drift: {token}")

    def test_parameter_and_geometry_limits_match_source_predicates(self) -> None:
        checks = {
            "OLMBlur": ("raw.amount < 1.0 || raw.amount > 1000.0", "width > 4096 || height > 2160", "raw.repeat < 1 || raw.repeat > 10"),
            "OLMColorKey": (
                "info.edge_blur_amount == 0.0",
                "info.edge_thin_amount >= -100.0 && info.edge_thin_amount <= 100.0",
                "info.edge_thin_distance_type >= 1 && info.edge_thin_distance_type <= 3",
                "IsGenericEdgeBlurTuple(info)",
            ),
            "OLMDirectionalBlur": ("info.front_strength > 0", "info.back_strength == 0", "info.noise_variation == 0.0"),
            "OLMDistanceGradation": ("p.blur_mode == BLUR_MODE_NONE", "p.interp_mode == INTERP_CONSTANT || p.interp_mode == INTERP_LINEAR", "is_admitted_pf32_smart_oracle_profile", "PF32_POWER_GENERIC_MAX_ULP == 1"),
            "OLMKiraKira": ("info.blur_mode == 1 || info.blur_mode == 2", "IsGenericBetaMode34TupleForGeometry", "width >= 9 && height >= 7"),
            "OLMRadialBlur": ("info.outer_strength >= 0 && info.outer_strength <= 64", "info.inner_strength == 0", "info.quality >= 1.0 && info.quality <= 5.0"),
            "OLMSmoother2": ("world->width < 16 || world->height < 16", "world->width > 8192 || world->height > 8192", "GAMMA_ALL_COLORS", "gamma_value >= 1.0 && gamma_value <= gamma_ui_max", "const A_FpLong gamma_ui_max = (A_FpLong)(float)2.4f", "smoothness >= 0 && smoothness <= 100"),
            "OLMToonDilate": ("info.search_radius < 0.0", "ValidateToonBetaAdmission<PF_Pixel8>", "RenderTileWorld", "ToonCheckedHalo", "output->origin_x - input->origin_x"),
        }
        for plugin, tokens in checks.items():
            for token in tokens:
                self.assertIn(token, self.sources[plugin], f"{plugin}: limit drift: {token}")

        self.assertIn("kBudgetBytes = 512ull * 1024ull * 1024ull", self.sources["OLMDirectionalBlur"])
        self.assertIn("info.search_radius > 100.0", self.sources["OLMToonDilate"])
        self.assertIn("count >= 1 && count <= COLORKEEP_MAX_COLORS", self.sources["ColorKeep"])
        radial = self.sources["OLMRadialBlur"]
        for token in (
            "info.outer_strength >= 0 && info.outer_strength <= 64",
            "info.center_x >= 0.0 && info.center_x <= (PF_FpLong)input->width",
            "info.ratio >= 1.0 && info.ratio <= 5.0",
            "info.angle_deg >= -360.0 && info.angle_deg <= 360.0",
            "info.quality >= 1.0 && info.quality <= 5.0",
            "info.inner_strength >= 0 && info.inner_strength <= 64",
            "info.outer_edge_fade >= 0 && info.outer_edge_fade <= 100",
            "info.inner_edge_fade >= 0 && info.inner_edge_fade <= 100",
            "const bool outer_offset_supported",
            "const bool inner_offset_supported",
            "IsGenericProceduralNoiseProfile(info)",
            "info.size_variation == 0.0 || info.size_variation == 1.0",
            "component_areas == std::vector<A_long>({1, 4, 9})",
            "IsGenericType3ZoomProfile<PixelT>",
            "info.noise_variation != 25.0 && info.noise_variation != 100.0",
            "info.noise_type == 1 && info.quality == 5.0",
            "info.noise_type == 2 && info.seed == 1 && info.noise_offset == 0",
        ):
            self.assertIn(token, radial)
        directional = self.sources["OLMDirectionalBlur"]
        for token in ("row[x].alpha > 32768", "IsGenericFrontOnlyDeepParameters", "GenericPF32SDRInput", "RenderExact8(input, output, nullptr, info, true)"):
            self.assertIn(token, directional)
        for claim in ("最大4096×2160", "Amount 1–1000", "Repeat 1–10", "最大HD 1920×1080", "最小9×7", "16×16–8192×8192", "Search Radius 0–100", "Enabled Color Num 1–100", "Edge Thin −100〜100", "Distance Type 1〜3", "Outer/Inner Strength整数0–64", "Noise Variation 25/100", "Size Variation 1/25/100", "最大1 ULP契約", "Gamma 1.0–2.4"):
            self.assertIn(claim, self.doc)

    def test_validation_language_does_not_overclaim(self) -> None:
        for phrase in (
            "Windows版とのbit完全一致はまだ主張しません",
            "Windows oracle／native AE検証は完了していません",
            "Windows oracleやnative AE検証の代替ではありません",
        ):
            self.assertIn(phrase, self.doc)

    def test_native_ae_quick_smoke_is_bounded_and_cumulative(self) -> None:
        summary = json.loads((
            ROOT / "refs/conformance/olm_all10_generic_beta_quick_ae_smoke_20260820.json"
        ).read_text(encoding="utf-8"))
        raw = json.loads((ROOT / summary["raw_report"]).read_text(encoding="utf-8"))
        self.assertEqual(summary["schema"], "olm.generic-beta-quick-ae-smoke/1")
        self.assertEqual(summary["status"], "pass")
        self.assertEqual((summary["passed"], summary["total"]), (10, 10))
        self.assertEqual(len(summary["plugins"]), 10)
        self.assertTrue(all(row["status"] == "passed" for row in summary["plugins"]))
        self.assertTrue(all(row["depth"] == 8 for row in summary["plugins"]))
        self.assertEqual(len({row["plugin"] for row in summary["plugins"]}), 10)
        self.assertTrue(all(re.fullmatch(r"[0-9a-f]{64}", row["installed_sha256"])
                            for row in summary["plugins"]))
        boundary = " ".join(summary["claim_boundary"])
        for phrase in ("1920x1080", "selected admitted parameter tuple", "not the 54-case", "No all-depth"):
            self.assertIn(phrase, boundary)
        self.assertEqual(raw["schema"], "olm.generic-beta-quick-ae-smoke-raw/1")
        self.assertEqual(len(raw["campaigns"]), 4)
        self.assertIn("failed", {row[1] for campaign in raw["campaigns"]
                                 for row in campaign["results"]})
        package_sha = "9a3b4ec68068ee05238913743e34bfbc5499c4bee0e6c79c5ec982c34011e41e"
        self.assertEqual(summary["package"]["sha256"], package_sha)
        final = raw["campaigns"][-1]
        self.assertEqual(final["status"], "completed")
        self.assertEqual(final["package_sha256"], package_sha)
        self.assertEqual(len(final["results"]), 10)
        self.assertTrue(all(row[1] == "passed" for row in final["results"]))
        final_hashes = {row[0]: row[2] for row in final["results"]}
        self.assertEqual(final_hashes,
                         {row["plugin"]: row["installed_sha256"] for row in summary["plugins"]})
        self.assertIn("exact binaries in the final package", boundary)
        self.assertIn("10プラグインすべてで通過", self.doc)
        self.assertIn("54-case smokeの代替ではありません", self.doc)

    def test_sanitizer_and_hd_4k_evidence_is_reported_fail_closed(self) -> None:
        sanitizer = json.loads(
            (ROOT / "refs/conformance/colorkeep_generic_beta_sanitizer_20260820.json").read_text(encoding="utf-8")
        )
        perf = json.loads(
            (ROOT / "reports/generic_beta_perf_smoke.json").read_text(encoding="utf-8")
        )
        self.assertEqual(sanitizer["status"], "pass")
        self.assertEqual(set(sanitizer["sanitizers"]), {"AddressSanitizer", "UndefinedBehaviorSanitizer"})
        self.assertIn("1920x1080", sanitizer["geometries"])
        self.assertIn("3840x2160", sanitizer["geometries"])
        self.assertIn("AddressSanitizer／UndefinedBehaviorSanitizer", self.doc)
        self.assertIn("1×1から4K", self.doc)
        rows = perf["results"]
        self.assertTrue(rows)
        failed = [row for row in rows if row["status"] == "failed"]
        self.assertEqual(failed, [], f"failed performance cells: {failed}")
        for row in rows:
            status = row["status"]
            if status == "passed":
                continue
            if status == "unsupported":
                self.assertTrue(row.get("reason"), row)
                self.assertTrue(row.get("support_predicate"), row)
                continue
            self.fail(f"supported performance cell was not measured: {row}")
        self.assertIn("対応セルはすべて成功", self.doc)
        self.assertIn("非対応セルはreasonとsupport predicate付き", self.doc)
        self.assertIn("未計測セルを成功扱いにしていません", self.doc)

        radial_perf = json.loads(
            (ROOT / "reports/generic_beta_perf_smoke_radial.json").read_text(encoding="utf-8")
        )
        radial_rows = [row for row in radial_perf["results"] if row["lane"] == "OLMRadialBlur"]
        self.assertEqual({row["geometry"] for row in radial_rows}, {"hd", "uhd"})
        self.assertTrue(all(row["status"] == "passed" for row in radial_rows))
        uhd = next(row for row in radial_rows if row["geometry"] == "uhd")
        self.assertEqual({(case["family"], case["depth_bpc"]) for case in uhd["case_results"]}, {
            (family, depth) for family in ("zoom", "rotation") for depth in (8, 16, 32)
        })
        self.assertIn("4K peak RSS約494 MiB", self.doc)

        classifier_doc = (
            ROOT / "refs/conformance/olmsmoother2_geometry_classifier_matrix_actual_aex_20260811.md"
        ).read_text(encoding="utf-8")
        self.assertIn("191 distinct switch indices", classifier_doc)
        self.assertIn("classifier 191/256はWindows exact", self.doc)
        self.assertIn("残る65/256はsafety-only", self.doc)

        self.assertIn("native AEの54-case smoke", self.doc)
        self.assertIn("milestoneまたはrelease candidate", self.doc)

    def test_readme_stays_concise_and_links_once(self) -> None:
        self.assertLessEqual(len(self.readme.splitlines()), 80)
        self.assertEqual(self.readme.count("docs/BETA_SUPPORT.md"), 1)
        self.assertNotIn("| プラグイン |", self.readme)

    def test_completion_audit_and_roi_dod_are_machine_readable(self) -> None:
        audit = json.loads((ROOT / "reports/public_beta_completion_audit_20260820.json").read_text())
        self.assertEqual(audit["schema"], "olm.public-beta-completion-audit/1")
        self.assertEqual(audit["overall"], "partial")
        self.assertEqual([row["plugin"] for row in audit["plugins"]], list(SOURCES))
        allowed = {"proven", "partial", "missing"}
        axes = ("arbitrary_image", "geometry_rowbytes", "parameters", "depth_route",
                "windows", "ae_host", "roi")
        for row in audit["plugins"]:
            self.assertTrue(all(row[axis] in allowed for axis in axes), row)
            self.assertTrue((ROOT / row["source"]).is_file(), row)
        self.assertTrue(all(row["arbitrary_image"] == "proven" for row in audit["plugins"]))
        self.assertTrue(all(row["ae_host"] == "partial" for row in audit["plugins"]))
        self.assertEqual(audit["criteria"]["native_ae_host"], "partial")
        self.assertEqual(audit["evidence"]["native_ae_current_roi"], "pending")
        package_report = json.loads(
            (ROOT / audit["evidence"]["current_roi_package_report"]).read_text()
        )
        self.assertEqual(package_report["schema"], "olm.public-beta-package/1")
        self.assertEqual(package_report["artifact_sha256"],
                         audit["evidence"]["current_roi_package_sha256"])
        self.assertEqual(package_report["generic_beta_gate"]["status"], "PASS")
        self.assertEqual(package_report["native_ae"]["current_roi_package"], "pending")
        roi = {row["plugin"]: row["roi"] for row in audit["plugins"]}
        self.assertEqual({name for name, status in roi.items() if status == "proven"},
                         {"ColorKeep", "OLMColorKey", "OLMToonDilate"})
        self.assertEqual({name for name, status in roi.items() if status == "partial"},
                         {"OLMDistanceGradation", "OLMDirectionalBlur", "OLMRadialBlur", "OLMSmoother2"})
        self.assertEqual({name for name, status in roi.items() if status == "missing"},
                         {"OLMBlur", "OLMKiraKira", "OLMSmoother"})
        self.assertEqual(audit["criteria"]["roi_tile_halo"], "partial")
        checkpoint = json.loads((ROOT / audit["evidence"]["windows_nonhd_roi_checkpoint"]).read_text())
        self.assertEqual(checkpoint["status"], "partial_complete")
        self.assertEqual(len(checkpoint["cases"]), 14)
        self.assertTrue(all(row["status"] == "ok" for row in checkpoint["cases"]))
        self.assertEqual(audit["evidence"]["windows_hd7"], "pending")
        for key in ("capability_contract", "hostless_gate", "performance", "native_ae_pre_roi",
                    "windows_nonhd_roi_checkpoint", "current_roi_package_report"):
            evidence = audit["evidence"][key]
            self.assertTrue((ROOT / evidence).is_file(), evidence)
        for claim in ("ROI／tile／halo", "full-frame出力", "必要halo", "非ゼロorigin",
                      "ROI外の出力とpadding", "ASan／UBSan clean", "tile render",
                      "finite-halo tile", "partial storage", "content bound", "14/14", "HD 7-case"):
            self.assertIn(claim, self.doc)
        self.assertIn("ROI実装前のmilestone package", self.doc)
        self.assertIn("現在のROI binariesはnative AE未実行", self.doc)
        self.assertNotIn("現在のgeneric buildはnative AE quick smoke", self.doc)


if __name__ == "__main__":
    unittest.main()
