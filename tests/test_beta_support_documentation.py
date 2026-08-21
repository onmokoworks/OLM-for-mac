#!/usr/bin/env python3
"""Keep the concise beta capability table tied to production predicates."""

from __future__ import annotations

import hashlib
import json
import re
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/BETA_SUPPORT.md"
README = ROOT / "README.md"
SMOOTHER2_GAMMA_COLORS_TEST = (
    ROOT / "tests/test_olmsmoother2_gamma_colors_beta_20260820.py"
)
DIRECTIONAL_BUDGET = ROOT / "core/dblur_generic_budget.h"
DIRECTIONAL_BACKONLY_DIRECT = (
    ROOT / "tools/emulation/test_dblur_generic_backonly_beta_20260821.py"
)
DIRECTIONAL_BACKONLY_EFFECTMAIN = (
    ROOT / "tools/emulation/test_dblur_generic_backonly_effectmain_20260821.py"
)
DIRECTIONAL_BACKONLY_ANCHOR = (
    ROOT / "refs/conformance/dblur_mode1_backonly_portable_20260805.json"
)
KIRAKIRA_MODE3_HELPER_CHAIN = (
    ROOT / "refs/conformance/olmkirakira_mode3_geometry_generalization_actual_aex_20260810.json"
)
KIRAKIRA_MODE3_WINDOWS_OWNER_REPORT = (
    ROOT / "refs/conformance/olmkirakira_mode3_ui_windows_owner_20260821.json"
)
KIRAKIRA_MODE3_WINDOWS_OWNER_DIGEST = (
    ROOT / "refs/conformance/olmkirakira_mode3_ui_windows_owner_20260821.sha256"
)
KIRAKIRA_MODE3_WINDOWS_OWNER_TEST = (
    ROOT / "tests/test_olmkirakira_mode3_ui_windows_owner_20260821.py"
)
KIRAKIRA_MODE3_WINDOWS_OWNER_VERIFIER = (
    ROOT / "tools/emulation/test_olmkirakira_mode3_ui_windows_owner_20260821.py"
)

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
        cls.directional_budget = DIRECTIONAL_BUDGET.read_text(encoding="utf-8")

    def test_table_has_exactly_the_ten_shipped_plugins(self) -> None:
        rows = re.findall(r"^\| (?!プラグイン|---)([^|]+?) \|", self.doc, re.MULTILINE)
        self.assertEqual(rows, list(SOURCES))

    def test_depth_and_route_claims_are_anchored_in_dispatch_code(self) -> None:
        required_tokens = {
            "ColorKeep": ("Iterate8Suite2", "Iterate16Suite2", "IterateFloatSuite2"),
            "OLMBlur": ("bpc==8?4u:(bpc==16?8u:(bpc==32?16u:0u))", "SmartRender("),
            "OLMColorKey": ("RenderTyped<PF_Pixel8>", "RenderTyped<PF_Pixel16>", "RenderTyped<PF_PixelFloat>"),
            "OLMDirectionalBlur": ("CanUseGenericNeutral8", "RenderGenericNeutral16", "RenderGenericNeutral32"),
            "OLMDistanceGradation": ("RenderBits<PF_Pixel8>", "RenderBits<PF_Pixel16>", "RenderBits<PF_PixelFloat>"),
            "OLMKiraKira": ("IsGenericBetaMode12Tuple", "IsGenericBetaMode3HorizontalTuple", "IsGenericBetaMode3BudgetAdmitted", "BitDepthForFormat"),
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
                "IsGenericEdgeCompositionTuple(info)",
                "info.edge_blur_direction == 102",
                "info.edge_thin_amount == -4.0 || info.edge_thin_amount == 4.0",
            ),
            "OLMDirectionalBlur": (
                "const bool any_side = info.front_strength != 0 || info.back_strength != 0",
                "info.front_strength < 0",
                "info.back_strength > 4000",
                "info.noise_variation == 0.0",
            ),
            "OLMDistanceGradation": ("p.blur_mode == BLUR_MODE_NONE", "p.interp_mode == INTERP_CONSTANT || p.interp_mode == INTERP_LINEAR", "is_admitted_pf32_smart_oracle_profile", "PF32_POWER_GENERIC_MAX_ULP == 1"),
            "OLMKiraKira": (
                "info.blur_mode == 1 || info.blur_mode == 2",
                "IsGenericBetaMode3HorizontalTuple",
                "info.horizontal_length < 1",
                "info.horizontal_length > 300",
                "owner_tuple.horizontal_length = 50",
                "IsGenericBetaMode3BudgetAdmitted",
                "kMaxGenericPixels",
                "kMaxPluginOwnedBytes",
                "kMaxMode3WorkUnits",
                "GenericBetaInputIsFiniteSDR",
                "generic_full_frame_request",
                "request_contains_known_full_frame",
                "width >= 9 && height >= 7",
            ),
            "OLMRadialBlur": ("info.outer_strength >= 0 && info.outer_strength <= 64", "info.inner_strength == 0", "info.quality >= 1.0 && info.quality <= 5.0"),
            "OLMSmoother2": ("world->width < 16 || world->height < 16", "world->width > 8192 || world->height > 8192", "GAMMA_ALL_COLORS", "gamma_mode == GAMMA_COLORS_ONLY", "gamma_count >= 1 && gamma_count <= NUM_GAMMA_COLORS", "gamma_value >= 1.0 && gamma_value <= gamma_ui_max", "const A_FpLong gamma_ui_max = (A_FpLong)(float)2.4f", "smoothness >= 0 && smoothness <= 100", "custom/user LUT", "!retained_fixture && V2GenericBetaAdmission"),
            "OLMToonDilate": ("info.search_radius < 0.0", "ValidateToonBetaAdmission<PF_Pixel8>", "RenderTileWorld", "ToonCheckedHalo", "output->origin_x - input->origin_x"),
        }
        for plugin, tokens in checks.items():
            for token in tokens:
                self.assertIn(token, self.sources[plugin], f"{plugin}: limit drift: {token}")

        for token in (
            "kMaximumDimension = 4096u",
            "kMaximumSourcePixels = 4096u * 2160u",
            "kPluginOwnedLiveLimitBytes",
            "3u * 1024u * 1024u * 1024u",
            "kUnmodelledAllocationReserveBytes",
            "64u * 1024u * 1024u",
            "kOperationUnitLimit = 350000000ull",
            "EstimateOperationUnits",
            "EstimateRender",
        ):
            self.assertIn(token, self.directional_budget)
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
        for token in (
            "pixel.alpha > 32768",
            "IsGenericNeutralDeepParameters",
            "IsRetainedNeutralBackExact8",
            "IsRetainedNeutralBackExact16",
            "IsRetainedNeutralBackExact32",
            "IsRetainedNeutralDualExact16",
            "GenericPF32SDRInput",
            "RenderExact8(input, output, nullptr, info, true)",
        ):
            self.assertIn(token, directional)
        for claim in ("最大4096×2160", "Amount 1–1000", "Repeat 1–10", "3 GiB per-render plugin-owned admission", "3億5000万work-unit", "最小9×7", "1 GiB per-render plugin-owned", "120億work-unit", "Horizontal-only", "Length 1–300", "Rotation 0/1", "16×16–8192×8192", "Search Radius 0–100", "Enabled Color Num 1–100", "Edge Thin −100〜100", "Distance Type 1〜3", "Size Variation 25/100 × procedural Noise Variation 25/100 Type 1/2", "1 GiB plugin-owned／350M work cap", "最大1 ULP契約", "Gamma 1.0–2.4"):
            self.assertIn(claim, self.doc)
        for claim in ("Thin ±4／DT2", "materialized 102", "full-frameのみ",
                      "任意source Windows exactは未主張", "native quickはEdge 0",
                      "Front／Backの片側または両側", "9 cases/geometry",
                      "actual-AEX raw-callback／production replay anchorはPF8 960×540・Back 240・Angle 0・Gain 1・scale 0.5",
                      "native AE saved-frameではない",
                      "16×16 retained exact unionはPF8 Back 8・Angle 0/45・Gain 1",
                      "PF16 Back 1/2/8・Angle 45・Gain 1",
                      "PF16 Dual Front 1/2/8＋Back 1・Angle 45・Gain 1",
                      "PF32 Back 1・Angle 0/45・Gain 0.5/1およびBack 8・Angle 45・Gain 1",
                      "すべてscale 1",
                      "一般geometry・全Strength組合せ・generic DualのWindows exact・native AE・ROI v2 packageには遡及しない",
                      "current canonical性能reportはHD/UHDそれぞれFront／Back／Dual×PF8/PF16/PF32の9 cases/geometry",
                      "source/toolchainの実行前後一致",
                      "UI全300 Length×3深度=900",
                      "HD/UHD各15 cases",
                      "hostless helper chainは代表14 Lengthの66 cases／497,250 words exact",
                      "zero-alpha／nonzero-RGBを含む固定17×11 source",
                      "Length {1,2,50,300}×raw-fixed Rotation {0,1}×PF8/16/32",
                      "24/24がMac public EffectMain Classic/Smartとraw active-byte exact",
                      "全Length 1–300、任意source／geometry",
                      "Windows padded rowbytes／Classic",
                      "native Windows UCRT／trigonometry",
                      "旧fixture-only source／extent／stride negativesはgeneric safety契約に置換",
                      "Gamma Colors palette count 1–5",
                      "palette order／duplicate／inactive tail／alpha semantics", "custom/user LUTは拒否"):
            self.assertIn(claim, self.doc)

        direct = DIRECTIONAL_BACKONLY_DIRECT.read_text(encoding="utf-8")
        effectmain = DIRECTIONAL_BACKONLY_EFFECTMAIN.read_text(encoding="utf-8")
        for token in (
            "PASS_DBLUR_GENERIC_BACKONLY_BETA",
            "positive_depth<PF_Pixel8>(8)",
            "positive_depth<PF_Pixel16>(16)",
            "positive_depth<PF_PixelFloat>(32)",
        ):
            self.assertIn(token, direct)
        for token in (
            "PASS_DBLUR_GENERIC_BACKONLY_EFFECTMAIN",
            "PF_Cmd_RENDER",
            "PF_Cmd_SMART_PRE_RENDER",
            "PF_Cmd_SMART_RENDER",
            "back=2/8",
        ):
            self.assertIn(token, effectmain)
        anchor = json.loads(DIRECTIONAL_BACKONLY_ANCHOR.read_text(encoding="utf-8"))
        self.assertEqual(anchor["status"], "pass")
        self.assertTrue(anchor["checks"]["actual_aex_raw_exact"])
        self.assertEqual(anchor["parameters"]["back_strength_ui"], 240)
        self.assertEqual(anchor["parameters"]["angle"], 0)
        self.assertEqual(anchor["parameters"]["brightness_gain"], 1)
        self.assertEqual(anchor["parameters"]["render_scale"], 0.5)
        self.assertFalse(anchor["claim_boundary"]["windows_ae_pixel_exact"])
        self.assertIn("saved-frame", anchor["claim_boundary"]["remaining"])

        exact8 = directional.split("static bool IsRetainedNeutralBackExact8", 1)[1].split(
            "static bool IsRetainedNeutralBackExact16", 1
        )[0]
        exact16 = directional.split("static bool IsRetainedNeutralBackExact16", 1)[1].split(
            "static bool IsRetainedNeutralBackExact32", 1
        )[0]
        exact32 = directional.split("static bool IsRetainedNeutralBackExact32", 1)[1].split(
            "static bool IsRetainedNeutralBackExact(", 1
        )[0]
        for token in (
            "info.back_strength == 8",
            "info.angle_deg == 0.0 || info.angle_deg == 45.0",
            "info.brightness_gain != 1.0",
            "info.back_strength == 240 && info.angle_deg == 0.0",
            "info.render_scale_x == 0.5 && info.render_scale_y == 0.5",
        ):
            self.assertIn(token, exact8)
        for token in (
            "info.back_strength == 1 || info.back_strength == 2",
            "info.back_strength == 8) && info.angle_deg == 45.0",
            "info.brightness_gain == 1.0",
            "info.render_scale_x == 1.0",
        ):
            self.assertIn(token, exact16)
        for token in (
            "info.back_strength == 1",
            "info.angle_deg == 0.0 || info.angle_deg == 45.0",
            "info.brightness_gain == 0.5 || info.brightness_gain == 1.0",
            "info.back_strength == 8 && info.angle_deg == 45.0",
            "info.brightness_gain == 1.0",
            "info.render_scale_x == 1.0",
        ):
            self.assertIn(token, exact32)

        gamma_colors_test = SMOOTHER2_GAMMA_COLORS_TEST.read_text(encoding="utf-8")
        for token in (
            "for (int depth : {{8,16,32}})",
            "for (int version : {{SMOOTHER_V1,SMOOTHER_V2}})",
            "normal.output != order.output",
            "normal.output != duplicate.output",
            "count_one.output != inactive_tail.output",
            "normal.output != alpha.output",
        ):
            self.assertIn(token, gamma_colors_test)

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

    def test_current_roi_v2_native_ae_quick_smoke_is_bounded(self) -> None:
        summary_path = ROOT / "refs/conformance/olm_all10_roi_v2_quick_ae_smoke_20260820.json"
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        raw = json.loads((ROOT / summary["raw_report"]).read_text(encoding="utf-8"))
        self.assertEqual(summary["schema"], "olm.roi-v2-quick-ae-smoke/1")
        self.assertEqual(summary["status"], "pass")
        self.assertEqual((summary["passed"], summary["total"]), (10, 10))
        self.assertEqual(summary["package"]["sha256"],
                         "7c8fb27e69ccb0a3fb2708ab026172e67050e8e15eff5acb49daf82d8f42b72b")
        self.assertEqual(summary["package"]["path"],
                         "handoff/public_beta/olm_mac_plugins_PublicBeta_ROI_v2_20260820.zip")
        self.assertEqual(summary["execution_branch"], "codex/public-beta-roi")
        self.assertEqual(summary["execution_head"],
                         "3a97926a4bd5bf9baaad4151b6af5dfb0e1845a7")
        self.assertEqual(summary["package_build_git_commit"],
                         "f4e4dac86925b512d4c7b8784d250f1a68871cb7")
        self.assertTrue(summary["package_build_git_dirty"])
        self.assertEqual(summary["mediacore_backup"],
                         "handoff/mac_plugin_backups/mediacore_20260820_232857")
        self.assertEqual(raw["schema"], "olm.roi-v2-quick-ae-smoke-raw/1")
        self.assertRegex(raw["source_campaign_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(raw["package"], summary["package"])
        self.assertEqual(raw["execution_head"], summary["execution_head"])
        self.assertEqual(raw["package_build_git_commit"],
                         summary["package_build_git_commit"])
        self.assertEqual(raw["package_build_git_dirty"],
                         summary["package_build_git_dirty"])
        self.assertEqual(raw["mediacore_backup"], summary["mediacore_backup"])
        self.assertIn("recomputed after the campaign", raw["final_artifact_validation"])
        self.assertIn("not authoritative", raw["final_artifact_validation"])
        self.assertEqual(len(raw["cases"]), 10)
        self.assertTrue(all(row["status"] == "passed" and row["depth"] == 8 and
                            row["geometry"] == [1920, 1080] and row["output_size_bytes"] > 0
                            for row in raw["cases"]))
        for row in raw["cases"]:
            self.assertRegex(row["installed_sha256"], r"^[0-9a-f]{64}$")
            self.assertRegex(row["output_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(dict(summary["plugins"]),
                         {row["plugin"]: row["installed_sha256"] for row in raw["cases"]})
        color_key = next(row for row in raw["cases"] if row["plugin"] == "OLMColorKey")
        self.assertEqual(color_key["tuple"], "pixel-local defaults (Edge Thin/Blur 0)")
        boundary = " ".join(summary["claim_boundary"])
        for phrase in ("Current ROI v2 binaries", "full-frame 1920x1080",
                       "first declared depth", "selected admitted tuple",
                       "not the 54-case", "does not prove partial ROI or tile parity"):
            self.assertIn(phrase, boundary)
        self.assertIn("immutable ROI v2 package", self.doc)
        self.assertIn("今回の10件はすべて8 bpc", self.doc)
        self.assertIn("partial ROI／tile parityをnative AEで証明するものではありません", self.doc)
        self.assertIn("パッケージ後のソース／文書変更", self.doc)

    def _assert_roi_v2_package_report(
        self, local_archive: Path | None
    ) -> bool:
        report = json.loads((
            ROOT / "reports/public_beta_roi_v2_package_20260820.json"
        ).read_text(encoding="utf-8"))
        self.assertEqual(report["artifact"],
                         "handoff/public_beta/olm_mac_plugins_PublicBeta_ROI_v2_20260820.zip")
        self.assertRegex(report["artifact_sha256"], r"^[0-9a-f]{64}$")
        self.assertGreater(report["artifact_size_bytes"], 0)
        self.assertEqual(report["package_manifest"]["path"],
                         "OLM_Mac_Plugins_Release/manifest.json")
        self.assertRegex(report["package_manifest"]["sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(report["package_manifest"]["git_commit"],
                         report["package_build_git_commit"])
        self.assertEqual(report["package_manifest"]["git_dirty"],
                         report["package_build_git_dirty"])
        self.assertEqual(report["beta_support"]["embedded_path"],
                         "OLM_Mac_Plugins_Release/BETA_SUPPORT.md")
        self.assertEqual(report["beta_support"]["embedded_sha256"],
                         report["beta_support_sha256"])
        self.assertRegex(report["beta_support_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(report["beta_support"]["manifest_field"],
                         "beta_support_sha256")
        self.assertEqual(report["beta_support"]["live_repository_path"],
                         "docs/BETA_SUPPORT.md")
        self.assertFalse(
            report["beta_support"]["live_repository_document_is_package_payload"]
        )
        self.assertNotEqual(hashlib.sha256(DOC.read_bytes()).hexdigest(),
                            report["beta_support_sha256"])
        self.assertIn("not the SHA-256 of the live docs/BETA_SUPPORT.md",
                      report["beta_support_scope"])
        self.assertIn("intentionally not substituted",
                      report["beta_support"]["relationship"])
        self.assertIn("immutable manifest hash", self.doc)
        self.assertIn("live文書のhashでpackage manifest値を置き換えることもありません",
                      self.doc)
        self.assertEqual(list(report["plugins"]), list(SOURCES))
        self.assertTrue(all(re.fullmatch(r"[0-9a-f]{64}", digest)
                            for digest in report["plugins"].values()))

        native = report["native_ae"]
        summary = json.loads((
            ROOT / native["current_roi_package_evidence"]
        ).read_text(encoding="utf-8"))
        self.assertEqual(native["current_roi_package"],
                         "partial / quick 10/10 passed")
        self.assertEqual(native["status"], "PASS_BOUNDED_QUICK_SMOKE")
        self.assertEqual((native["passed"], native["total"]), (10, 10))
        self.assertEqual(native["artifact_sha256"], report["artifact_sha256"])
        self.assertEqual(summary["package"]["sha256"], report["artifact_sha256"])
        self.assertEqual(dict(summary["plugins"]), report["plugins"])
        self.assertIn("all ten selected cases were 8 bpc", native["coverage"]["depth"])
        excluded = " ".join(native["not_proven"])
        for phrase in ("54-case", "all-depth", "partial ROI", "Windows-to-Mac",
                       "after this package was built"):
            self.assertIn(phrase, excluded)
        for phrase in ("immutable artifact", "10/10", "8 bpc", "not the 54-case",
                       "later live-source/document changes"):
            self.assertIn(phrase, report["claim_boundary"])

        if local_archive is None:
            return False

        package_bytes = local_archive.read_bytes()
        self.assertEqual(hashlib.sha256(package_bytes).hexdigest(),
                         report["artifact_sha256"])
        self.assertEqual(len(package_bytes), report["artifact_size_bytes"])
        with zipfile.ZipFile(local_archive) as archive:
            manifest_bytes = archive.read(report["package_manifest"]["path"])
            embedded_doc = archive.read(report["beta_support"]["embedded_path"])
        manifest = json.loads(manifest_bytes)
        self.assertEqual(hashlib.sha256(manifest_bytes).hexdigest(),
                         report["package_manifest"]["sha256"])
        self.assertEqual(manifest["git_commit"], report["package_build_git_commit"])
        self.assertEqual(manifest["git_dirty"], report["package_build_git_dirty"])
        embedded_sha = hashlib.sha256(embedded_doc).hexdigest()
        self.assertEqual(embedded_sha, manifest["beta_support_sha256"])
        self.assertEqual(embedded_sha, report["beta_support_sha256"])
        manifest_plugins = {
            row["name"]: row["binary_sha256"] for row in manifest["plugins"]
        }
        self.assertEqual(manifest_plugins, report["plugins"])
        return True

    def test_roi_v2_package_report_binds_immutable_payload_not_live_docs(self) -> None:
        report = json.loads((
            ROOT / "reports/public_beta_roi_v2_package_20260820.json"
        ).read_text(encoding="utf-8"))
        package_path = ROOT / report["artifact"]
        local_archive = package_path if package_path.is_file() else None
        self.assertEqual(
            self._assert_roi_v2_package_report(local_archive),
            local_archive is not None,
        )

    def test_roi_v2_package_report_clean_checkout_needs_no_ignored_archive(self) -> None:
        # Simulate a clean checkout even when the ignored distribution artifact is
        # present locally. Durable report/summary assertions still execute; only
        # the optional byte-level archive comparison is absent.
        self.assertFalse(self._assert_roi_v2_package_report(None))

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
        self.assertEqual(len(rows), 20)
        self.assertEqual({(row["lane"], row["geometry"]) for row in rows}, {
            (plugin, geometry) for plugin in SOURCES for geometry in ("hd", "uhd")
        })
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
        self.assertIn("current live-source", self.doc)
        self.assertIn("20セルを実測し、20/20成功", self.doc)
        self.assertIn("9 cases/geometryを各active Strength 2", self.doc)
        self.assertIn("実行前後でhash照合", self.doc)
        self.assertEqual(perf["provenance"]["binding_mode"], "execution_pre_and_post")
        self.assertEqual(
            perf["provenance"]["measurement_source_identity"],
            "exact_pre_and_post_match",
        )
        self.assertTrue(perf["provenance"]["post_run_dependency_match"])
        self.assertTrue(perf["provenance"]["post_run_toolchain_match"])
        directional = [row for row in rows if row["lane"] == "OLMDirectionalBlur"]
        self.assertEqual({row["geometry"] for row in directional}, {"hd", "uhd"})
        self.assertTrue(all(row["status"] == "passed" for row in directional))
        expected_directional_cases = {
            (side, depth, front, back)
            for depth in (8, 16, 32)
            for side, front, back in (
                ("front", 2, 0), ("back", 0, 2), ("dual", 2, 2)
            )
        }
        for row in directional:
            cases = row.get("case_results", [])
            self.assertEqual(
                len(cases), 9,
                "stale Directional performance report: expected exactly nine "
                "neutral single/dual cases per geometry",
            )
            observed = {
                (case.get("side"), case.get("depth"),
                 case.get("front_strength"), case.get("back_strength"))
                for case in cases
            }
            self.assertEqual(
                observed,
                expected_directional_cases,
                "stale Directional performance report: regenerate it with nine "
                "Front/Back/Dual cases per geometry before restoring the "
                "performance claim",
            )
            self.assertTrue(all(case.get("angle") == 37.25 for case in cases))
            self.assertTrue(all(case.get("brightness_gain") == 0.75
                                for case in cases))

        kirakira = [row for row in rows if row["lane"] == "OLMKiraKira"]
        self.assertEqual({row["geometry"] for row in kirakira}, {"hd", "uhd"})
        expected_kira_profiles = {
            ("box", "m1_h7_r0", 7, 0.0),
            ("approximated_gaussian", "m2_h7_ramp_r0", 7, 0.0),
            ("gaussian_length50", "m3_h50_r0", 50, 0.0),
            ("exponential", "m4_highlight_r3", 0, 0.0),
            ("gaussian_length300", "m3_ui_length", 300, 1.0),
        }
        expected_kira_cases = {
            (*profile, depth)
            for profile in expected_kira_profiles
            for depth in (8, 16, 32)
        }
        for row in kirakira:
            cases = row.get("case_results", [])
            self.assertEqual(len(cases), 15)
            self.assertEqual(
                {(case["mode"], case["tuple"], case["horizontal_length"],
                  case["rotation_degrees"], case["depth_bpc"])
                 for case in cases},
                expected_kira_cases,
            )
            self.assertTrue(all(
                case["returncode"] == 0 and case["wall_seconds"] > 0 and
                case["peak_rss_bytes"] > 0 and case["classic_smart_parity"] and
                case["deterministic"] and case["independent_strides"] and
                case["input_span_unchanged"] and
                case["output_padding_unchanged"] and
                case["output_active_changed"] and
                case["content_bounds"] == "full" and
                case["callback_shape"] == "1/1/1/0"
                for case in cases
            ))
            self.assertLess(row["wall_seconds"], row["timeout_seconds"])
            self.assertLessEqual(row["peak_rss_bytes"], row["rss_budget_bytes"])
            self.assertIn(f"{row['wall_seconds']:.2f}秒", self.doc)
            self.assertIn(f"{row['peak_rss_bytes']:,} bytes", self.doc)
            for fragment in (
                "mode3_horizontal_only",
                "1 <= length <= 300",
                "per_render_plugin_owned_bytes <= 1073741824",
                "mode3_work_units <= 12000000000",
            ):
                self.assertIn(fragment, row["support_predicate"])
        self.assertIn("Mode 3 Horizontal Length 300・Rotation 1", self.doc)
        self.assertIn("DCI 4096×2160 endpointの実測", self.doc)

        helper = json.loads(KIRAKIRA_MODE3_HELPER_CHAIN.read_text(encoding="utf-8"))
        self.assertEqual(helper["status"], "captured")
        self.assertEqual(
            helper["aex_sha256"],
            "60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7",
        )
        self.assertEqual(len(helper["cases"]), 66)
        self.assertEqual(
            {case["length"] for case in helper["cases"]},
            {1, 2, 3, 5, 7, 9, 11, 25, 50, 100, 200, 300, 301, 1000},
        )
        self.assertEqual(
            {case["angle_degrees"] for case in helper["cases"]},
            {-45, 0, 17, 45},
        )
        self.assertEqual(
            sum(
                len(case[stage]["words_u32"])
                for case in helper["cases"]
                for stage in ("forward", "gaussian", "final")
            ),
            497250,
        )
        self.assertIn("代表14 Length", self.doc)
        self.assertIn(helper["aex_sha256"], self.doc)

        radial_perf = json.loads(
            (ROOT / "reports/generic_beta_perf_smoke.json").read_text(encoding="utf-8")
        )
        radial_rows = [row for row in radial_perf["results"] if row["lane"] == "OLMRadialBlur"]
        self.assertEqual({row["geometry"] for row in radial_rows}, {"hd", "uhd"})
        self.assertTrue(all(row["status"] == "passed" for row in radial_rows))
        uhd = next(row for row in radial_rows if row["geometry"] == "uhd")
        self.assertEqual({(case["family"], case["profile"], case["depth_bpc"]) for case in uhd["case_results"]}, {
            (family, profile, depth) for family in ("zoom", "rotation")
            for profile in ("baseline", "size_noise") for depth in (8, 16, 32)
        })
        self.assertEqual(len(uhd["case_results"]), 12)
        self.assertIn("HD 8.38 s / 255787008 B", self.doc)
        self.assertIn("UHD 16.52 s / 704692224 B", self.doc)
        self.assertIn("一般4連結topology", self.doc)
        self.assertIn("1 GiB plugin-owned／350M work cap", self.doc)

        classifier_doc = (
            ROOT / "refs/conformance/olmsmoother2_geometry_classifier_matrix_actual_aex_20260811.md"
        ).read_text(encoding="utf-8")
        self.assertIn("191 distinct switch indices", classifier_doc)
        self.assertIn("classifier 191/256はWindows exact", self.doc)
        self.assertIn("残る65/256はsafety-only", self.doc)

        self.assertIn("native AEの54-case smoke", self.doc)
        self.assertIn("milestoneまたはrelease candidate", self.doc)

    def test_kirakira_mode3_windows_owner_report_is_exact_and_bounded(self) -> None:
        report = json.loads(
            KIRAKIRA_MODE3_WINDOWS_OWNER_REPORT.read_text(encoding="utf-8")
        )
        self.assertEqual(report["schema"], "olmkirakira.mode3-ui-windows-owner/1")
        self.assertEqual(report["status"], "raw_active_bytes_exact")
        self.assertEqual(report["date"], "2026-08-21")
        self.assertEqual(report["summary"], {
            "active_bytes_per_depth": {"PF8": 748, "PF16": 1496, "PF32": 2992},
            "all_routes_exact": True,
            "all_windows_lifecycle_exact": True,
            "cell_count": 24,
            "exact_cell_count": 24,
            "route_count": 3,
        })
        self.assertEqual(
            (report["fixture"]["width"], report["fixture"]["height"]),
            (17, 11),
        )
        self.assertEqual(
            report["fixture"]["counts"]["zero_alpha_nonzero_rgb_pixels"], 1
        )
        self.assertEqual(report["parameters"]["lengths"], [1, 2, 50, 300])
        self.assertEqual(report["parameters"]["rotations_raw_fixed"], [0, 1])
        self.assertEqual(report["parameters"]["depths"], ["PF8", "PF16", "PF32"])
        expected_cells = {
            (length, rotation, depth)
            for length in (1, 2, 50, 300)
            for rotation in (0, 1)
            for depth in ("PF8", "PF16", "PF32")
        }
        self.assertEqual(
            {(cell["length"], cell["rotation_raw_fixed"], cell["depth"])
             for cell in report["cells"]},
            expected_cells,
        )
        self.assertEqual(len(report["cells"]), 24)
        for cell in report["cells"]:
            self.assertTrue(cell["routes_exact"])
            self.assertEqual(
                {
                    cell["windows_exported_smart_sha256"],
                    cell["mac_public_classic_sha256"],
                    cell["mac_public_smart_sha256"],
                },
                {cell["windows_exported_smart_sha256"]},
            )
            lifecycle = cell["windows_lifecycle"]
            self.assertEqual(lifecycle["render_mode"], "smart-cpu")
            self.assertEqual(lifecycle["render_error"], 0)
            self.assertTrue(lifecycle["guards_intact"])
            self.assertTrue(lifecycle["cleanup_complete"])
            self.assertTrue(lifecycle["input_png_file_unchanged"])

        scope = report["scope"]
        for key in (
            "actual_windows_aex_exported_smart_via_aexcompat_unicorn",
            "mac_production_source_public_classic",
            "mac_production_source_public_smart",
            "raw_active_bytes_compared_by_sha256",
            "windows_tight_rowbytes_only",
        ):
            self.assertIs(scope[key], True)
        for key in (
            "native_windows_after_effects",
            "native_macos_after_effects",
            "installed_plugin",
            "native_windows_ucrt_or_trigonometry",
            "gpu",
            "install_or_ae_run_performed",
        ):
            self.assertIs(scope[key], False)

        identities = report["identities"]
        worker = identities["aex_guest_worker"]
        self.assertEqual(
            (worker["sha256"], worker["size_bytes"]),
            ("fe376e9ba1d6ee1f20cd9b6954d63542555ed4ffd52a0dfb5e8c95d1f4ccdffe",
             3886128),
        )
        aexcompat = identities["aexcompat"]
        self.assertEqual(
            aexcompat["git_commit"],
            "28d535469f84f67236ef3425afe4291ea2fb0991",
        )
        self.assertTrue(aexcompat["tracked_worktree_clean"])
        build = aexcompat["worker_build"]
        self.assertTrue(build["completed"])
        self.assertEqual(build["command"][-1], "--frozen")
        self.assertEqual(build["target_sha256"], worker["sha256"])
        self.assertEqual(build["target_size_bytes"], worker["size_bytes"])
        self.assertIn("cargo 1.95.0", build["cargo_version"])
        self.assertIn("rustc 1.95.0", build["rustc_version"])

        repository_paths = {row["path"] for row in identities["repository_source"]}
        self.assertEqual(repository_paths, {
            "tools/emulation/test_olmkirakira_mode3_ui_windows_owner_20260821.py",
            "refs/upstream_official/20260619_olm_official_zips/SHA256SUMS.txt",
            "tests/olmkirakira_generic_beta_sanitizer_harness.cpp",
            "tools/emulation/olmkirakira_public_smart_bounded_closure_harness_20260812.cpp",
            "mac/OLMKiraKira/OLMKiraKira.cpp",
            "mac/OLMKiraKira/OLMKiraKira.h",
            "mac/OLMKiraKira/OLMKiraKira_Strings.cpp",
            "mac/OLMKiraKira/OLMKiraKira_Strings.h",
            "core/kirakira_gaussian.h",
            "core/kirakira_highlight.h",
            "core/kirakira_mode4.h",
            "core/kirakira_warp.h",
            "core/kirakira_merge2.h",
        })
        root = ROOT.resolve(strict=True)
        for relative in repository_paths:
            with self.subTest(kirakira_windows_owner_source=relative):
                (ROOT / relative).resolve(strict=True).relative_to(root)
        source_scope = identities["repository_source_scope"]
        for phrase in (
            "excludes symlinked Adobe SDK/Util",
            "Mac system SDK/compiler",
            "standard-library inputs",
        ):
            self.assertIn(phrase, source_scope)

        boundary = report["claim_boundary"]
        for phrase in (
            "Actual Windows OLMKiraKira.aex exported SmartPreRender->SmartRender owner",
            "AEXCompat's Unicorn x86_64 backend",
            "fixed 17x11 fixture",
            "not native Windows or macOS After Effects",
            "native Windows UCRT/trigonometry",
            "Windows padded-rowbytes evidence",
        ):
            self.assertIn(phrase, boundary)
        for phrase in (
            "追加の24-cell Windows-owner証拠",
            "24/24が3経路でexact",
            "独立sidecarに固定",
            "JSON型混同もfail-close",
            "tight rowbytes",
            "Rotation 1のtrigonometry importはhost代替",
            "Adobe SDK／symlinked Util",
        ):
            self.assertIn(phrase, self.doc)

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
        self.assertIn("20/20 HD/UHD cells passed",
                      audit["evidence"]["performance_status"])
        self.assertIn("execution_pre_and_post exact source/toolchain binding",
                      audit["evidence"]["performance_status"])
        self.assertIn("9 Front/Back/Dual cases/geometry",
                      audit["evidence"]["performance_status"])
        self.assertIn("15 cases/geometry including Mode 3 Horizontal Length 300 Rotation 1",
                      audit["evidence"]["performance_status"])
        self.assertIn("HD 38.19 seconds / peak 503742464 bytes",
                      audit["evidence"]["performance_status"])
        self.assertIn("UHD 141.89 seconds / peak 1470169088 bytes",
                      audit["evidence"]["performance_status"])
        directional_audit = next(
            row for row in audit["plugins"] if row["plugin"] == "OLMDirectionalBlur"
        )
        self.assertEqual(directional_audit["geometry_rowbytes"], "proven")
        for axis in ("parameters", "windows", "ae_host", "roi"):
            self.assertEqual(directional_audit[axis], "partial")
        kirakira_audit = next(
            row for row in audit["plugins"] if row["plugin"] == "OLMKiraKira"
        )
        self.assertEqual(kirakira_audit["geometry_rowbytes"], "proven")
        self.assertEqual(kirakira_audit["depth_route"], "proven")
        for axis in ("parameters", "windows", "ae_host"):
            self.assertEqual(kirakira_audit[axis], "partial")
        self.assertEqual(kirakira_audit["roi"], "missing")
        self.assertEqual(
            audit["evidence"]["kirakira_mode3_ui_hostless"],
            "tests/test_olmkirakira_mode3_ui_length_beta_20260821.py",
        )
        self.assertEqual(
            audit["evidence"]["kirakira_mode3_windows_helper_chain"],
            "refs/conformance/olmkirakira_mode3_geometry_generalization_actual_aex_20260810.json",
        )
        for phrase in (
            "Horizontal-only Mode 3 Length 1..300",
            "Rotation 0/1",
            "PF8/PF16/PF32 Classic and Smart",
            "1 GiB per-render plugin-owned",
            "12 billion work-unit caps",
            "partial ROI/tile",
        ):
            self.assertIn(phrase, audit["evidence"]["kirakira_mode3_ui_scope"])
        for phrase in (
            "66 cases and 497250 words exact",
            "the 14 sampled Lengths {1,2,3,5,7,9,11,25,50,100,200,300,301,1000}",
            "angles {-45,0,17,45}",
            "60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7",
            "the earlier exported public EffectMain all-depth report is Length-50-only",
            "separate pinned exported Smart-owner differential covers only the explicitly documented 24 cells",
            "not broad Length 1..300 exported-owner or native AE equality",
        ):
            self.assertIn(phrase, audit["evidence"]["kirakira_mode3_windows_exact_scope"])
        self.assertEqual(
            audit["evidence"]["kirakira_mode3_windows_owner_report"],
            "refs/conformance/olmkirakira_mode3_ui_windows_owner_20260821.json",
        )
        self.assertEqual(
            audit["evidence"]["kirakira_mode3_windows_owner_digest"],
            "refs/conformance/olmkirakira_mode3_ui_windows_owner_20260821.sha256: "
            "50bbf05233f985608e4e320473970e734987d60ffd9e1d859c63bd10b1d8f687",
        )
        self.assertEqual(
            KIRAKIRA_MODE3_WINDOWS_OWNER_DIGEST.read_text(encoding="ascii"),
            "50bbf05233f985608e4e320473970e734987d60ffd9e1d859c63bd10b1d8f687\n",
        )
        self.assertEqual(
            audit["evidence"]["kirakira_mode3_windows_owner_test"],
            "tests/test_olmkirakira_mode3_ui_windows_owner_20260821.py",
        )
        self.assertEqual(
            audit["evidence"]["kirakira_mode3_windows_owner_verifier"],
            "tools/emulation/test_olmkirakira_mode3_ui_windows_owner_20260821.py",
        )
        owner_scope = audit["evidence"]["kirakira_mode3_windows_owner_scope"]
        for phrase in (
            "raw active bytes exact 24/24 only",
            "fixed mixed-alpha 17x11 source containing zero-alpha/nonzero-RGB",
            "Lengths {1,2,50,300}",
            "owner raw-fixed Rotations {0,1}",
            "PF8/PF16/PF32",
            "commit 28d535469f84f67236ef3425afe4291ea2fb0991 exact-checkout target",
            "cargo --frozen",
            "cargo/rustc 1.95",
            "fe376e9ba1d6ee1f20cd9b6954d63542555ed4ffd52a0dfb5e8c95d1f4ccdffe",
            "tight Windows rowbytes only",
            "Rotation 1 trigonometry is host-substituted",
            "not all Length 1..300",
            "Windows padded rowbytes or Classic",
            "native Windows/macOS After Effects",
            "native Windows UCRT/trigonometry",
            "helper-chain generalization",
            "Adobe SDK/symlinked Util",
        ):
            self.assertIn(phrase, owner_scope)
        self.assertIn(
            "older fixture-only source/extent/stride rejection claims are superseded",
            audit["evidence"]["kirakira_mode3_fixed32_supersession"],
        )
        self.assertEqual(
            audit["evidence"]["directional_neutral_hostless"],
            [
                "tools/emulation/test_dblur_generic_backonly_beta_20260821.py",
                "tools/emulation/test_dblur_generic_backonly_effectmain_20260821.py",
            ],
        )
        self.assertIn(
            "Front-only, Back-only, or Dual",
            audit["evidence"]["directional_neutral_scope"],
        )
        self.assertEqual(
            audit["evidence"]["directional_back_actual_aex_anchor"],
            "refs/conformance/dblur_mode1_backonly_portable_20260805.json",
        )
        exact_scope = audit["evidence"]["directional_back_windows_exact_scope"]
        for phrase in (
            "actual-AEX raw-callback anchors",
            "PF8 960x540 Back 240 Angle 0 Gain 1 scale 0.5",
            "fixed 16x16 PF8 Back 8 Angle 0/45 Gain 1",
            "PF16 Back 1/2/8 Angle 45 Gain 1",
            "PF16 Dual Front 1/2/8 plus Back 1 Angle 45 Gain 1",
            "PF32 Back 1 Angle 0/45 Gain 0.5/1",
            "Back 8 Angle 45 Gain 1",
            "not native AE saved-frame",
            "not generic Dual Windows exact",
            "not general geometry",
            "not all strength combinations",
            "not the ROI v2 package",
        ):
            self.assertIn(phrase, exact_scope)
        self.assertEqual(audit["evidence"]["native_ae_current_roi"],
                         "partial / quick 10/10 passed")
        current_roi_scope = audit["evidence"]["native_ae_current_roi_scope"]
        for phrase in (audit["evidence"]["current_roi_package_sha256"],
                       "full-frame 1920x1080", "all selected cases 8 bpc",
                       "one selected tuple per plugin", "excludes the 54-case matrix",
                       "partial ROI/tile parity", "later source/document changes"):
            self.assertIn(phrase, current_roi_scope)
        package_report = json.loads(
            (ROOT / audit["evidence"]["current_roi_package_report"]).read_text()
        )
        self.assertEqual(package_report["schema"], "olm.public-beta-package/1")
        self.assertEqual(package_report["artifact_sha256"],
                         audit["evidence"]["current_roi_package_sha256"])
        self.assertEqual(package_report["generic_beta_gate"]["status"], "PASS")
        self.assertEqual(package_report["native_ae"]["current_roi_package"],
                         "partial / quick 10/10 passed")
        self.assertEqual(package_report["native_ae"]["current_roi_package_evidence"],
                         audit["evidence"]["native_ae_current_roi_evidence"])
        self.assertIn("embedded in this immutable package", package_report["beta_support_scope"])
        self.assertIn("not the 54-case matrix", package_report["claim_boundary"])
        self.assertIn("does not prove all depths/routes/parameters, partial ROI/tile parity",
                      package_report["claim_boundary"])
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
        hd = json.loads((ROOT / audit["evidence"]["windows_hd_checkpoint"]).read_text())
        self.assertEqual(hd["schema"], "generic-beta-aexcompat-hd-checkpoint/1")
        self.assertEqual(hd["status"], "PARTIAL_COMPLETE_5_OF_7")
        self.assertEqual(len(hd["completed_cases"]), 5)
        self.assertEqual(len(hd["pending_cases"]), 2)
        self.assertTrue(all(row["status"] == "ok" and row["render_error"] == 0
                            for row in hd["completed_cases"]))
        self.assertTrue(all(re.fullmatch(r"[0-9a-f]{64}", row["input_sha256"])
                            and re.fullmatch(r"[0-9a-f]{64}", row["output_sha256"])
                            for row in hd["completed_cases"]))
        self.assertEqual(set(hd["aex_sha256"]), {"ColorKeep", "OLMColorKey", "OLMToonDilate"})
        self.assertTrue(all(re.fullmatch(r"[0-9a-f]{64}", value)
                            for value in hd["aex_sha256"].values()))
        self.assertRegex(hd["execution"]["runner_sha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(hd["execution"]["worker_sha256"], r"^[0-9a-f]{64}$")
        self.assertFalse(hd["execution"]["process_residue_after_runs"])
        self.assertEqual({row["id"] for row in hd["pending_cases"]}, {
            "OLMToonDilate_hd_random_radius_2_01", "OLMToonDilate_hd_random_radius_5"
        })
        self.assertTrue(all("not executed" in row["reason"] and
                            "campaign time budget" in row["reason"] and
                            "runtime is unknown" in row["reason"] and
                            "281.765s" in row["reason"] and "300s" in row["reason"]
                            for row in hd["pending_cases"]))
        self.assertEqual(audit["criteria"]["windows_grounding"], "partial")
        for key in ("capability_contract", "hostless_gate", "performance", "native_ae_pre_roi",
                    "native_ae_current_roi_evidence",
                    "windows_nonhd_roi_checkpoint", "windows_hd_checkpoint",
                    "current_roi_package_report", "kirakira_mode3_ui_hostless",
                    "kirakira_mode3_windows_helper_chain",
                    "kirakira_mode3_windows_owner_report",
                    "kirakira_mode3_windows_owner_test",
                    "kirakira_mode3_windows_owner_verifier"):
            evidence = audit["evidence"][key]
            self.assertTrue((ROOT / evidence).is_file(), evidence)
        for claim in ("ROI／tile／halo", "full-frame出力", "必要halo", "非ゼロorigin",
                      "ROI外の出力とpadding", "ASan／UBSan clean", "tile render",
                      "finite-halo tile", "partial storage", "content bound", "14/14", "5/7",
                      "所要時間は未計測", "native Windows／After Effects実行ではありません"):
            self.assertIn(claim, self.doc)
        self.assertIn("immutable ROI v2 package", self.doc)
        self.assertNotIn("現在のgeneric buildはnative AE quick smoke", self.doc)


if __name__ == "__main__":
    unittest.main()
