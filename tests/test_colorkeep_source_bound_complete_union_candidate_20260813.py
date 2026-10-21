from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "tools/emulation/test_colorkeep_source_bound_complete_union_candidate_20260813.py"
REPORT = ROOT / "refs/conformance/colorkeep_source_bound_complete_union_candidate_20260813.json"


def load_module():
    spec = importlib.util.spec_from_file_location("colorkeep_complete_union", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


class ColorKeepCompleteUnionCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()
        cls.report = json.loads(REPORT.read_text())

    def test_generator_identity_is_pinned_externally(self):
        self.assertEqual(
            hashlib.sha256(GENERATOR.read_bytes()).hexdigest(),
            "32429241a354b1d1e317d515011fe29e568958a23e46f4dbe6b1e2acaf4b993f",
        )

    def test_report_validates_against_live_candidate(self):
        self.module.validate(self.report)

    def test_complete_union_cardinality(self):
        legacy = self.report["legacy_union"]
        self.assertEqual((legacy["paths_per_slice"], len(legacy["architectures"]["arm64"]),
                          len(legacy["architectures"]["x86_64"])), (10, 10, 10))
        self.assertEqual(legacy["source_helper_active_mutation_rejects"], 18)
        self.assertEqual(self.report["count9_union"]["architectures"]["arm64"]["rejects"], 136)
        self.assertEqual(self.report["count9_union"]["architectures"]["x86_64"]["rejects"], 136)

    def test_recanonicalized_tampering_fails(self):
        attacks = []
        for mutate in (
            lambda r: r.update(extra=True),
            lambda r: r["scope"].update(installed=True),
            lambda r: r["candidate"].update(binary_sha256="0" * 64),
            lambda r: r["candidate"]["inventory"][0].update(size=0),
            lambda r: r["legacy_union"].update(paths_per_slice=11),
            lambda r: r["legacy_union"]["architectures"]["arm64"][0].update(active_sha256="0" * 64),
            lambda r: r["count9_union"]["architectures"]["x86_64"].update(rejects=135),
            lambda r: r["authorities"].update(production_source_sha256="0" * 64),
        ):
            candidate = copy.deepcopy(self.report)
            mutate(candidate)
            attacks.append(candidate)
        for candidate in attacks:
            with self.assertRaises(RuntimeError):
                self.module.validate(candidate)


if __name__ == "__main__":
    unittest.main()
