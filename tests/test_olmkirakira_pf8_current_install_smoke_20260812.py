import copy
import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "refs/conformance/olmkirakira_pf8_current_install_smoke_20260812.json"
RAW = ROOT / "refs/conformance/olmkirakira_pf8_current_install_smoke_raw_20260812.json"
CLOSURE = ROOT / "refs/conformance/olmkirakira_pf8_source_decode_closure_20260812.json"
HIGHLIGHT_CLOSURE = ROOT / "refs/conformance/olmkirakira_mode4_highlight_gradient_closure_20260812.json"
SOURCE = ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp"
CORE = ROOT / "core/kirakira_highlight.h"
INSTALLED_PATH = "/Users/onmk/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMKiraKira.plugin/Contents/MacOS/OLMKiraKira"
SOURCE_SHA = "c05dc15a0f7a12857d70e0387d55ee5d18d95a25c5b76c316a93399703a2091b"
CORE_SHA = "e98232e4224b6ae4dd372216e10c29f3ba6621f68ab6cb10b56a02b9cc248390"
INSTALLED_SHA = "5248592a32d3a34bac67c43a1a65af875097aa1c251840d1db4aa8dcd2b39367"
PREVIOUS_SHA = "136ca31b2a2f75bd2dc624bbba4f907e29214202af80926c091abcef536f5c92"
RAW_SHA = "0ec121cce5330e532589a752a361ea205dc555c1ea4d9e01b3132ce6a14e21c0"
CLOSURE_SHA = "50a10ee36bd6e4a1031db88ec836897c6f508b3bc0f2424c5a9c11e590678452"
HIGHLIGHT_CLOSURE_SHA = "cda745b1fb26cdffd3e77d75863d0d231f4d5b82dfb7972e8b208b74c98b1fd7"
NO_EFFECT_SHA = "dc92c84754876c15faa89e48dd4e10e3e0864eb7c4a4febca4fb3495a1d8e019"
EFFECT_ON_SHA = "79462401862ae242928edc0b9282551ebff7bfe07fb4acfa03b0b8c1c3e1206e"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validates(summary: dict, raw: dict) -> bool:
    try:
        row = raw["rows"][0]
        ae = row["ae_result"]
        host = row["host_identity"]
        branches = row["branches"]
        before = {item["display_name"]: item["value"] for item in ae["parameters_before"]}
        after = {item["display_name"]: item["value"] for item in ae["parameters_after"]}
        raw_binding = summary["host_smoke"]["raw_report"]
        closure_binding = summary["hostless_pf8_source_decode_closure"]
        highlight_binding = summary["hostless_highlight_gradient_closure"]
        return all([
            summary["schema_version"] == 1,
            summary["kind"] == "olmkirakira_pf8_current_install_smoke",
            summary["status"] == "installed_host_smoke_pass_pixel_gate_fail_closed",
            summary["build"]["production_source_sha256"] == SOURCE_SHA,
            summary["build"]["highlight_core_sha256"] == CORE_SHA,
            summary["build"]["architectures"] == ["x86_64", "arm64"],
            summary["build"]["codesign_deep_strict"] is True,
            summary["installed_bundle"]["binary_sha256"] == INSTALLED_SHA,
            summary["installed_bundle"]["binary_path"].replace("~", "/Users/onmk") == INSTALLED_PATH,
            summary["installed_bundle"]["matching_bundle_count"] == 1,
            summary["installed_bundle"]["previous_binary_sha256"] == PREVIOUS_SHA,
            summary["installed_bundle"]["recoverable_backup"] == "/tmp/olmkirakira-pf8-install-backup.lcSjG1/OLMKiraKira.plugin",
            raw_binding == {
                "path": "refs/conformance/olmkirakira_pf8_current_install_smoke_raw_20260812.json",
                "sha256": RAW_SHA,
            },
            sha256(RAW) == RAW_SHA,
            raw["installed_plugin"] == {"path": INSTALLED_PATH, "sha256": INSTALLED_SHA},
            raw["case_id"] == "kk_mapped_bm4_mm1_hi_r5_orange_opaque",
            raw["status"] == "mismatch" and raw["exact_depths"] == [],
            len(raw["rows"]) == 1,
            row["depth"] == 32 and row["status"] == "mismatch",
            ae["status"] == "ok" and ae["ae_version"] == "26.3x87",
            ae["renderer_raw"] == 1816 and ae["bits_per_channel"] == 32,
            len(ae["parameters_before"]) == 25,
            len(ae["parameters_after"]) == 25,
            ae["parameters_before"] == ae["parameters_after"],
            after["Highlight Radius"] == 5,
            after["Blur Mode"] == 4,
            after["Merge mode"] == 1,
            after["Brightness Gain"] == 1,
            host == {"ae_pids": [73457], "loaded_kira_modules": [INSTALLED_PATH], "exact": True},
            summary["host_smoke"]["ae_pid"] == 73457,
            summary["host_smoke"]["loaded_module_path"] == INSTALLED_PATH,
            summary["host_smoke"]["loaded_module_count"] == 1,
            summary["host_smoke"]["loaded_module_identity_exact"] is True,
            branches["no_effect"]["mac_sha256"] == NO_EFFECT_SHA == summary["host_smoke"]["no_effect_exr_sha256"],
            branches["effect_on"]["mac_sha256"] == EFFECT_ON_SHA == summary["host_smoke"]["effect_on_exr_sha256"],
            branches["no_effect"]["raw_float32_compare"]["equal"] is False,
            branches["effect_on"]["raw_float32_compare"]["equal"] is False,
            branches["no_effect"]["raw_float32_compare"]["nonzero_count"] == 6220800,
            branches["effect_on"]["raw_float32_compare"]["nonzero_count"] == 6220800,
            summary["host_smoke"]["windows_raw_float32_exact"] is False,
            summary["host_smoke"]["depth"] == "PF32",
            summary["host_smoke"]["input_interpretation"] == {
                "preserve_rgb": None,
                "working_space": "None",
                "linear_blending": False,
            },
            closure_binding["sha256"] == CLOSURE_SHA,
            closure_binding["status"] == "raw_exact",
            closure_binding["path"] == "refs/conformance/olmkirakira_pf8_source_decode_closure_20260812.json",
            "historical closure snapshot" in closure_binding["relation_to_installed_build"],
            "current workspace closure has superseded that snapshot" in closure_binding["relation_to_installed_build"],
            highlight_binding["sha256"] == HIGHLIGHT_CLOSURE_SHA,
            highlight_binding["status"] == "raw_exact",
            highlight_binding["path"] == "refs/conformance/olmkirakira_mode4_highlight_gradient_closure_20260812.json",
            "historical closure snapshot" in highlight_binding["relation_to_installed_build"],
            "current workspace closure has superseded that snapshot" in highlight_binding["relation_to_installed_build"],
            summary["historical_install_evidence"]["binary_sha256"] == PREVIOUS_SHA,
            "historical" in summary["historical_install_evidence"]["relation"],
            "No live-AE PF8 pixel claim; the recorded PF8-corrected build smoke row is PF32" in summary["claims_not_made"],
        ])
    except (KeyError, IndexError, TypeError):
        return False


