import copy
import hashlib
import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "refs/conformance/olmblur_classic_current_install_smoke_20260812.json"
RAW = ROOT / "refs/conformance/olmblur_classic_current_install_smoke_raw_20260812.json"
SOURCE = ROOT / "mac/OLMBlur/OLMBlur.cpp"
RUNNER = ROOT / "scripts/run_olmblur_classic_current_install_smoke_20260812.py"
OBS = ROOT / "refs/conformance/olmblur_classic_current_install_smoke_observed_raw_20260812.json"
OBS_RUNNER = ROOT / "scripts/run_olmblur_classic_current_install_smoke_observed_20260812.py"
SANITIZER = ROOT / "scripts/sanitize_olmblur_classic_current_install_smoke_20260812.py"
CLOSURE = ROOT / "refs/conformance/olmblur_classic_public_entry_closure_20260812.json"
HANDOFF = ROOT / "handoffs/olmblur_classic_current_install_20260812"
MANIFEST = HANDOFF / "manifest.json"
CURRENT = HANDOFF / "current_build.plugin"
PREVIOUS = HANDOFF / "previous_build.plugin"
BUILD_LOG = HANDOFF / "xcodebuild.log"
INSTALLED_BUNDLE = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMBlur.plugin"
INSTALLED = INSTALLED_BUNDLE / "Contents/MacOS/OLMBlur"

EXPECTED_SOURCE_SHA = "21f3c96acd699ed463635435ed586030d65784406d71d06333a5d0afe6618c89"
EXPECTED_CURRENT_SHA = "b1461f8ee35b3d566a9825e9e04882c8ec28b51ce9e67dbbd83f463d706d943f"
EXPECTED_PREVIOUS_SHA = "272b764a0d5ebbc4f7167eebdfd36a645be9d5a96ff23ebf64a92b464d575d22"
EXPECTED_RAW_SHA = "a620dbf7fa18332197672053b6c26168673caef19d4ce7a9d4babb77ec75adfa"
EXPECTED_OBS_SHA = "5a1b5d1e1533e8733e23f7adc9d162130859d1a03227463625d6b146f8b3bdd4"
EXPECTED_OBS_RUNNER_SHA = "dbb0bf8886ef298f9517c8345cd2fafbb62ac82827ca981b9e7138fd086ae23b"
EXPECTED_SANITIZER_SHA = "54c1e51ea579a5b584bf9af5e336afb79513875cad6129a859f6eb2498119a7e"
EXPECTED_RUNNER_SHA = "b612b08516020b38f54de0ab01fef10da38ef0f0c107ac7d9fd72cc421afca58"
EXPECTED_MANIFEST_SHA = "48907c060d8d20c0fc9bdaccb103463a47556dd1e78eab0faa5bdee169244666"
EXPECTED_CLOSURE_SHA = "510c40c29f133ad5bee6a9a1d9d2105a56a1eb9552fcbbc52ceca6d92886a28a"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(value: object) -> str:
    return hashlib.sha256((json.dumps(value, indent=2, sort_keys=True) + "\n").encode()).hexdigest()


def archs() -> list[str]:
    return subprocess.check_output(["lipo", "-archs", str(INSTALLED)], text=True).split()


def signed() -> bool:
    return subprocess.run(
        ["codesign", "--verify", "--deep", "--strict", str(INSTALLED_BUNDLE)],
        capture_output=True,
    ).returncode == 0


def installed_count() -> int:
    roots = [
        Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore",
        Path("/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore"),
    ]
    return sum(1 for root in roots if (root / "OLMBlur.plugin").is_dir())


def sanitized_observation() -> dict:
    value = json.loads(OBS.read_text())
    value["claim_boundary"] = (
        "Fresh AE installed-path load, effect add, and default-parameter PF32 Software render only; "
        "no live classic PF8/PF16 pixel-exact or owner-route claim."
    )
    value["gates"]["classic_pf8_pf16_live_pixel_exact_claim"] = value["gates"].pop(
        "lab76_live_pixel_exact_claim"
    )
    value["provenance"] = {
        "observed_raw_sha256_before_semantic_label_sanitization": sha(OBS),
        "temporary_runner_sha256": sha(OBS_RUNNER),
        "sanitization": (
            "Observation values are unchanged. Only ColorKey-template Lab76 claim labels were replaced "
            "with OLMBlur classic fail-closed labels before repository persistence."
        ),
    }
    return value


def bundle_fields(bundle: Path) -> dict:
    return {
        "binary_sha256": sha(bundle / "Contents/MacOS/OLMBlur"),
        "info_plist_sha256": sha(bundle / "Contents/Info.plist"),
        "resource_sha256": sha(bundle / "Contents/Resources/OLMBlur.rsrc"),
    }


