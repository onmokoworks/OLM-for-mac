from __future__ import annotations
import copy, importlib.util, json, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "tools/emulation/test_olmradialblur_type1_size_noise_source_guard_20260813.py"
spec = importlib.util.spec_from_file_location("size_noise", PATH); module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
class SizeNoiseGuardTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.report = json.loads(module.REPORT.read_text())
    def test_valid(self): module.validate(self.report)
    def test_source_tamper(self):
        value = copy.deepcopy(self.report); value["active_source_sha256"]["PF32"] = "0" * 64
        with self.assertRaises(RuntimeError): module.validate(value)
    def test_run_tamper(self):
        value = copy.deepcopy(self.report); value["runs"][1]["lines"][0] = "tampered"
        with self.assertRaises(RuntimeError): module.validate(value)
    def test_claim_tamper(self):
        value = copy.deepcopy(self.report); value["claim_boundary"]["proven"] = "all"
        with self.assertRaises(RuntimeError): module.validate(value)
    def test_schema_tamper(self):
        value = copy.deepcopy(self.report); value["extra"] = True
        with self.assertRaises(RuntimeError): module.validate(value)
if __name__ == "__main__": unittest.main()
