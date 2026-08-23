import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("campaign", ROOT / "scripts/run_ae_generalization_smoke.py")
assert SPEC and SPEC.loader
campaign = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(campaign)


class AEGeneralizationSmokeTests(unittest.TestCase):
    def test_prepares_generic_request_accepted_by_single_case_schema(self) -> None:
        state = {"key": "toon", "binary": "OLMToonDilate",
                 "effect_match_name": "ADBE OLMToonDilate", "effect_name": "OLM Toon Dilate",
                 "execution_route": "Smart", "supported_tuple": "default", "params": ()}
        with tempfile.TemporaryDirectory() as raw:
            request, case_id = campaign.prepare_request(Path(raw), state, 16, 31, 17, "odd")
            self.assertTrue((request / "input" / f"{case_id}_before_effects.png").is_file())
            manifest = __import__("json").loads((request / "request_manifest.json").read_text())
            reference = __import__("json").loads((request / "reference_manifest.json").read_text())
            self.assertEqual(manifest["cases"][0]["id"], case_id)
            self.assertEqual(reference["project"]["bits_per_channel"], 16)
            self.assertEqual(reference["comp"]["width"], 31)

    def test_plugin_probe_is_read_only_and_complete(self) -> None:
        state = campaign.plugin_state("colorkey")
        self.assertIn("installed_sha256", state)
        self.assertEqual([row["config"] for row in state["local_candidates"]], ["Debug", "Release"])

    def test_host_probe_targets_only_the_main_ae_executable(self) -> None:
        source = (ROOT / "scripts/run_ae_generalization_smoke.py").read_text()
        self.assertIn('f"^{executable_path}$"', source)
        self.assertNotIn('["pgrep", "-f", "Adobe After Effects"]', source)

    def test_all_ten_pipl_match_names_and_declared_depths_are_encoded(self) -> None:
        self.assertEqual(len(campaign.PLUGINS), 10)
        self.assertEqual(campaign.PLUGINS["toon"]["match"], "ADBE OLMToonDilate")
        self.assertEqual(campaign.PLUGINS["blur"]["match"], "OLM OLM Blur")
        self.assertEqual(campaign.PLUGINS["directional"]["depths"], (8,))
        self.assertEqual(campaign.PLUGINS["smoother"]["depths"], (8, 16))
        self.assertEqual(campaign.PLUGINS["smoother"]["route"], "Smart")

    def test_directional_dual_profile_is_separate_from_baseline_matrix(self) -> None:
        baseline = campaign.plugin_state("directional")
        profiled = campaign.plugin_state("directional")
        campaign.apply_parameter_profile(profiled, "directional-dual")
        self.assertEqual(baseline["declared_depths"], (8,))
        self.assertEqual(profiled["declared_depths"], (8, 16, 32))
        params = {match: value for match, _name, value in profiled["params"]}
        self.assertEqual(params["OLM Directional Blur-0001"], 37.25)
        self.assertEqual(params["OLM Directional Blur-0002"], 0.75)
        self.assertEqual(params["OLM Directional Blur-0005"], 2)
        self.assertEqual(params["OLM Directional Blur-0010"], 2)
        self.assertEqual(campaign.PLUGINS["directional"]["depths"], (8,))

    def test_colorkeep_count100_profile_reaches_last_palette_entry(self) -> None:
        baseline = campaign.plugin_state("colorkeep")
        profiled = campaign.plugin_state("colorkeep")
        campaign.apply_parameter_profile(profiled, "colorkeep-count100")
        params = {match: value for match, _name, value in profiled["params"]}
        self.assertEqual(params["OLM Color Keep-0001"], 100)
        self.assertEqual(params["OLM Color Keep-0101"], [17 / 255, 5 / 255, 1 / 255])
        self.assertEqual(profiled["declared_depths"], (8, 16, 32))
        self.assertEqual(baseline["params"], ())
        self.assertEqual(campaign.PLUGINS["colorkeep"].get("params", ()), ())

    def test_blur_legacy_repeat10_profile_is_separate_from_baseline(self) -> None:
        baseline = campaign.plugin_state("blur")
        profiled = campaign.plugin_state("blur")
        campaign.apply_parameter_profile(profiled, "blur-legacy-repeat10")
        params = {match: value for match, _name, value in profiled["params"]}
        self.assertEqual(params, {
            "OLM OLM Blur-0005": 5,
            "OLM OLM Blur-0006": 100,
            "OLM OLM Blur-0003": 10,
            "OLM OLM Blur-0004": 1,
            "OLM OLM Blur-0007": 1,
        })
        self.assertEqual(profiled["declared_depths"], (8, 16, 32))
        self.assertEqual(baseline["params"], ())
        self.assertEqual(campaign.PLUGINS["blur"].get("params", ()), ())

    def run_preflight(self, profile: str, plugins: tuple[str, ...] = ()) -> dict:
        with tempfile.TemporaryDirectory() as raw:
            plugin_args = [item for plugin in plugins for item in ("--plugin", plugin)]
            completed = subprocess.run(
                [sys.executable, str(ROOT / "scripts/run_ae_generalization_smoke.py"),
                 "--profile", profile, "--output-dir", raw, *plugin_args],
                check=True, text=True, capture_output=True,
            )
            self.assertNotIn("AE single case status", completed.stdout)
            return json.loads((Path(raw) / "campaign_result.json").read_text())

    def test_quick_profile_is_one_first_declared_depth_hd_case_per_plugin(self) -> None:
        report = self.run_preflight("quick")
        self.assertEqual(report["profile"], "quick")
        self.assertEqual(len(report["matrix"]), 10)
        self.assertEqual({row["plugin"] for row in report["matrix"]},
                         {spec["binary"] for spec in campaign.PLUGINS.values()})
        self.assertTrue(all((row["width"], row["height"], row["status"]) ==
                            (1920, 1080, "planned") for row in report["matrix"]))
        first_depth = {spec["binary"]: spec["depths"][0] for spec in campaign.PLUGINS.values()}
        self.assertTrue(all(row["depth"] == first_depth[row["plugin"]]
                            for row in report["matrix"]))

    def test_full_profile_retains_declared_54_case_matrix(self) -> None:
        report = self.run_preflight("full")
        self.assertEqual(report["profile"], "full")
        self.assertEqual(len(report["matrix"]), 54)
        expected = {
            (spec["binary"], depth, width, height)
            for spec in campaign.PLUGINS.values()
            for depth in spec["depths"]
            for width, height, _ in campaign.SIZES
        }
        actual = {(row["plugin"], row["depth"], row["width"], row["height"])
                  for row in report["matrix"]}
        self.assertEqual(actual, expected)
        self.assertTrue(all(
            (row["output_mode"], row["output_template"]) ==
            (("png_render_queue", campaign.PNG16_TEMPLATE)
             if row["depth"] == 8 and row["plugin"] == "OLMDirectionalBlur" else
             ("png", "") if row["depth"] == 8 else
             ("png16_render_queue", campaign.PNG16_TEMPLATE) if row["depth"] == 16 else
             ("exr_render_queue", campaign.EXR_TEMPLATE))
            for row in report["matrix"]
        ))
        self.assertTrue(report["unsupported_routes"])
        directional = [row for row in report["matrix"]
                       if row["plugin"] == "OLMDirectionalBlur"]
        strengths = {
            (row["width"], row["height"]): row["parameter_overrides"][0]["value"]
            for row in directional
        }
        self.assertEqual(strengths, {(1920, 1080): 48, (3840, 2160): 8})

    def test_two_plugin_retry_filter_and_parameter_evidence(self) -> None:
        report = self.run_preflight("quick", ("kirakira", "smoother2"))
        self.assertEqual(report["selected_plugin_keys"], ["kirakira", "smoother2"])
        self.assertEqual([row["plugin"] for row in report["matrix"]],
                         ["OLMKiraKira", "OLMSmoother2"])
        by_plugin = {row["plugin"]: row for row in report["matrix"]}
        kira = {row["match_name"]: row["value"]
                for row in by_plugin["OLMKiraKira"]["parameter_overrides"]}
        self.assertEqual(kira["OLM OLM Kira Kira-0003"], 0)
        self.assertEqual(kira["OLM OLM Kira Kira-0006"], 3)
        smoother = {row["match_name"]: row["value"]
                    for row in by_plugin["OLMSmoother2"]["parameter_overrides"]}
        self.assertEqual(smoother["OLM Smoother v2-0006"], 2)
        self.assertEqual(smoother["OLM Smoother v2-0007"], 1)
        self.assertEqual(smoother["OLM Smoother v2-0008"], 2.4)
        jsx = (ROOT / "scripts/ae_render_single_case.jsx").read_text()
        self.assertIn('" actual=" + valueToLog(coerceValue(prop.value))', jsx)


if __name__ == "__main__":
    unittest.main()