class KiraPF8CurrentInstallSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary = json.loads(SUMMARY.read_text())
        cls.raw = json.loads(RAW.read_text())

    def test_raw_report_build_and_closure_are_bound(self):
        self.assertTrue(validates(self.summary, self.raw))

    def test_identity_parameter_and_result_tampering_fails_closed(self):
        mutations = []
        for mutate in (
            lambda s, r: s["build"].update(production_source_sha256="0" * 64),
            lambda s, r: s["build"].update(highlight_core_sha256="0" * 64),
            lambda s, r: s["installed_bundle"].update(binary_sha256="0" * 64),
            lambda s, r: s["installed_bundle"].update(matching_bundle_count=2),
            lambda s, r: r["installed_plugin"].update(sha256="0" * 64),
            lambda s, r: r["rows"][0]["host_identity"].update(ae_pids=[]),
            lambda s, r: r["rows"][0]["host_identity"].update(loaded_kira_modules=[]),
            lambda s, r: r["rows"][0]["ae_result"]["parameters_after"][5].update(value=4),
            lambda s, r: r["rows"][0]["branches"]["no_effect"]["raw_float32_compare"].update(nonzero_count=0),
            lambda s, r: r["rows"][0]["branches"]["effect_on"]["raw_float32_compare"].update(nonzero_count=0),
            lambda s, r: r["rows"][0]["branches"]["no_effect"].update(mac_sha256="0" * 64),
            lambda s, r: r["rows"][0]["branches"]["effect_on"].update(mac_sha256="0" * 64),
            lambda s, r: r["rows"][0]["branches"]["no_effect"]["raw_float32_compare"].update(equal=True),
            lambda s, r: r["rows"][0]["branches"]["effect_on"]["raw_float32_compare"].update(equal=True),
            lambda s, r: s["host_smoke"].__setitem__("no_effect_exr_sha256", "0" * 64),
            lambda s, r: s["host_smoke"].__setitem__("effect_on_exr_sha256", "0" * 64),
            lambda s, r: s["host_smoke"].__setitem__("depth", "PF8"),
            lambda s, r: s["host_smoke"]["raw_report"].update(sha256="0" * 64),
            lambda s, r: s["hostless_pf8_source_decode_closure"].update(sha256="0" * 64),
            lambda s, r: s["hostless_highlight_gradient_closure"].update(sha256="0" * 64),
            lambda s, r: s["hostless_highlight_gradient_closure"].update(status="fail_closed"),
            lambda s, r: s["historical_install_evidence"].update(binary_sha256="0" * 64),
            lambda s, r: s["claims_not_made"].remove("No live-AE PF8 pixel claim; the recorded PF8-corrected build smoke row is PF32"),
        ):
            summary, raw = copy.deepcopy(self.summary), copy.deepcopy(self.raw)
            mutate(summary, raw)
            mutations.append(validates(summary, raw))
        self.assertEqual(mutations, [False] * len(mutations))


if __name__ == "__main__":
    unittest.main()
