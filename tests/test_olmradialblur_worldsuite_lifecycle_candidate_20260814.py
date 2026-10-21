from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/emulation/audit_olmradialblur_worldsuite_lifecycle_candidate_20260814.py"
TOOL_SHA256 = "928c30d152fca8ae36ce5894c112a781ad2ffb3592728c3a71a5dbe4d799ffc7"
SPEC = importlib.util.spec_from_file_location("radial_candidate", TOOL)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MOD)


class RadialWorldSuiteCandidateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = json.loads(MOD.REPORT.read_text(encoding="utf-8"))

    def test_live_candidate(self) -> None:
        MOD.validate(self.report)

    def test_tool_identity(self) -> None:
        if TOOL_SHA256 != "PENDING":
            self.assertEqual(hashlib.sha256(TOOL.read_bytes()).hexdigest(), TOOL_SHA256)

    def test_inventory_tamper_rejected(self) -> None:
        changed = copy.deepcopy(self.report)
        changed["bundle"]["inventory"][0]["bytes"] += 1
        changed["bundle"]["inventory_sha256"] = MOD.canonical_inventory(changed["bundle"]["inventory"])
        with self.assertRaises(AssertionError):
            MOD.validate(changed)

    def test_scope_escalation_rejected(self) -> None:
        changed = copy.deepcopy(self.report)
        changed["scope"]["installed"] = True
        with self.assertRaises(AssertionError):
            MOD.validate(changed)

    def test_unknown_key_rejected(self) -> None:
        changed = copy.deepcopy(self.report)
        changed["extra"] = True
        with self.assertRaises(AssertionError):
            MOD.validate(changed)


if __name__ == "__main__":
    unittest.main()
