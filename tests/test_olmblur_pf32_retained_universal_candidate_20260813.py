import json,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];HANDOFF=ROOT/"handoffs/olmblur_pf32_retained_public_universal_candidate_20260813";VER=HANDOFF/"verify_candidate.py"
class TestCandidate(unittest.TestCase):
 def test_live_candidate(self):subprocess.run([sys.executable,str(VER)],cwd=ROOT,check=True)
 def test_scope_and_closed_schema(self):
  v=json.loads((HANDOFF/"build_identity.json").read_text())
  self.assertEqual(set(v),{"schema","status","source","authorities","candidate","scope"})
  self.assertEqual(v["scope"],{"installed":False,"after_effects_launched":False,"native_runtime_pixel_claim":False,"developer_id_or_notarization":False})
if __name__=="__main__":unittest.main()
