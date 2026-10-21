from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "tools/emulation/test_olmsmoother2_case07_unique_direct_oracle_20260814.py"
HARNESS = ROOT / "tools/emulation/olmsmoother2_case07_current_source_direct_harness_20260814.cpp"
REPORT = ROOT / "refs/conformance/olmsmoother2_case07_unique_direct_oracle_20260814.json"
NOTE = REPORT.with_suffix(".md")
GENERATOR_SHA256 = "4f0d4f38b6e9710e7b6cca61b25d6985159b914dc8ac6e46a7890101a9c3abfd"
HARNESS_SHA256 = "9ea4ea615cd25565cb2c6a9a73fd579424c1c9a36e690edc634ce164528f3172"
REPORT_SHA256 = "5be3cc58fb73fed148a927df4bc888ce217dd0f96906f54b44a9dce1b62b0063"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module():
    spec = importlib.util.spec_from_file_location("smoother2_case07_unique", GENERATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Smoother2Case07UniqueDirectOracleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()
        cls.report = json.loads(REPORT.read_text())

    def test_identities_and_complete_unique_preimage(self) -> None:
        self.assertEqual(sha256(GENERATOR), GENERATOR_SHA256)
        self.assertEqual(sha256(HARNESS), HARNESS_SHA256)
        self.assertEqual(sha256(REPORT), REPORT_SHA256)
        proof = self.report["proof"]
        self.assertEqual(proof["word_count"], 8294400)
        self.assertEqual(proof["alpha_mismatches"], 0)
        self.assertEqual(proof["float32_rgb_times_alpha_mismatches"], 0)
        self.assertEqual(proof["float32_divide_inverse_mismatches"], 0)
        self.assertEqual(proof["adjacent_float_preimage_collisions"], 0)
        self.assertEqual(proof["direct_vs_final_changed_rgb_words"], 3132)

    def test_default_and_validate_only_are_read_only(self) -> None:
        before = {path: path.read_bytes() for path in (REPORT, NOTE)}
        for extra in ([], ["--validate-only"]):
            run = subprocess.run([sys.executable, str(GENERATOR), *extra], cwd=ROOT,
                                 capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertIn("PASS_OLMSMOOTHER2_CASE07_UNIQUE_DIRECT_ORACLE_AE_FREE", run.stdout)
        self.assertEqual({path: path.read_bytes() for path in before}, before)

    def test_scope_broadening_and_identity_tamper_rejected(self) -> None:
        attacks = []
        for section, key, value in (
            ("production_policy", "case07_currently_admitted", False),
            ("production_policy", "production_changed_by_this_closure", True),
            ("oracle_relation", "preimage_unique_over_all_words", False),
            ("oracle_relation", "expected_word_correction_used", True),
        ):
            changed = copy.deepcopy(self.report)
            changed[section][key] = value
            attacks.append(changed)
        changed = copy.deepcopy(self.report)
        changed["claims_not_made"].remove("No native direct output-world memory capture")
        attacks.append(changed)
        changed = copy.deepcopy(self.report)
        changed["identities"]["aex"] = "0" * 64
        attacks.append(changed)
        changed = copy.deepcopy(self.report)
        changed["unexpected"] = True
        attacks.append(changed)
        for attack in attacks:
            self.assertFalse(self.module.validate(attack, live=False))

    def test_proof_census_and_hash_tamper_rejected(self) -> None:
        for key, value in (
            ("adjacent_float_preimage_collisions", 1),
            ("alpha_mismatches", 1),
            ("direct_raw_sha256", "0" * 64),
            ("final_semantic_argb_sha256", "0" * 64),
            ("word_count", 8294399),
        ):
            changed = copy.deepcopy(self.report)
            changed["proof"][key] = value
            self.assertFalse(self.module.validate(changed, live=False))

    def test_no_ae_process_claim_or_launch(self) -> None:
        self.assertIn("No new After Effects execution", self.report["claims_not_made"])
        source = GENERATOR.read_text() + HARNESS.read_text()
        for forbidden in ("AfterFX", "aerender", "DoScriptFile"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
