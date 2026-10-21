from __future__ import annotations

import copy
import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUMMARY = (
    ROOT
    / "refs/conformance/"
    "olmdirectionalblur_type2_natural64_current_install_smoke_20260812.json"
)
RAW = (
    ROOT
    / "refs/conformance/"
    "olmdirectionalblur_type2_natural64_current_install_smoke_raw_20260812.json"
)
CLOSURE = (
    ROOT
    / "refs/conformance/"
    "olmdirectionalblur_type2_natural64_aexcompat_closure_20260812.json"
)
SOURCE = ROOT / "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp"

SOURCE_SHA = "b37b100cf99ef900bb7b661a013e5d1bf4b8e106214887d199adfa8f505c8bc6"
CLOSURE_SHA = "3b75a06e07446df07f4445cc0ce40798febb42087f5c6e353b0c9b9dc6d58647"
CURRENT_SOURCE_SHA = "494116880d037a0d44a48b0e0ebe0fc5358b4cd8892b90ca8c61ea8a7bb2e845"
CURRENT_CLOSURE_SHA = "1a98a25bf6bbf4dadb340a122721a26965557c54f849c4881eda20a983e6eba3"
INSTALLED_SHA = "9142c19937c54dec8ed07a06c14181db1cf274335b599605251982bf671516f6"
PREVIOUS_SHA = "f9c914b6fd30b4715d3c469859f2271b0bcdbadd72a15724438cffbf61b09940"
RAW_SHA = "3482673aa164cf03e7f99945a29eb35a74fa4a9e29942370625f6ac2d36112e2"
SUMMARY_CANONICAL_SHA = "823bbf63e9cb555cadd39eb80870162f86fc48dc21e5014cded98cc15f59dde4"
INPUT_SHA = "0673ea66da1913c89180fed2b9500cd26ce5b88511cf2c59dfd9d515e67a5e4e"
OUTPUT_SHA = "bf59701e9e4e562c9cb3e174bf9302283ea779f0e799303506772ff20208c99e"
INSTALLED_PATH = (
    "/Users/onmk/Library/Application Support/Adobe/Common/Plug-ins/7.0/"
    "MediaCore/OLMDirectionalBlur.plugin/Contents/MacOS/OLMDirectionalBlur"
)
RAW_RELATIVE = (
    "refs/conformance/"
    "olmdirectionalblur_type2_natural64_current_install_smoke_raw_20260812.json"
)
CLOSURE_RELATIVE = (
    "refs/conformance/"
    "olmdirectionalblur_type2_natural64_aexcompat_closure_20260812.json"
)
NO_LIVE_TUPLE_CLAIM = (
    "No live-AE Type-2 natural64 tuple pixel claim; this smoke used plugin defaults"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: dict) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validates_historical_snapshot(summary: dict, raw: dict) -> bool:
    try:
        build = summary["build"]
        installed = summary["installed_bundle"]
        host = summary["host_smoke"]
        closure_binding = summary["hostless_type2_natural64_closure"]
        return all(
            [
                canonical_sha256(summary) == SUMMARY_CANONICAL_SHA,
                summary["schema_version"] == 1,
                summary["kind"]
                == "olmdirectionalblur_type2_natural64_current_install_smoke_20260812",
                summary["status"] == "installed_host_smoke_pass_pixel_gate_fail_closed",
                build["production_source_path"]
                == "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp",
                build["production_source_sha256"] == SOURCE_SHA,
                build["architectures"] == ["x86_64", "arm64"],
                build["codesign"] == "adhoc",
                build["codesign_deep_strict"] is True,
                installed["path"]
                == "~/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMDirectionalBlur.plugin",
                installed["binary_path"].replace("~", "/Users/onmk")
                == INSTALLED_PATH,
                installed["binary_sha256"] == INSTALLED_SHA,
                installed["matching_bundle_count"] == 1,
                installed["previous_binary_sha256"] == PREVIOUS_SHA,
                installed["recoverable_backup"]
                == "/tmp/olmdirectionalblur-natural64-backup.nvITrj/OLMDirectionalBlur.plugin",
                host["application"] == "Adobe After Effects 2026",
                host["ae_version"] == "26.3x87",
                host["ae_pid"] == 92353,
                host["renderer_raw"] == 1816,
                host["renderer"] == "SOFTWARE",
                host["depth"] == "PF32",
                host["composition_geometry"] == [64, 36],
                host["input_png_sha256"] == INPUT_SHA,
                host["effect_match_name"] == "OLM Directional Blur",
                host["effect_added"] is True,
                host["effect_enabled"] is True,
                host["parameters"]
                == "plugin defaults; no Type-2 natural64 tuple values were applied",
                host["ae_result_status"] == "ok",
                host["loaded_module_path_observed"] == INSTALLED_PATH,
                host["loaded_module_count_observed"] == 1,
                host["loaded_module_observation"]
                == "ephemeral vmmap observation for AE PID 92353; the raw vmmap output was not retained",
                host["loaded_module_identity_persisted"] is False,
                "not independently proven" in host["loaded_module_identity_semantics"],
                host["output_png_sha256"] == OUTPUT_SHA,
                host["render_output_created"] is True,
                host["raw_result"]
                == {"path": RAW_RELATIVE, "sha256": RAW_SHA},
                sha256(RAW) == RAW_SHA,
                raw
                == {
                    "status": "ok",
                    "ae_version": "26.3x87",
                    "bits": 32,
                    "renderer": 1816,
                    "binary": INSTALLED_SHA,
                    "output": OUTPUT_SHA,
                    "error": "",
                    "line": 0,
                },
                host["pixel_exact"] is False,
                host["scope"]
                == "script-checked current on-disk Universal binary / default-effect add / SOFTWARE PF32 render; mapped-module identity remains unpersisted operator observation",
                closure_binding["path"] == CLOSURE_RELATIVE,
                closure_binding["sha256"] == CLOSURE_SHA,
                closure_binding["status"] == "exact_bounded_public_owner",
                closure_binding["production_source_sha256"] == SOURCE_SHA,
                "separate" in closure_binding["relation_to_installed_build"],
                summary["claims_not_made"]
                == [
                    NO_LIVE_TUPLE_CLAIM,
                    "No Windows/Mac AE pixel-exact claim from this output PNG",
                    "No promotion beyond the separate bounded hostless closure",
                    "No claim for arbitrary parameters, dimensions, source content, rowbytes, renderer, or host version",
                ],
            ]
        )
    except (KeyError, TypeError):
        return False


