from __future__ import annotations

import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "handoffs/olmdirectionalblur_smart_cleanup_universal_candidate_20260813"
VALIDATOR = HERE / "test_build_identity.py"
MANIFEST = HERE / "build_identity.json"
EXECUTABLE = HERE / "Product/OLMDirectionalBlur.plugin/Contents/MacOS/OLMDirectionalBlur"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class DirectionalSmartCleanupCandidate(unittest.TestCase):
    def test_external_identities_and_live_validation(self) -> None:
        self.assertEqual(sha(VALIDATOR), "5c964d0f3194761222655a82b367640e49e1dc30d82ad3719aa893600d5bd1da")
        self.assertEqual(sha(MANIFEST), "aa16e1cb0586f2192c730e98b50ab7cd3405690b92ade9acf318034891788398")
        self.assertEqual(sha(EXECUTABLE), "371c3b624c42d81d67f0e140f14f75d23dcfba302fbca716407902046d2cd0f0")
        spec = importlib.util.spec_from_file_location("directional_cleanup_build", VALIDATOR)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader if spec else None)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)
        self.assertTrue(module.validate(json.loads(MANIFEST.read_text())))


if __name__ == "__main__":
    unittest.main()
