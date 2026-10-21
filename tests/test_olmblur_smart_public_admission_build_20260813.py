from __future__ import annotations

import hashlib
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / "handoffs/olmblur_smart_public_admission_macos11_project_20260813/verify_candidate.py"
REPORT = ROOT / "handoffs/olmblur_smart_public_admission_macos11_project_20260813/build_identity.json"
CURRENT_VERIFIER = ROOT / "handoffs/olmblur_retained_public_universal_candidate_v4_20260813/verify_candidate.py"
CURRENT_REPORT = CURRENT_VERIFIER.parent / "build_identity.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


spec = importlib.util.spec_from_file_location("blur_build_verify", VERIFIER)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

current_spec = importlib.util.spec_from_file_location("blur_current_build_verify", CURRENT_VERIFIER)
assert current_spec and current_spec.loader
current_module = importlib.util.module_from_spec(current_spec)
current_spec.loader.exec_module(current_module)


class OLMBlurCandidateBuildTest(unittest.TestCase):
    def test_verifier_and_report_identities(self):
        self.assertEqual(sha256(VERIFIER), "2f10be27d1d163897e57919dc0e9ee3e9820f98c27f03578a414df4f7f37ec59")
        self.assertEqual(sha256(REPORT), "1d4ab147557ca06889bb1a02ec76b536bea29b40d1fba8e84e19710d9c027510")

    def test_historical_candidate_is_explicitly_superseded(self):
        historical = json.loads(REPORT.read_text())
        self.assertEqual(historical["authorities"]["source"]["sha256"], "ec0e502eb88c45770e8582f179035a4c1da72bb7e26d3ca3a00a30b835320489")
        self.assertEqual(historical["candidate"]["binary_sha256"], "5893faeaf19d55bb4db6f42eb4c21915c94ad8fe2b945e2002c890d79131c48b")
        with self.assertRaises(ValueError):
            module.validate(historical)

    def test_current_superseding_candidate_validates(self):
        current_module.validate(json.loads(CURRENT_REPORT.read_text()))


if __name__ == "__main__":
    unittest.main()
