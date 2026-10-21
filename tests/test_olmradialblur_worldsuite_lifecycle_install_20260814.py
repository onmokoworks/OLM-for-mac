from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/emulation/audit_olmradialblur_worldsuite_lifecycle_install_20260814.py"
TOOL_SHA256 = "a357f9f5c3b75c3de4fdc94d049c6d8cf3f27e1c718211376810069572bdff37"
SPEC = importlib.util.spec_from_file_location("radial_install_audit", TOOL)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MOD)


class RadialWorldSuiteInstallTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = json.loads(MOD.impl.REPORT.read_text(encoding="utf-8"))

    def test_live_install_validates(self) -> None:
        MOD.impl.validate(self.report)

    def test_tool_identity(self) -> None:
        if TOOL_SHA256 != "PENDING":
            self.assertEqual(hashlib.sha256(TOOL.read_bytes()).hexdigest(), TOOL_SHA256)

    def test_scope_tamper_rejected(self) -> None:
        changed = copy.deepcopy(self.report)
        changed["scope"]["after_effects_launched"] = True
        with self.assertRaises(ValueError):
            MOD.impl.validate(changed)

    def test_identity_tamper_rejected(self) -> None:
        changed = copy.deepcopy(self.report)
        changed["identity_change"]["other_nine_rows_exact"] = False
        with self.assertRaises(ValueError):
            MOD.impl.validate(changed)


if __name__ == "__main__":
    unittest.main()
