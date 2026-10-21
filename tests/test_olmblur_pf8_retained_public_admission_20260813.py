import copy,hashlib,importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];PATH=ROOT/"tools/emulation/test_olmblur_pf8_retained_public_admission_20260813.py"
SPEC=importlib.util.spec_from_file_location("pf8_admission",PATH);MOD=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(MOD)
class TestPF8Admission(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.v=json.loads(MOD.REPORT.read_text());MOD.validate(cls.v)
 def reject(self,fn):
  v=copy.deepcopy(self.v);fn(v)
  with self.assertRaises(ValueError):MOD.validate(v)
 def test_counts(self):self.assertEqual((12,24,744),(self.v["summary"]["cells"],self.v["summary"]["positive_controls"],self.v["summary"]["negative_controls"]))
 def test_generator_identity(self):self.assertEqual("80b75ea4d6ccf1ad659cb199a9d68850115d5858002e06951586943f12a0d4b7",hashlib.sha256(PATH.read_bytes()).hexdigest())
 def test_extra(self):self.reject(lambda v:v.__setitem__("extra",1))
 def test_cell(self):self.reject(lambda v:v["cells"][0].__setitem__("active_output_sha256","0"*64))
 def test_run_recanonicalized(self):
  def m(v):v["run_lines"][0]=v["run_lines"][0].replace("exact=1","exact=0");v["run_sha256"]=hashlib.sha256(("\n".join(v["run_lines"])+"\n").encode()).hexdigest()
  self.reject(m)
 def test_claim(self):self.reject(lambda v:v.__setitem__("claim_boundary","broader"))
if __name__=="__main__":unittest.main()
