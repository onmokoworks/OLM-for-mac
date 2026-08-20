import importlib.util
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = ROOT / "scripts/run_ae_generalization_smoke.py"
SOURCE = ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp"
HARNESS = ROOT / "tests/olmkirakira_generic_beta_sanitizer_harness.cpp"
BASE_HARNESS = ROOT / "tools/emulation/olmkirakira_public_smart_bounded_closure_harness_20260812.cpp"


def load_campaign():
    spec = importlib.util.spec_from_file_location("generalization_smoke", CAMPAIGN)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class KiraKiraNativeSmokeTupleTests(unittest.TestCase):
    def test_ui_defaults_are_not_a_declared_generic_tuple(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        setup = source[source.index("static PF_Err ParamsSetup"):
                       source.index("static PF_Err Render(")]
        self.assertIn("StrID_BlurMode_Param_Name), 3, 2", setup)
        self.assertIn("StrID_MergeMode_Param_Name), 2, 1", setup)
        self.assertEqual(setup.count("0, 300, 50"), 4)
        self.assertIn("StrID_HighlightRadius_Param_Name), 0, 500, 0, 500, 0", setup)
        admission = source[source.index("const bool mode2_horizontal"):
                           source.index("const bool mode3_horizontal")]
        self.assertNotIn("vertical_length == 50", admission)
        self.assertNotIn("diagonal_length == 50", admission)

    def test_campaign_uses_the_closed_mode2_highlight_tuple(self) -> None:
        spec = load_campaign().PLUGINS["kirakira"]
        self.assertEqual(spec["tuple"], "closed Mode 2 Highlight radius 3 tuple")
        self.assertEqual(
            {match: value for match, _name, value in spec["params"]},
            {
                "OLM OLM Kira Kira-0003": 0,
                "OLM OLM Kira Kira-0004": 0,
                "OLM OLM Kira Kira-0005": 0,
                "OLM OLM Kira Kira-0026": 0,
                "OLM OLM Kira Kira-0006": 3,
            },
        )

    def test_campaign_can_forward_diagnostic_environment(self) -> None:
        source = CAMPAIGN.read_text(encoding="utf-8")
        self.assertIn('parser.add_argument("--ae-env", action="append"', source)
        self.assertIn('command.extend(("--ae-env", value))', source)

    def test_production_admission_retains_the_same_tuple(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        start = source.index("const bool mode2_highlight")
        end = source.index("const bool mode3_horizontal", start)
        body = source[start:end]
        for condition in (
            "info.blur_mode == 2", "info.merge_mode == 1",
            "info.brightness_gain == 1.0", "info.glow_rotation == 0.0",
            "info.horizontal_length == 0", "info.diagonal2_length == 0",
            "info.highlight_radius == 3", "!info.highlight_use_ramp",
        ):
            self.assertIn(condition, body)

    def test_hostless_matrix_executes_mode2_highlight_at_all_depths(self) -> None:
        harness = HARNESS.read_text(encoding="utf-8")
        tuples = BASE_HARNESS.read_text(encoding="utf-8")
        self.assertIn('{"m2_highlight_r3", 2, 1, 0, 1, 0, 0, 3', tuples)
        self.assertIn("run_depth<PF_Pixel8>", harness)
        self.assertIn("run_depth<PF_Pixel16>", harness)
        self.assertIn("run_depth<PF_PixelFloat>", harness)

    def test_closed_smoke_tuple_renders_hd_at_all_depths(self) -> None:
        sdk = subprocess.check_output(["xcrun", "--show-sdk-path"], text=True).strip()
        source = str(SOURCE)
        with tempfile.TemporaryDirectory(prefix="kira_native_smoke_tuple_") as raw:
            executable = Path(raw) / "driver"
            build = subprocess.run([
                "clang++", "-std=c++20", "-O2", "-DNDEBUG", "-w",
                "-fno-fast-math", "-ffp-contract=off", "-isysroot", sdk,
                "-I", str(ROOT / "Headers"), "-I", str(ROOT / "Headers/SP"),
                "-I", str(ROOT / "Util"), "-I", str(ROOT / "Resources"),
                f'-DKIRA_SOURCE="{source}"', str(HARNESS),
                str(ROOT / "Util/AEGP_SuiteHandler.cpp"),
                str(ROOT / "Util/MissingSuiteError.cpp"),
                "-framework", "Cocoa", "-o", str(executable),
            ], cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(build.returncode, 0, build.stderr[-8000:])
            diagnostic = Path(raw) / "diagnostic.log"
            for depth in (8, 16, 32):
                environment = os.environ.copy()
                if depth == 8:
                    environment["OLMKIRAKIRA_DIAGNOSTIC_LOG"] = str(diagnostic)
                run = subprocess.run(
                    [str(executable), "--single", "6", str(depth), "1920", "1080"],
                    cwd=ROOT, text=True, capture_output=True, timeout=60,
                    env=environment,
                )
                self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
                self.assertIn("tuple=m2_highlight_r3", run.stdout)
                self.assertIn(f"depth={depth}", run.stdout)
                self.assertIn("ok=1", run.stdout)
            log = diagnostic.read_text(encoding="utf-8")
            self.assertIn("pre success dimensions=1920x1080", log)
            self.assertIn("smart validate_world error=0", log)
            self.assertIn("smart admission", log)
            self.assertIn("generic=1", log)
            self.assertIn("smart render_world error=0", log)

            overscan = subprocess.run(
                [str(executable), "--overscan"], cwd=ROOT, text=True,
                capture_output=True, timeout=60,
            )
            self.assertEqual(overscan.returncode, 0, overscan.stdout + overscan.stderr)
            self.assertIn("size=1920x1080 ok=1", overscan.stdout)

            partial = subprocess.run(
                [str(executable), "--partial-guard"], cwd=ROOT, text=True,
                capture_output=True, timeout=10,
            )
            self.assertEqual(partial.returncode, 0, partial.stdout + partial.stderr)
            self.assertIn(
                "REQUEST_GUARD partial=1 non_unity_downsample=0 ok=1 callbacks=0",
                partial.stdout,
            )

            downsample = subprocess.run(
                [str(executable), "--downsample-guard"], cwd=ROOT, text=True,
                capture_output=True, timeout=10,
            )
            self.assertEqual(
                downsample.returncode, 0, downsample.stdout + downsample.stderr
            )
            self.assertIn(
                "REQUEST_GUARD partial=0 non_unity_downsample=1 ok=1 callbacks=0",
                downsample.stdout,
            )


if __name__ == "__main__":
    unittest.main()
