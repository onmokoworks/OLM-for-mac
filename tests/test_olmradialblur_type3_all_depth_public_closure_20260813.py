from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "tools/emulation/test_olmradialblur_type3_all_depth_public_closure_20260813.py"
REPORT = ROOT / "refs/conformance/olmradialblur_type3_all_depth_public_closure_20260813.json"
GENERATOR_SHA256 = "2538fae2eb4c2b3534058a219d9ac0a273fb5ec8a1ad7d19a6671efdef6665ec"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module():
    spec = importlib.util.spec_from_file_location("radial_type3_all_depth", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


class RadialType3AllDepthClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()
        cls.report = json.loads(REPORT.read_text())

    def test_generator_identity(self):
        self.assertEqual(sha(GENERATOR), GENERATOR_SHA256)

    def test_default_is_read_only_and_valid(self):
        before = sha(REPORT)
        subprocess.run([sys.executable, str(GENERATOR)], cwd=ROOT, check=True)
        self.assertEqual(sha(REPORT), before)

    def test_exact_expanded_depth_rows(self):
        self.module.validate_report(self.report)
        self.assertEqual([row["depth"] for row in self.report["rows"]],
                         [8] * 15 + [16] * 15 + [32] * 15)
        self.assertTrue(all(all(row["matches"].values()) for row in self.report["rows"]))
        for row in self.report["rows"]:
            for key in ("source_span", "pre_blur", "post_blur", "output"):
                self.assertEqual(row["actual"][key], row["candidate"][key])
            self.assertEqual(row["candidate"]["classic_output"], row["actual"]["output"])
            self.assertEqual(row["candidate"]["smart_output"], row["actual"]["output"])

    def test_recanonicalized_paired_tamper_rejected(self):
        altered = copy.deepcopy(self.report)
        altered["rows"][0]["actual"]["output"] = "0" * 64
        altered["rows"][0]["candidate"]["output"] = "0" * 64
        altered["rows"][0]["matches"]["output"] = True
        altered["rows_sha256"] = self.module.canonical_rows_sha256(altered["rows"])
        with self.assertRaises(AssertionError):
            self.module.validate_report(altered)

    def test_unknown_schema_key_rejected(self):
        altered = copy.deepcopy(self.report)
        altered["unbound"] = True
        with self.assertRaises(AssertionError):
            self.module.validate_report(altered)

    def test_source_and_layer_mutation_controls_are_bound(self):
        altered = copy.deepcopy(self.report)
        altered["rows"][1]["source_sha256"] = "f" * 64
        altered["rows_sha256"] = self.module.canonical_rows_sha256(altered["rows"])
        with self.assertRaises(AssertionError):
            self.module.validate_report(altered)

    def test_exact_source_and_alignment_guards_are_in_production(self):
        source = (ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp").read_text()
        for token in (
            "MatchesType3SmallSourceLayerPair<PixelT>(input, noise_world)",
            "sha256_active_rows_match_hex",
            "reinterpret_cast<std::uintptr_t>(input->data) % alignof(PixelT)",
            "reinterpret_cast<std::uintptr_t>(output->data) % alignof(PixelT)",
            "reinterpret_cast<std::uintptr_t>(noise_world->data) % alignof(PixelT)",
        ):
            self.assertIn(token, source)


if __name__ == "__main__":
    unittest.main()
