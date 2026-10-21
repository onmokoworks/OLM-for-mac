from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/emulation/test_olmradialblur_worldsuite_lifecycle_closure_20260814.py"
TOOL_SHA256 = "1db8f1f86ade9fc1ec85930d113e3464bd1cb818f962ddf902189fcd6f38da65"
SPEC = importlib.util.spec_from_file_location("radial_worldsuite", TOOL)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MOD)


class RadialWorldSuiteLifecycleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = json.loads(MOD.REPORT.read_text(encoding="utf-8"))

    def test_report_validates(self) -> None:
        MOD.validate(self.report)

    def test_generator_identity(self) -> None:
        if TOOL_SHA256 != "PENDING":
            self.assertEqual(hashlib.sha256(TOOL.read_bytes()).hexdigest(), TOOL_SHA256)

    def test_rows_recanonicalization_rejected(self) -> None:
        changed = copy.deepcopy(self.report)
        changed["rows"][0]["release"] = 0
        changed["rows_sha256"] = MOD.canonical_rows(changed["rows"])
        with self.assertRaises(AssertionError):
            MOD.validate(changed)

    def test_scope_escalation_rejected(self) -> None:
        changed = copy.deepcopy(self.report)
        changed["claims"]["native_ae"] = True
        with self.assertRaises(AssertionError):
            MOD.validate(changed)

    def test_unknown_key_rejected(self) -> None:
        changed = copy.deepcopy(self.report)
        changed["extra"] = True
        with self.assertRaises(AssertionError):
            MOD.validate(changed)


if __name__ == "__main__":
    unittest.main()
