from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/emulation/test_olmradialblur_type1_pairwise_source_guard_readiness_20260813.py"
REPORT = ROOT / "refs/conformance/olmradialblur_type1_pairwise_source_guard_readiness_20260813.json"


def module():
    spec = importlib.util.spec_from_file_location("radial_pairwise_readiness", TOOL)
    loaded = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(loaded)
    return loaded


class RadialPairwiseSourceGuardReadinessTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool = module()
        cls.report = json.loads(REPORT.read_text())

    def test_report_validates(self):
        self.tool.validate(self.report)

    def test_source_hash_tamper_rejected(self):
        forged = copy.deepcopy(self.report)
        forged["active_source_sha256"]["PF8_9x7"] = "0" * 64
        with self.assertRaises(RuntimeError):
            self.tool.validate(forged)

    def test_unknown_key_rejected(self):
        forged = copy.deepcopy(self.report); forged["extra"] = True
        with self.assertRaises(RuntimeError):
            self.tool.validate(forged)

    def test_transcript_tamper_rejected(self):
        forged = copy.deepcopy(self.report)
        forged["runs"][0]["lines"][0] = "forged"
        with self.assertRaises(RuntimeError):
            self.tool.validate(forged)

    def test_claim_broadening_rejected(self):
        forged = copy.deepcopy(self.report)
        forged["claim_boundary"]["proven"] = "all Type1 sources"
        with self.assertRaises(RuntimeError):
            self.tool.validate(forged)


if __name__ == "__main__":
    unittest.main()
