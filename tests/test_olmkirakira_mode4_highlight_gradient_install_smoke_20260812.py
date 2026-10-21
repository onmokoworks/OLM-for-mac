import copy
import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "refs/conformance/olmkirakira_mode4_highlight_gradient_install_smoke_20260812.json"
RAW = ROOT / "refs/conformance/olmkirakira_mode4_highlight_gradient_install_smoke_raw_20260812.json"
CLOSURE = ROOT / "refs/conformance/olmkirakira_mode4_highlight_gradient_closure_20260812.json"
INSTALLED_PATH = "/Users/onmk/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMKiraKira.plugin/Contents/MacOS/OLMKiraKira"
INSTALLED_SHA = "136ca31b2a2f75bd2dc624bbba4f907e29214202af80926c091abcef536f5c92"
RAW_SHA = "a335c37dc1825699ae444ad824db6676dc7c180196df22ac6abc147e4dabda10"
CLOSURE_SHA = "cda745b1fb26cdffd3e77d75863d0d231f4d5b82dfb7972e8b208b74c98b1fd7"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validates(summary: dict, raw: dict) -> bool:
    try:
        row = raw["rows"][0]
        ae = row["ae_result"]
        host = row["host_identity"]
        branches = row["branches"]
        params = {item["display_name"]: item["value"] for item in ae["parameters_after"]}
        raw_binding = summary["host_smoke"]["raw_report"]
        closure_binding = summary["hostless_highlight_gradient_closure"]
        return all([
            summary["schema_version"] == 1,
            summary["kind"] == "olmkirakira_mode4_highlight_gradient_install_smoke",
            summary["status"] == "installed_host_smoke_pass_pixel_gate_fail_closed",
            raw_binding == {
                "path": "refs/conformance/olmkirakira_mode4_highlight_gradient_install_smoke_raw_20260812.json",
                "sha256": RAW_SHA,
            },
            sha256(RAW) == RAW_SHA,
            closure_binding["sha256"] == CLOSURE_SHA,
            closure_binding["status"] == "raw_exact",
            "historical closure snapshot" in closure_binding["relation_to_installed_build"],
            "current workspace closure has superseded that snapshot" in closure_binding["relation_to_installed_build"],
            raw["installed_plugin"] == {"path": INSTALLED_PATH, "sha256": INSTALLED_SHA},
            summary["installed_bundle"]["binary_sha256"] == INSTALLED_SHA,
            raw["case_id"] == "kk_mapped_bm4_mm1_hi_r5_orange_opaque",
            raw["status"] == "mismatch",
            raw["exact_depths"] == [],
            len(raw["rows"]) == 1,
            row["depth"] == 32 and row["status"] == "mismatch",
            ae["status"] == "ok" and ae["ae_version"] == "26.3x87",
            ae["renderer_raw"] == 1816 and ae["bits_per_channel"] == 32,
            params["Highlight Radius"] == 5,
            params["Blur Mode"] == 4,
            params["Merge mode"] == 1,
            params["Brightness Gain"] == 1,
            host == {"ae_pids": [60878], "loaded_kira_modules": [INSTALLED_PATH], "exact": True},
            branches["no_effect"]["mac_sha256"] == summary["host_smoke"]["no_effect_exr_sha256"],
            branches["effect_on"]["mac_sha256"] == summary["host_smoke"]["effect_on_exr_sha256"],
            branches["no_effect"]["raw_float32_compare"]["equal"] is False,
            branches["effect_on"]["raw_float32_compare"]["equal"] is False,
            branches["no_effect"]["raw_float32_compare"]["nonzero_count"] == 6220800,
            branches["effect_on"]["raw_float32_compare"]["nonzero_count"] == 6220800,
            summary["host_smoke"]["loaded_module_identity_exact"] is True,
            summary["host_smoke"]["windows_raw_float32_exact"] is False,
        ])
    except (KeyError, IndexError, TypeError):
        return False


class KiraHighlightGradientInstallSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary = json.loads(SUMMARY.read_text())
        cls.raw = json.loads(RAW.read_text())

    def test_raw_report_is_bound_to_summary(self):
        self.assertTrue(validates(self.summary, self.raw))

    def test_identity_and_result_tampering_fails_closed(self):
        mutations = []
        for mutate in (
            lambda s, r: r["installed_plugin"].update(sha256="0" * 64),
            lambda s, r: r["rows"][0]["host_identity"].update(ae_pids=[]),
            lambda s, r: r["rows"][0]["host_identity"].update(loaded_kira_modules=[]),
            lambda s, r: r["rows"][0]["ae_result"]["parameters_after"][5].update(value=4),
            lambda s, r: r["rows"][0]["branches"]["no_effect"]["raw_float32_compare"].update(nonzero_count=0),
            lambda s, r: s["host_smoke"].__setitem__("no_effect_exr_sha256", "0" * 64),
            lambda s, r: s["host_smoke"]["raw_report"].update(sha256="0" * 64),
            lambda s, r: s["hostless_highlight_gradient_closure"].update(sha256="0" * 64),
            lambda s, r: s["hostless_highlight_gradient_closure"].update(relation_to_installed_build="fake"),
        ):
            summary, raw = copy.deepcopy(self.summary), copy.deepcopy(self.raw)
            mutate(summary, raw)
            mutations.append(validates(summary, raw))
        self.assertEqual(mutations, [False] * len(mutations))


if __name__ == "__main__":
    unittest.main()
