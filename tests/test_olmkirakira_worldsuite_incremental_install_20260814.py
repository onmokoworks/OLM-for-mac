import copy, importlib.util, json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; TOOL=ROOT/"tools/emulation/audit_olmkirakira_worldsuite_incremental_install_20260814.py"
spec=importlib.util.spec_from_file_location("kira_install_audit",TOOL); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
class InstallAuditTest(unittest.TestCase):
 def test_live(self): m.validate(m.generate())
 def test_report(self): m.validate(json.loads(m.REPORT.read_text()))
 def test_schema_tamper(self):
  r=m.generate(); r["extra"]=1
  with self.assertRaises(RuntimeError): m.validate(r)
 def test_identity_tamper(self):
  r=copy.deepcopy(m.generate()); r["new_binary_sha256"]="0"*64
  with self.assertRaises(RuntimeError): m.validate(r)
if __name__=="__main__": unittest.main()
