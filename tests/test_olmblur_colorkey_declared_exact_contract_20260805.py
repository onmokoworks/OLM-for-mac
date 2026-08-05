#!/usr/bin/env python3
"""Fail-closed regression for the declared OLMBlur/OLMColorKey 32bpc cells.

This test intentionally validates retained, hash-bound AE evidence.  It does
not render AE and therefore cannot promote a new case or binary.
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONF = ROOT / "refs/conformance"
SHA256 = re.compile(r"^[0-9a-f]{64}$")
BLUR_AEX = "f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b"
COLORKEY_AEX = "9c6cca226a52d35ce7833fcc4c0f914f6b15b3abe0202e0957ba97ba3bb2cf2c"
COLORKEY_FINAL_MAC = "410d6cd6b568f7d2ae5bb426451eb3d628998a716a83f0cdbe3c5c0bc028ed7f"
WORDS = 1920 * 1080 * 4


def load(name: str) -> dict:
    return json.loads((CONF / name).read_text(encoding="utf-8"))


def assert_hash(test: unittest.TestCase, value: object) -> None:
    test.assertIsInstance(value, str)
    test.assertRegex(value, SHA256)


class DeclaredExactContractTests(unittest.TestCase):
    def test_olmblur_all_seven_retained_32bpc_cases_are_hash_bound(self):
        for number in range(1, 8):
            with self.subTest(case=number):
                row = load(f"olmblur_32bpc_case{number:04d}_ae_exact_20260727.json")
                self.assertTrue(row["ae_exact_claim"])
                self.assertEqual(row["case_id"], f"OLMBlur/case_{number:04d}")
                self.assertEqual(row["ae_version"], "26.3x87")
                self.assertEqual(row["contract"]["bits_per_channel"], 32)
                self.assertEqual(row["contract"]["renderer"]["raw"], 1816)
                self.assertEqual(row["contract"]["working_space_raw"], "None")
                self.assertEqual(row["windows"]["loaded_plugin_proof"]["aex_sha256"], BLUR_AEX)

                mac_proof = row["mac"].get("loaded_plugin_proof")
                mac_hash = mac_proof["module_sha256"] if mac_proof else row["mac"]["plugin"]["sha256"]
                assert_hash(self, mac_hash)
                for gate in ("no_effect_control", "effect_on"):
                    comparison = row["comparison"][gate]
                    self.assertEqual(comparison["total_values"], WORDS)
                    self.assertEqual(comparison["mismatched_values"], 0)
                    self.assertEqual(comparison["max_raw_u32_delta"], 0)
                for gate in ("no_effect_control", "effect_on"):
                    assert_hash(self, row["mac"]["outputs"][gate]["sha256"])
                    assert_hash(self, row["windows"]["outputs"][gate]["sha256"])

    def test_olmcolorkey_all_nine_retained_32bpc_cases_are_hash_bound(self):
        closeout = load("olmcolorkey_32bpc_all9_ae_exact_20260728.json")
        self.assertTrue(closeout["ae_exact_claim"])
        self.assertEqual(closeout["classification"], "windows_mac_ae_exact")
        self.assertEqual(closeout["binaries"]["windows_aex_sha256"], COLORKEY_AEX)
        self.assertEqual(closeout["binaries"]["mac_macho_sha256"], COLORKEY_FINAL_MAC)
        self.assertEqual(closeout["summary"]["declared_case_count"], 9)
        self.assertEqual(closeout["summary"]["raw_gate_count"], 18)
        self.assertEqual(closeout["summary"]["exact_gate_count"], 18)
        self.assertEqual(closeout["summary"]["max_raw_u32_delta"], 0)

        rows = closeout["new_windows_native_parameter_attested_cases"]
        self.assertEqual([r["case_id"] for r in rows], [
            f"olmcolorkey__case_{n:04d}" for n in (1, 3, 4, 5, 6, 7, 8)
        ])
        for row in rows:
            self.assertEqual(row["parameter_count"], 219)
            self.assertTrue(row["parameter_readback_exact"])
            assert_hash(self, row["source_aepx_sha256"])
            assert_hash(self, row["params_sha256"])
            for gate in ("no_effect", "effect_on"):
                result = row["gates"][gate]
                self.assertEqual(result["mismatched_float32_words"], 0)
                self.assertEqual(result["max_raw_u32_delta"], 0)
                assert_hash(self, result["windows_exr_sha256"])
                assert_hash(self, result["mac_exr_sha256"])

        prior = {r["case_id"]: load(Path(r["evidence"]).name)
                 for r in closeout["previously_promoted_cases"]}
        self.assertEqual(set(prior), {"olmcolorkey__case_0002", "olmcolorkey__case_0009"})
        case2 = prior["olmcolorkey__case_0002"]
        self.assertEqual(case2["windows"]["plugin_aex_sha256"], COLORKEY_AEX)
        for key in ("windows_control_vs_mac_control", "windows_effect_vs_mac_effect"):
            self.assertEqual(case2["raw_float32_comparisons"][key]["mismatched_values"], 0)
            self.assertEqual(case2["raw_float32_comparisons"][key]["max_raw_u32_delta"], 0)
        case9 = prior["olmcolorkey__case_0009"]
        self.assertEqual(case9["windows"]["aex_sha256"], COLORKEY_AEX)
        self.assertEqual(case9["mac"]["loaded_plugin_proof"]["module_sha256"], COLORKEY_FINAL_MAC)
        for gate in ("no_effect", "effect_on"):
            result = case9["exact_gates"][gate]
            self.assertEqual(result["word_count"], WORDS)
            self.assertEqual(result["mismatched_float32_words"], 0)
            self.assertEqual(result["max_raw_u32_delta"], 0)


if __name__ == "__main__":
    raise SystemExit(unittest.main())
