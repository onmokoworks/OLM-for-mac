from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / "tools/emulation/test_olmdirectionalblur_current_installed_internal_owner_boundary_20260814.py"
REPORT = ROOT / "refs/conformance/olmdirectionalblur_current_installed_internal_owner_boundary_20260814.json"
GEN_SHA256 = "2d357c3f94ef710742d0af7386f17914b988139ca439b8089573478b7d484e49"


def load_module():
    spec = importlib.util.spec_from_file_location("dblur_installed_owner_boundary", GEN)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


class InstalledOwnerBoundaryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module(); cls.report = json.loads(REPORT.read_text())

    def test_generator_pin(self) -> None:
        self.assertEqual(hashlib.sha256(GEN.read_bytes()).hexdigest(), GEN_SHA256)

    def test_live_report(self) -> None:
        self.assertTrue(self.module.validate(self.report))

    def test_recanonicalized_claim_tamper(self) -> None:
        changed = copy.deepcopy(self.report)
        changed["scope"]["windows_exported_smart_for_all_fifteen_dual_cells"] = False
        self.assertFalse(self.module.validate(changed, live=False))

    def test_identity_tamper(self) -> None:
        changed = copy.deepcopy(self.report); changed["identities"]["installed_binary_sha256"] = "0" * 64
        self.assertFalse(self.module.validate(changed, live=False))

    def test_installed_runtime_tamper(self) -> None:
        changed = copy.deepcopy(self.report)
        changed["installed_runtime"]["transcript_lines"][0] = changed["installed_runtime"]["transcript_lines"][0].replace("PASS=1", "PASS=0")
        self.assertFalse(self.module.validate(changed, live=False))


if __name__ == "__main__":
    unittest.main()
