from __future__ import annotations

import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / "handoffs/olmblur_pf16_worker_sources_public_universal_candidate_20260813/verify_candidate.py"
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


OLD = load("blur_worker_historical", VERIFIER)
CURRENT = load("blur_worker_current", CURRENT_VERIFIER)


class Candidate(unittest.TestCase):
    def test_historical_artifact_pins(self) -> None:
        self.assertEqual(sha(VERIFIER), "18f6e941697ea88be4062d53b2f4ce1a0ee998ef26c21d751250405e8311a85c")
        self.assertEqual(sha(REPORT), "274eff56d5ae8dd70826dd0fa78b17e9983247d49be95c7e4cd88b31ac616037")

    def test_historical_candidate_rejects_current_source_drift(self) -> None:
        saved = json.loads(REPORT.read_text())
        self.assertEqual(saved["authorities"]["source"]["sha256"], "cd9aafec4dd2d8c57a85279232a5ccd62e74b9978fc1b2ee07e32678e3a380ea")
        with self.assertRaises(ValueError):
            OLD.validate(saved)

    def test_current_superseding_candidate_validates(self) -> None:
        CURRENT.validate(json.loads(CURRENT_REPORT.read_text()))


if __name__ == "__main__":
    unittest.main()