def expected_manifest() -> dict:
    return {
        "schema_version": 1,
        "current_build": {"bundle": "current_build.plugin", **bundle_fields(CURRENT)},
        "previous_build": {"bundle": "previous_build.plugin", **bundle_fields(PREVIOUS)},
        "xcodebuild_log_sha256": sha(BUILD_LOG),
        "claim_boundary": (
            "The frozen source, build transcript, current artifact and prior backup are recorded alongside "
            "one another. This manifest does not claim reproducible binary identity from source alone."
        ),
    }


def validates(summary: dict, raw: dict, manifest: dict) -> bool:
    try:
        pid = str(summary["host_smoke"]["ae_pid"])
        effect = raw["execution"]["ae_return"]["effect"]
        project = raw["execution"]["ae_return"]["project"]
        outputs = raw["execution"]["ae_return"]["outputs"]
        host = summary["host_smoke"]
        defaults = [(x["index"], x["name"], x["value"]) for x in effect["parameters_before"]]
        durable = summary["durable_artifacts"]
        current_fields = bundle_fields(CURRENT)
        installed_fields = {
            "binary_sha256": sha(INSTALLED),
            "info_plist_sha256": sha(INSTALLED_BUNDLE / "Contents/Info.plist"),
            "resource_sha256": sha(INSTALLED_BUNDLE / "Contents/Resources/OLMBlur.rsrc"),
        }
        return all(
            (
                summary["schema_version"] == 1,
                summary["kind"] == "olmblur_classic_current_install_smoke",
                summary["status"] == "installed_host_smoke_pass_no_classic_pixel_promotion",
                summary["build"]["production_source_sha256"] == sha(SOURCE) == EXPECTED_SOURCE_SHA,
                summary["build"]["source_binary_relation"]
                == "recorded alongside the build transcript and durable artifact; not a reproducible-build claim",
                summary["build"]["configuration"] == "Debug",
                summary["build"]["architectures"] == archs() == ["x86_64", "arm64"],
                summary["build"]["codesign"] == "adhoc",
                summary["build"]["codesign_deep_strict"] is signed() is True,
                summary["installed_bundle"]["binary_sha256"] == sha(INSTALLED) == EXPECTED_CURRENT_SHA,
                summary["installed_bundle"]["previous_binary_sha256"]
                == sha(PREVIOUS / "Contents/MacOS/OLMBlur")
                == EXPECTED_PREVIOUS_SHA,
                summary["installed_bundle"]["matching_bundle_count"] == installed_count() == 1,
                summary["installed_bundle"]["recoverable_backup"]
                == "handoffs/olmblur_classic_current_install_20260812/previous_build.plugin",
                raw == sanitized_observation(),
                canonical_sha(raw) == EXPECTED_RAW_SHA,
                host["raw_report"] == {
                    "path": "refs/conformance/olmblur_classic_current_install_smoke_raw_20260812.json",
                    "sha256": EXPECTED_RAW_SHA,
                },
                host["observed_raw"]["sha256"] == sha(OBS) == EXPECTED_OBS_SHA,
                host["observed_runner"]["sha256"] == sha(OBS_RUNNER) == EXPECTED_OBS_RUNNER_SHA,
                host["sanitizer"]["sha256"] == sha(SANITIZER) == EXPECTED_SANITIZER_SHA,
                host["replay_runner"]["sha256"] == sha(RUNNER) == EXPECTED_RUNNER_SHA,
                summary["classic_public_entry_closure"]["sha256"]
                == sha(CLOSURE)
                == EXPECTED_CLOSURE_SHA,
                durable == {
                    "manifest": "handoffs/olmblur_classic_current_install_20260812/manifest.json",
                    "manifest_sha256": EXPECTED_MANIFEST_SHA,
                    "current_bundle": "handoffs/olmblur_classic_current_install_20260812/current_build.plugin",
                    "previous_bundle": "handoffs/olmblur_classic_current_install_20260812/previous_build.plugin",
                    "build_log": "handoffs/olmblur_classic_current_install_20260812/xcodebuild.log",
                },
                sha(MANIFEST) == EXPECTED_MANIFEST_SHA,
                manifest == expected_manifest(),
                current_fields == installed_fields,
                manifest["current_build"] == {"bundle": "current_build.plugin", **installed_fields},
                manifest["previous_build"]
                == {"bundle": "previous_build.plugin", **bundle_fields(PREVIOUS)},
                raw["status"] == "installed_host_smoke_pass",
                raw["application"]["plist_short_version"] == "26.3.0",
                raw["claim_boundary"]
                == "Fresh AE installed-path load, effect add, and default-parameter PF32 Software render only; no live classic PF8/PF16 pixel-exact or owner-route claim.",
                raw["gates"]
                == {
                    "classic_pf8_pf16_live_pixel_exact_claim": False,
                    "effect_add_and_render_completed": True,
                    "fresh_process": True,
                    "installed_hash_unchanged": True,
                    "loaded_module_identity_exact_after_effect_add": True,
                },
                raw["fresh_host"]["initial_ae_pids"] == [],
                raw["fresh_host"]["loaded_modules_pre_render"] == {pid: []},
                raw["fresh_host"]["loaded_modules_post_render"] == {pid: [str(INSTALLED)]},
                raw["fresh_host"]["agent_quit_ae"] is True,
                raw["installed_plugin"]["binary_sha256_pre"]
                == raw["installed_plugin"]["binary_sha256_post"]
                == sha(INSTALLED),
                effect["match_name"] == host["effect_match_name"] == "OLM OLM Blur",
                effect["parameter_count"] == host["default_parameter_count"] == 5,
                effect["parameters_unchanged"] is host["parameters_unchanged"] is True,
                effect["parameters_before"] == effect["parameters_after"],
                defaults
                == [
                    (1, "Blur Amount", 5),
                    (2, "Blur Smoothness", 100),
                    (3, "Number of Repeat", 2),
                    (4, "Bias Direction", 1),
                    (5, "Legacy", 0),
                ],
                project
                == {
                    "bits_per_channel": 32,
                    "dimensions": [64, 36],
                    "linear_blending": False,
                    "renderer": "SOFTWARE",
                    "renderer_raw": 1816,
                    "working_space": "None",
                },
                host["ae_version"] == raw["execution"]["ae_return"]["ae_version"] == "26.3x87",
                host["renderer"] == project["renderer"],
                host["renderer_raw"] == project["renderer_raw"],
                host["dimensions"] == project["dimensions"],
                host["working_space"] == project["working_space"],
                host["linear_blending"] == project["linear_blending"],
                host["depth"] == "PF32",
                host["fresh_process"] is True,
                host["loaded_module_path"] == str(INSTALLED),
                host["loaded_module_identity_exact"] is True,
                host["ae_quit_after_smoke"] is True,
                host["control_exr_sha256"]
                == outputs["control"]["sha256"]
                == "038038fcced17f79d5734db404b4c8c97199a6fa5fa498d30c09022fd63a790a",
                host["effect_on_exr_sha256"]
                == outputs["effect_on"]["sha256"]
                == "551c7bd47abc58c961c6e11163b547d73d84d3995e93f5b71158b9852c621019",
                outputs["control"]["sha256"] != outputs["effect_on"]["sha256"],
                summary["claims_not_made"]
                == [
                    "No live-AE classic PF8/PF16 pixel-exact claim",
                    "No proof that AE routed this PF32 render through classic PF_Cmd_RENDER",
                    "No Windows/Mac pixel equality claim from these EXR hashes",
                    "No arbitrary parameter, geometry, depth, renderer, GPU, or host promotion",
                ],
            )
        )
    except (KeyError, TypeError, OSError, subprocess.SubprocessError):
        return False


