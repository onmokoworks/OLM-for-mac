import copy
import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "tools/emulation/test_olmsmoother2_pf8_legacy12_public_closure_20260814.py"
GENERATOR_SHA256 = "20922fbd0f3899da32043f1b4f1c319fe25fb7975ac04be788686f2ddc6c7da8"

spec = importlib.util.spec_from_file_location("pf8_legacy12", GENERATOR)
module = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(module)


class PF8Legacy12ClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(module.REPORT.read_text())

    def test_live_report_and_external_generator_identity(self):
        self.assertEqual(hashlib.sha256(GENERATOR.read_bytes()).hexdigest(), GENERATOR_SHA256)
        self.assertTrue(module.validate(self.data))

    def test_unknown_keys_fail_closed(self):
        changed = copy.deepcopy(self.data)
        changed["extra"] = True
        self.assertFalse(module.validate(changed))
        changed = copy.deepcopy(self.data)
        changed["cases"][0]["extra"] = True
        self.assertFalse(module.validate(changed))

    def test_case_identity_and_paired_hash_tamper_fail_closed(self):
        changed = copy.deepcopy(self.data)
        changed["cases"][0]["direct_argb8_sha256"], changed["cases"][1]["direct_argb8_sha256"] = (
            changed["cases"][1]["direct_argb8_sha256"], changed["cases"][0]["direct_argb8_sha256"])
        self.assertFalse(module.validate(changed))
        changed = copy.deepcopy(self.data)
        changed["cases"][0]["windows_effect_decoded_argb8_sha256"] = "0" * 64
        self.assertFalse(module.validate(changed))

    def test_public_matrix_tamper_fails_closed(self):
        changed = copy.deepcopy(self.data)
        changed["public_cases"][0]["name"] = "case00"
        self.assertFalse(module.validate(changed))
        changed = copy.deepcopy(self.data)
        changed["public_negative_count"] = 33
        self.assertFalse(module.validate(changed))

    def test_dependency_and_claim_tamper_fails_closed(self):
        changed = copy.deepcopy(self.data)
        changed["dependencies"]["manifest"]["sha256"] = "f" * 64
        self.assertFalse(module.validate(changed))
        changed = copy.deepcopy(self.data)
        changed["claims_not_made"] = []
        self.assertFalse(module.validate(changed))


if __name__ == "__main__":
    unittest.main()
