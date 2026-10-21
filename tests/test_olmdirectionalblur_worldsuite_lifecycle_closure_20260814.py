import copy,hashlib,importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];TOOL=ROOT/"tools/emulation/test_olmdirectionalblur_worldsuite_lifecycle_closure_20260814.py"
spec=importlib.util.spec_from_file_location("dblur_worldsuite",TOOL);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class DirectionalWorldSuiteTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.report=json.loads(m.REPORT.read_text())
 def test_live(self):m.validate(m.generate())
 def test_report(self):m.validate(self.report)
 def test_row_tamper(self):
  v=copy.deepcopy(self.report);v["rows"][0]["get"]=1
  with self.assertRaises(AssertionError):m.validate(v)
 def test_scope_tamper(self):
  v=copy.deepcopy(self.report);v["claims"]["native_ae"]=True
  with self.assertRaises(AssertionError):m.validate(v)
 def test_unknown_key(self):
  v=copy.deepcopy(self.report);v["extra"]=1
  with self.assertRaises(AssertionError):m.validate(v)
if __name__=="__main__":unittest.main()
