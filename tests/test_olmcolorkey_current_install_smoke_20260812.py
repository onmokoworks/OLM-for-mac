import copy
import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "refs/conformance/olmcolorkey_current_install_smoke_20260812.json"
RAW = ROOT / "refs/conformance/olmcolorkey_current_install_smoke_raw_20260812.json"
CLOSURE = ROOT / "refs/conformance/olmcolorkey_lab76_multikey_order_closure_20260812.json"
SOURCE = ROOT / "mac/OLMColorKey/OLMColorKey.cpp"
RUNNER = ROOT / "scripts/run_olmcolorkey_current_install_smoke_20260812.py"
INSTALLED = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMColorKey.plugin/Contents/MacOS/OLMColorKey"
BACKUP = Path("/tmp/olmcolorkey-lab76-backup.becrne/OLMColorKey.plugin/Contents/MacOS/OLMColorKey")
SOURCE_SHA = "41595dc9ab1054324fa113357f39480073a8ac54e065d1cbf0462028a01e66c8"
INSTALLED_SHA = "350ed6eb00c078952ad512b621e3489e6e6ed47d9129e3c11748f547fc441230"
PREVIOUS_SHA = "7d329f614561705a7e74f38b91baa99bc7c47eb4b4d78542b6b25cd4229bf92c"
RAW_SHA = "92addd3f2aa9a3af246749b3cd86f2a2854e8738c66608db4f72333b8729a8aa"
RUNNER_SHA = "82e32dc8bc971049eb052af82df650459eebb8554fa7f405312ab871dac73eb8"
CLOSURE_SHA = "4cb2de69e19e705a5ae07de573386dc8fed9b4087b2838be903a2c9c905461e3"
OUTPUT_SHA = "7bf128f1809160aca2d8d5f6c3f6f67ca3e6c6558c78c83f844f010923ffe855"
INSTALLED_PATH = str(INSTALLED)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validates(summary: dict, raw: dict) -> bool:
    try:
        returned = raw["execution"]["ae_return"]
        effect = returned["effect"]
        project = returned["project"]
        outputs = returned["outputs"]
        fresh = raw["fresh_host"]
        host = summary["host_smoke"]
        pid = host["ae_pid"]
        return all((
            summary["schema_version"] == 1,
            summary["kind"] == "olmcolorkey_current_install_smoke",
            summary["status"] == "installed_host_smoke_pass_no_pixel_promotion",
            summary["date"] == "2026-08-12",
            summary["build"]["production_source_path"] == "mac/OLMColorKey/OLMColorKey.cpp",
            summary["build"]["production_source_sha256"] == SOURCE_SHA,
            sha256(SOURCE) == SOURCE_SHA,
            summary["build"]["configuration"] == "Debug",
            summary["build"]["architectures"] == ["x86_64", "arm64"],
            summary["build"]["codesign"] == "adhoc",
            summary["build"]["codesign_deep_strict"] is True,
            summary["installed_bundle"]["path"] == "~/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMColorKey.plugin",
            summary["installed_bundle"]["binary_path"] == "~/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMColorKey.plugin/Contents/MacOS/OLMColorKey",
            summary["installed_bundle"]["binary_sha256"] == INSTALLED_SHA,
            summary["installed_bundle"]["matching_bundle_count"] == 1,
            summary["installed_bundle"]["previous_binary_sha256"] == PREVIOUS_SHA,
            summary["installed_bundle"]["recoverable_backup"] == "/tmp/olmcolorkey-lab76-backup.becrne/OLMColorKey.plugin",
            sha256(INSTALLED) == INSTALLED_SHA,
            sha256(BACKUP) == PREVIOUS_SHA,
            host["raw_report"] == {
                "path": "refs/conformance/olmcolorkey_current_install_smoke_raw_20260812.json",
                "sha256": RAW_SHA,
            },
            sha256(RAW) == RAW_SHA,
            host["runner"] == {
                "path": "scripts/run_olmcolorkey_current_install_smoke_20260812.py",
                "sha256": RUNNER_SHA,
            },
            sha256(RUNNER) == RUNNER_SHA,
            raw["schema_version"] == 1,
            raw["kind"] == "olmcolorkey_current_install_ae_smoke_raw",
            raw["status"] == "installed_host_smoke_pass",
            raw["claim_boundary"] == "Fresh AE installed-path load, effect add, default-parameter PF32 Software render only; no Lab76 two-key live-host pixel-exact claim.",
            raw["installed_plugin"]["bundle_path"] == str(INSTALLED.parent.parent.parent),
            raw["installed_plugin"]["binary_path"] == INSTALLED_PATH,
            raw["installed_plugin"]["expected_binary_sha256"] == INSTALLED_SHA,
            raw["installed_plugin"]["binary_sha256_pre"] == INSTALLED_SHA,
            raw["installed_plugin"]["binary_sha256_post"] == INSTALLED_SHA,
            raw["installed_plugin"]["matching_bundle_paths"] == [str(INSTALLED.parent.parent.parent)],
            raw["application"] == {
                "path": "/Applications/Adobe After Effects 2026/Adobe After Effects 2026.app",
                "plist_build": "26.3.0.87",
                "plist_short_version": "26.3.0",
            },
            raw["execution"]["osascript"] == {"returncode": 0, "stderr": "", "stdout": "0\n"},
            raw["execution"]["host_trace"] == "LOADER_ENTER\nLOADER_RETURN\n",
            json.loads(raw["execution"]["ae_return_text"]) == returned,
            returned["status"] == "ok" and returned["ae_version"] == "26.3x87",
            project == {
                "bits_per_channel": 32,
                "dimensions": [64, 36],
                "linear_blending": False,
                "renderer": "SOFTWARE",
                "renderer_raw": 1816,
                "working_space": "None",
            },
            returned["source"] == {"kind": "AE solid", "rgba8": [26, 191, 204, 255]},
            effect["name"] == effect["match_name"] == "OLM Color Key",
            effect["parameter_count"] == 217,
            len(effect["parameters_before"]) == len(effect["parameters_after"]) == 217,
            effect["parameters_before"] == effect["parameters_after"],
            effect["parameters_unchanged"] is True,
            outputs["control"]["sha256"] == outputs["effect_on"]["sha256"] == OUTPUT_SHA,
            fresh["initial_ae_pids"] == [],
            fresh["ae_pids_pre_render"] == fresh["ae_pids_post_render"] == [pid],
            fresh["loaded_modules_pre_render"] == {str(pid): []},
            fresh["loaded_modules_post_render"] == {str(pid): [INSTALLED_PATH]},
            fresh["agent_started_ae"] is True and fresh["agent_quit_ae"] is True,
            fresh["open"] == {"returncode": 0, "stderr": "", "stdout": ""},
            fresh["quit"] == {"returncode": 0, "stderr": "", "stdout": ""},
            raw["gates"] == {
                "effect_add_and_render_completed": True,
                "fresh_process": True,
                "installed_hash_unchanged": True,
                "lab76_live_pixel_exact_claim": False,
                "loaded_module_identity_exact_after_effect_add": True,
            },
            host["application"] == "Adobe After Effects 2026",
            host["ae_version"] == "26.3x87",
            host["fresh_process"] is True,
            host["renderer"] == "SOFTWARE" and host["renderer_raw"] == 1816,
            host["depth"] == "PF32" and host["dimensions"] == [64, 36],
            host["working_space"] == "None" and host["linear_blending"] is False,
            host["source"] == {"kind": "AE solid", "rgba8": [26, 191, 204, 255]},
            host["effect_name"] == host["effect_match_name"] == "OLM Color Key",
            host["default_parameter_count"] == 217 and host["parameters_unchanged"] is True,
            host["loaded_module_path"] == INSTALLED_PATH,
            host["loaded_module_count_after_effect_add"] == 1,
            host["loaded_module_identity_semantics"] == "the fresh process had no OLMColorKey mapping before addProperty; after effect add and both renders, lsof reported exactly the installed path, whose bytes were SHA-bound before launch and after render",
            host["control_exr_sha256"] == OUTPUT_SHA,
            host["effect_on_exr_sha256"] == OUTPUT_SHA,
            host["default_noop_equal"] is True,
            host["render_outputs_created"] is True,
            host["loaded_module_identity_exact"] is True,
            host["ae_quit_after_smoke"] is True,
            sha256(CLOSURE) == CLOSURE_SHA,
            summary["hostless_lab76_multikey_closure"]["path"] == "refs/conformance/olmcolorkey_lab76_multikey_order_closure_20260812.json",
            summary["hostless_lab76_multikey_closure"]["sha256"] == CLOSURE_SHA,
            summary["hostless_lab76_multikey_closure"]["status"] == "raw_exact",
            summary["hostless_lab76_multikey_closure"]["relation_to_installed_build"] == "the closure and installed smoke bind the same current production source SHA-256; the closure owns the bounded Lab76 two-key pixel claim, while this AE run owns installed load/add/default-noop-render only",
            json.loads(CLOSURE.read_text())["status"] == "raw_exact",
            summary["claims_not_made"] == [
                "No live-AE Lab76 two-key pixel-exact claim",
                "No Windows/Mac AE pixel-exact claim from the equal control/default-noop output hashes",
                "No arbitrary ColorKey parameter, source, geometry, depth, renderer, GPU, or host promotion",
                "No claim that an unloaded pre-addProperty mapping exists; OLMColorKey was observed as a lazy-loaded exact installed mapping after effect add",
            ],
        ))
    except (KeyError, IndexError, TypeError, OSError, json.JSONDecodeError):
        return False


class ColorKeyCurrentInstallSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary = json.loads(SUMMARY.read_text())
        cls.raw = json.loads(RAW.read_text())

    def test_summary_raw_closure_and_installed_identity_are_bound(self):
        self.assertTrue(validates(self.summary, self.raw))

    def test_identity_host_result_and_claim_tampering_fails_closed(self):
        mutations = (
            lambda s, r: s["build"].update(production_source_sha256="0" * 64),
            lambda s, r: s["installed_bundle"].update(binary_sha256="0" * 64),
            lambda s, r: s["installed_bundle"].update(matching_bundle_count=2),
            lambda s, r: s["host_smoke"]["raw_report"].update(sha256="0" * 64),
            lambda s, r: s["host_smoke"]["runner"].update(sha256="0" * 64),
            lambda s, r: s["hostless_lab76_multikey_closure"].update(sha256="0" * 64),
            lambda s, r: r["installed_plugin"].update(binary_sha256_post="0" * 64),
            lambda s, r: r["installed_plugin"].update(expected_binary_sha256="0" * 64),
            lambda s, r: r["installed_plugin"].update(bundle_path="/tmp/fake.plugin"),
            lambda s, r: r["fresh_host"].update(initial_ae_pids=[1]),
            lambda s, r: r["fresh_host"]["loaded_modules_post_render"].update({str(s["host_smoke"]["ae_pid"]): []}),
            lambda s, r: r["fresh_host"].update(agent_quit_ae=False),
            lambda s, r: r["execution"]["ae_return"].update(ae_version="26.4x1"),
            lambda s, r: r["execution"].update(host_trace="LOADER_ENTER\nLOADER_FAIL\n"),
            lambda s, r: r["execution"]["osascript"].update(returncode=1),
            lambda s, r: r["execution"]["ae_return"]["project"].update(bits_per_channel=16),
            lambda s, r: r["execution"]["ae_return"]["effect"].update(parameters_unchanged=False),
            lambda s, r: r["execution"]["ae_return"]["effect"]["parameters_after"][0].update(value=1),
            lambda s, r: r["execution"]["ae_return"]["outputs"]["effect_on"].update(sha256="0" * 64),
            lambda s, r: r["gates"].update(lab76_live_pixel_exact_claim=True),
            lambda s, r: s["host_smoke"].update(depth="PF16"),
            lambda s, r: s["host_smoke"].update(default_noop_equal=False),
            lambda s, r: s["host_smoke"].update(loaded_module_identity_semantics="overclaim"),
            lambda s, r: s["hostless_lab76_multikey_closure"].update(relation_to_installed_build="overclaim"),
            lambda s, r: s["claims_not_made"].remove("No live-AE Lab76 two-key pixel-exact claim"),
        )
        results = []
        for mutate in mutations:
            summary, raw = copy.deepcopy(self.summary), copy.deepcopy(self.raw)
            mutate(summary, raw)
            results.append(validates(summary, raw))
        self.assertEqual(results, [False] * len(mutations))


if __name__ == "__main__":
    unittest.main()
