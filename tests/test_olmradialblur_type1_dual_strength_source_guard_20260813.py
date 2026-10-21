from __future__ import annotations
import copy, importlib.util, json, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TOOL=ROOT/"tools/emulation/test_olmradialblur_type1_dual_strength_source_guard_20260813.py"
spec=importlib.util.spec_from_file_location("radial_dual_guard",TOOL); mod=importlib.util.module_from_spec(spec)
assert spec.loader; spec.loader.exec_module(mod)

class DualStrengthSourceGuard(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.report=json.loads(mod.REPORT.read_text())
    def test_valid(self): mod.validate(self.report)
    def test_source_tamper(self):
        bad=copy.deepcopy(self.report); bad["active_source_sha256"]["PF32_plain"]="0"*64
        with self.assertRaises(RuntimeError): mod.validate(bad)
    def test_transcript_tamper(self):
        bad=copy.deepcopy(self.report); bad["runs"][1]["lines"][0]="forged"
        with self.assertRaises(RuntimeError): mod.validate(bad)
    def test_claim_tamper(self):
        bad=copy.deepcopy(self.report); bad["claim_boundary"]["proven"]="arbitrary sources"
        with self.assertRaises(RuntimeError): mod.validate(bad)
    def test_unknown_key(self):
        bad=copy.deepcopy(self.report); bad["extra"]=1
        with self.assertRaises(RuntimeError): mod.validate(bad)

if __name__=="__main__": unittest.main()
