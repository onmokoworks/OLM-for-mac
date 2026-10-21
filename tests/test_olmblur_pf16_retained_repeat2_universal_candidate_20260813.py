from __future__ import annotations

import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / "handoffs/olmblur_pf16_retained_repeat2_public_universal_candidate_20260813/verify_candidate.py"
REPORT = VERIFIER.parent / "build_identity.json"
CURRENT_VERIFIER = ROOT / "handoffs/olmblur_pf16_legacy_retained_public_universal_candidate_20260813/verify_candidate.py"
CURRENT_REPORT = CURRENT_VERIFIER.parent / "build_identity.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


SPEC = importlib.util.spec_from_file_location("blur_repeat2_candidate", VERIFIER)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)
CURRENT_SPEC = importlib.util.spec_from_file_location("blur_legacy_current", CURRENT_VERIFIER)
CURRENT_MODULE = importlib.util.module_from_spec(CURRENT_SPEC)
assert CURRENT_SPEC.loader is not None
CURRENT_SPEC.loader.exec_module(CURRENT_MODULE)


class Candidate(unittest.TestCase):
    def test_external_pins(self) -> None:
        self.assertEqual(sha(VERIFIER), "749cd51828bdc9823eb9426589f375b94bd0db5b3f074fde04ec06e76a8a974c")
        self.assertEqual(sha(REPORT), "b5c6c0cc73cb7bf95f5c7c77862d5a0bd104f0fba7c4da772772a53069c5f399")

    def test_historical_candidate_is_superseded(self) -> None:
        data = json.loads(REPORT.read_text())
        self.assertEqual(len(data["compiled_inputs"]), 29)
        self.assertEqual(data["authorities"]["source"]["sha256"], "c0c90d1a3e3e2579b2b6fd83d5a02892e164bc7b1d64de02d3ece21dcc8b4fe7")
        with self.assertRaises(ValueError):
            MODULE.validate(data)

    def test_current_superseding_candidate_validates(self) -> None:
        CURRENT_MODULE.validate(json.loads(CURRENT_REPORT.read_text()))


if __name__ == "__main__":
    unittest.main()