class SmokeTests(unittest.TestCase):
    def setUp(self):
        self.summary = json.loads(SUMMARY.read_text())
        self.raw = json.loads(RAW.read_text())
        self.manifest = json.loads(MANIFEST.read_text())

    def test_bound(self):
        self.assertTrue(validates(self.summary, self.raw, self.manifest))

    def test_tamper(self):
        mutations = (
            lambda s, r, m: s["build"].update(production_source_sha256="0" * 64),
            lambda s, r, m: s["build"].update(architectures=["arm64"]),
            lambda s, r, m: s["build"].update(codesign_deep_strict=False),
            lambda s, r, m: s["installed_bundle"].update(matching_bundle_count=2),
            lambda s, r, m: s["host_smoke"]["raw_report"].update(sha256="0" * 64),
            lambda s, r, m: s["host_smoke"]["replay_runner"].update(sha256="0" * 64),
            lambda s, r, m: s["durable_artifacts"].update(manifest_sha256="0" * 64),
            lambda s, r, m: m["current_build"].update(binary_sha256="0" * 64),
            lambda s, r, m: m["previous_build"].update(resource_sha256="0" * 64),
            lambda s, r, m: m.update(xcodebuild_log_sha256="0" * 64),
            lambda s, r, m: m.update(claim_boundary="reproducible build"),
            lambda s, r, m: r["gates"].update(classic_pf8_pf16_live_pixel_exact_claim=True),
            lambda s, r, m: r["fresh_host"].update(agent_quit_ae=False),
            lambda s, r, m: r["execution"]["ae_return"]["effect"].update(parameters_unchanged=False),
            lambda s, r, m: r["execution"]["ae_return"]["effect"]["parameters_before"][0].update(value=6),
            lambda s, r, m: r["execution"]["ae_return"]["project"].update(bits_per_channel=16),
            lambda s, r, m: r["execution"]["ae_return"]["outputs"]["control"].update(sha256="0" * 64),
            lambda s, r, m: s["host_smoke"].update(working_space="sRGB"),
        )
        for mutation in mutations:
            summary, raw, manifest = copy.deepcopy(self.summary), copy.deepcopy(self.raw), copy.deepcopy(self.manifest)
            mutation(summary, raw, manifest)
            self.assertFalse(validates(summary, raw, manifest))


if __name__ == "__main__":
    unittest.main()
