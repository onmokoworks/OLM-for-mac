import copy,importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"handoffs/olmblur_pf32_retained_public_universal_candidate_v2_20260813/verify_candidate.py"
S=importlib.util.spec_from_file_location("olmblur_candidate_v2",PATH);M=importlib.util.module_from_spec(S);S.loader.exec_module(M)
class Candidate(unittest.TestCase):
 @classmethod
 def setUpClass(c):c.v=json.loads(M.REPORT.read_text());M.validate(c.v)
 def test_live(self):M.validate(self.v)
 def test_tamper(self):
  v=copy.deepcopy(self.v);v["candidate"]["binary_sha256"]="0"*64
  with self.assertRaises(ValueError):M.validate(v)
if __name__=="__main__":unittest.main()
