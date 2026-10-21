from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "handoffs/olmdirectionalblur_worldsuite_lifecycle_candidate_20260814"
VALIDATOR = HERE / "test_build_identity.py"
MANIFEST = HERE / "build_identity.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_validator():
    spec = importlib.util.spec_from_file_location("directional_worldsuite_candidate", VALIDATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DirectionalWorldSuiteCandidateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_validator()
        cls.value = json.loads(MANIFEST.read_text())

    def test_external_identities_and_live_validation(self) -> None:
        self.assertEqual(sha256(VALIDATOR), "12a7b956cc45ec211c8c292cc0c712815788a2eb0ae123c90c46f54b29824f8b")
        self.assertEqual(sha256(MANIFEST), "8e75d0a799b7b796c8f2cb63c8553df127ccc87d5868e2b0cb0b72a62b404de6")
        self.assertTrue(self.module.validate(self.value))

    def test_manifest_tamper_fails_closed(self) -> None:
        mutations = [
            lambda v: v.__setitem__("extra", True),
            lambda v: v.__setitem__("source_sha256", "0" * 64),
            lambda v: v.__setitem__("binary_sha256", "0" * 64),
            lambda v: v["bundle_inventory"].__setitem__("Contents/PkgInfo", "0" * 64),
            lambda v: v["evidence"].__setitem__("worldsuite_lifecycle_sha256", "0" * 64),
            lambda v: v["claim_boundary"].__setitem__("installed", True),
            lambda v: v["codesign"].__setitem__("kind", "Developer ID"),
            lambda v: v["minimum_os"].__setitem__("arm64", "26.2"),
        ]
        for mutate in mutations:
            changed = copy.deepcopy(self.value)
            mutate(changed)
            self.assertFalse(self.module.validate(changed))


if __name__ == "__main__":
    unittest.main()
