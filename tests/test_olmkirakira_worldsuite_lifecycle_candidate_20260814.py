from __future__ import annotations
import copy,hashlib,importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];AUDIT=ROOT/"tools/emulation/audit_olmkirakira_worldsuite_lifecycle_candidate_20260814.py"
REPORT=ROOT/"handoffs/olmkirakira_worldsuite_lifecycle_candidate_20260814/build_identity.json";AUDIT_SHA="8ce7449a3576feb71942e1529954eff5b2d552d4bcce2892841432f5c167b91f"
def load():s=importlib.util.spec_from_file_location("kira_candidate",AUDIT);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class KiraCandidateTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.m=load();cls.r=json.loads(REPORT.read_text())
 def test_identity(self):
  if AUDIT_SHA!="PENDING":self.assertEqual(hashlib.sha256(AUDIT.read_bytes()).hexdigest(),AUDIT_SHA)
 def test_live(self):self.m.validate(self.m.generate());self.m.validate(self.r)
 def test_inventory_tamper(self):
  x=copy.deepcopy(self.r);x["inventory"][0]["sha256"]="0"*64
  with self.assertRaises(AssertionError):self.m.validate(x)
 def test_scope_tamper(self):
  x=copy.deepcopy(self.r);x["scope"]["native_ae"]=True
  with self.assertRaises(AssertionError):self.m.validate(x)
if __name__=="__main__":unittest.main()
