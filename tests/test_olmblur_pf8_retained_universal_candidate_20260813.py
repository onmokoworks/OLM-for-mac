import copy,hashlib,importlib.util,json,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];VER=ROOT/"handoffs/olmblur_pf8_retained_public_universal_candidate_20260813/verify_candidate.py"
SPEC=importlib.util.spec_from_file_location("pf8_candidate",VER);MOD=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(MOD)
class Candidate(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.v=json.loads(MOD.REPORT.read_text());MOD.validate(cls.v)
 def reject(self,fn):
  v=copy.deepcopy(self.v);fn(v)
  with self.assertRaises(ValueError):MOD.validate(v)
 def test_default(self):subprocess.run([sys.executable,str(VER)],cwd=ROOT,check=True)
 def test_verifier_identity(self):self.assertEqual("021a1e1ac7e4a526074f74359299d925aefe2b8cd2100cc7d3fcc65c11b94be7",hashlib.sha256(VER.read_bytes()).hexdigest())
 def test_source(self):self.reject(lambda v:v["source"].__setitem__("sha256","0"*64))
 def test_binary(self):self.reject(lambda v:v["candidate"].__setitem__("binary_sha256","0"*64))
 def test_scope(self):self.reject(lambda v:v["scope"].__setitem__("installed",True))
if __name__=="__main__":unittest.main()