class DirectionalBlurNatural64CurrentInstallSmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
        cls.raw = json.loads(RAW.read_bytes())
        cls.closure = json.loads(CLOSURE.read_text(encoding="utf-8"))

    def test_checked_in_evidence_validates(self) -> None:
        self.assertTrue(validates_historical_snapshot(self.summary, self.raw))

    def test_current_workspace_supersedes_historical_snapshot(self) -> None:
        self.assertEqual(sha256(SOURCE), CURRENT_SOURCE_SHA)
        self.assertEqual(sha256(CLOSURE), CURRENT_CLOSURE_SHA)
        self.assertNotEqual(CURRENT_SOURCE_SHA, SOURCE_SHA)
        self.assertNotEqual(CURRENT_CLOSURE_SHA, CLOSURE_SHA)
        self.assertEqual(self.closure["status"], "exact_bounded_public_owner")
        self.assertEqual(
            self.closure["identities"]["production_sha256"], CURRENT_SOURCE_SHA
        )
        self.assertEqual(self.closure["counterfactuals"]["rejects"], 64)
        self.assertEqual(
            self.closure["counterfactuals"]["source_one_away_or_unlisted_rejects"],
            12,
        )
        self.assertEqual(
            set(self.closure["input"]["decoded_argb_sha256"]),
            {"PF8", "PF16", "PF32"},
        )
        self.assertEqual(len(self.closure["source_basis"]), 4)
        for row in self.closure["source_basis"]:
            self.assertEqual(
                set(row["typed_input_sha256"]), {"PF8", "PF16", "PF32"}
            )

    def test_identity_result_scope_and_closure_tampering_fails_closed(self) -> None:
        mutations = (
            lambda s, r, c: s["build"].update(production_source_sha256="0" * 64),
            lambda s, r, c: s["build"].update(architectures=["arm64"]),
            lambda s, r, c: s["build"].update(codesign="unsigned"),
            lambda s, r, c: s["build"].update(codesign_deep_strict=False),
            lambda s, r, c: s["installed_bundle"].update(binary_sha256="0" * 64),
            lambda s, r, c: s["installed_bundle"].update(matching_bundle_count=2),
            lambda s, r, c: s["installed_bundle"].update(previous_binary_sha256="0" * 64),
            lambda s, r, c: s["host_smoke"].update(ae_pid=0),
            lambda s, r, c: s["host_smoke"].update(loaded_module_path_observed="/tmp/wrong"),
            lambda s, r, c: s["host_smoke"].update(loaded_module_count_observed=2),
            lambda s, r, c: s["host_smoke"].update(loaded_module_identity_persisted=True),
            lambda s, r, c: s["host_smoke"].update(composition_geometry=[16, 16]),
            lambda s, r, c: s["host_smoke"].update(input_png_sha256="0" * 64),
            lambda s, r, c: s["host_smoke"].update(effect_added=False),
            lambda s, r, c: s["host_smoke"].update(effect_enabled=False),
            lambda s, r, c: s["host_smoke"].update(parameters="natural64 tuple"),
            lambda s, r, c: s["host_smoke"].update(output_png_sha256="0" * 64),
            lambda s, r, c: s["host_smoke"].update(pixel_exact=True),
            lambda s, r, c: s["host_smoke"].update(scope="pixel exact"),
            lambda s, r, c: s["host_smoke"]["raw_result"].update(sha256="0" * 64),
            lambda s, r, c: r.update(binary="0" * 64),
            lambda s, r, c: r.update(output="0" * 64),
            lambda s, r, c: r.update(status="error"),
            lambda s, r, c: s["hostless_type2_natural64_closure"].update(sha256="0" * 64),
            lambda s, r, c: s["hostless_type2_natural64_closure"].update(status="fail_closed"),
            lambda s, r, c: s["claims_not_made"].remove(NO_LIVE_TUPLE_CLAIM),
        )
        for index, mutate in enumerate(mutations):
            summary = copy.deepcopy(self.summary)
            raw = copy.deepcopy(self.raw)
            closure = copy.deepcopy(self.closure)
            mutate(summary, raw, closure)
            with self.subTest(index=index):
                self.assertFalse(validates_historical_snapshot(summary, raw))


if __name__ == "__main__":
    unittest.main()
