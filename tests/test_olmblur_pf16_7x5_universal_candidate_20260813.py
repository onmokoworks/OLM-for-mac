from __future__ import annotations

import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / "handoffs/olmblur_pf16_7x5_public_universal_candidate_20260813/verify_candidate.py"
REPORT = VERIFIER.parent / "build_identity.json"
CURRENT_VERIFIER = ROOT / "handoffs/olmblur_pf16_legacy_retained_public_universal_candidate_20260813/verify_candidate.py"
CURRENT_REPORT = CURRENT_VERIFIER.parent / "build_identity.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


OLD = load("blur_7x5_historical", VERIFIER)
CURRENT = load("blur_7x5_current", CURRENT_VERIFIER)


class Candidate(unittest.TestCase):
    def test_historical_artifact_pins(self) -> None:
        self.assertEqual(sha(VERIFIER), "9e2d91e6e15b1b245250704d2d2b40c15ed92a325cb121e8dda64e18d870995e")
        self.assertEqual(sha(REPORT), "c62661da660399525b7fad3eeaa422e4c63568c94e5190ae77f252f202e48502")

    def test_historical_candidate_rejects_current_source_drift(self) -> None:
        saved = json.loads(REPORT.read_text())
        self.assertEqual(saved["authorities"]["source"]["sha256"], "c79ba706c09043dbf2ec062590eb7f67f0d5b7c201a9be2f3579c00bdc89b3ce")
        with self.assertRaises(ValueError):
            OLD.validate(saved)

    def test_current_superseding_candidate_validates(self) -> None:
        CURRENT.validate(json.loads(CURRENT_REPORT.read_text()))


if __name__ == "__main__":
    unittest.main()
