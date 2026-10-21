from __future__ import annotations
import copy, importlib.util, json, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "tools/emulation/audit_olmradialblur_type1_source_guard_batch4_install_20260813.py"
spec = importlib.util.spec_from_file_location("audit", PATH); module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
class RadialBatch4InstallTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.report = json.loads(module.REPORT.read_text())
    def test_valid(self): module.validate(self.report)
    def test_install_boundary(self):
        self.assertFalse(self.report["scope"]["after_effects_launched"]); self.assertEqual(self.report["installed"]["old_full_inventory_exact_copies"], ["backup", "pre_swap", "moved_old"])
    def test_tamper(self):
        value = copy.deepcopy(self.report); value["scope"]["after_effects_launched"] = True
        with self.assertRaises(RuntimeError): module.validate(value)
if __name__ == "__main__": unittest.main()
