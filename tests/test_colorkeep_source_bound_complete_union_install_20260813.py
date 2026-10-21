from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "tools/emulation/audit_colorkeep_source_bound_complete_union_install_20260813.py"
REPORT = ROOT / "refs/conformance/colorkeep_source_bound_complete_union_install_20260813.json"


def load_module():
    spec = importlib.util.spec_from_file_location("colorkeep_complete_install", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


class ColorKeepCompleteUnionInstallTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()
        cls.report = json.loads(REPORT.read_text())

    def test_generator_identity(self):
        self.assertEqual(hashlib.sha256(GENERATOR.read_bytes()).hexdigest(),
                         "9f08e025f6a83b2acabb32f95b74b9d6919bc0bab7e63e75df988e638fae28a4")

    def test_live_identity_validates(self):
        self.module.validate(self.report)

    def test_install_and_replay_cardinality(self):
        self.assertEqual(self.report["identity_transition"]["changed_plugins"],
                         {"ColorKeep": ["sha256", "source_bundle", "source_sha256"]})
        self.assertEqual(self.report["scope"]["rollback_copies"], 3)
        self.assertEqual(len(self.report["installed_replay"]["legacy_union"]["architectures"]["arm64"]), 10)
        self.assertEqual(self.report["installed_replay"]["count9_union"]["architectures"]["x86_64"]["rejects"], 136)

    def test_tampering_fails(self):
        mutations = (
            lambda r: r.update(extra=True),
            lambda r: r["scope"].update(after_effects_launched=True),
            lambda r: r["authorities"].update(transaction_sha256="0" * 64),
            lambda r: r["bundles"]["installed"].update(binary_sha256="0" * 64),
            lambda r: r["identity_transition"].update(unchanged_plugins=[]),
            lambda r: r["installed_replay"]["legacy_union"].update(paths_per_slice=9),
            lambda r: r["installed_replay"]["count9_union"]["architectures"]["arm64"].update(rejects=135),
            lambda r: r["preflight"][0].update(plugin_rows=9),
        )
        for mutation in mutations:
            candidate = copy.deepcopy(self.report)
            mutation(candidate)
            with self.assertRaises(RuntimeError):
                self.module.validate(candidate)


if __name__ == "__main__":
    unittest.main()
