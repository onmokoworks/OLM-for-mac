from __future__ import annotations
import copy,hashlib,importlib.util,json,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
GEN=ROOT/"tools/emulation/test_olmsmoother_v1_current_installed_admission_union_20260813.py";REPORT=ROOT/"refs/conformance/olmsmoother_v1_current_installed_admission_union_20260813.json";MD=REPORT.with_suffix(".md")
GEN_SHA="a0b70c8cad308344375ef6a2ca0909b7ca76d7d19725bf11c5e6df3b40d2955e";REPORT_SHA="34d66834c08ff265b8760ec84f2b2595023ca3ed9120582726f97e3d10c3963a";MD_SHA="4b399a5411a5d2b6dfe7dd9071dec9f0ebb859b536f0557343425b6f5450796c"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load():s=importlib.util.spec_from_file_location("v1union",GEN);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class V1InstalledAdmissionUnion(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.g=load();cls.r=json.loads(REPORT.read_text())
 def reject(self,fn):d=copy.deepcopy(self.r);fn(d);self.assertRaises(RuntimeError,self.g.validate,d)
 def test_default_live_read_only(self):
  before=REPORT.read_bytes(),MD.read_bytes();p=subprocess.run([sys.executable,str(GEN)],cwd=ROOT,text=True,capture_output=True);self.assertEqual(p.returncode,0,p.stdout+p.stderr);self.assertEqual(before,(REPORT.read_bytes(),MD.read_bytes()))
 def test_hashes(self):self.assertEqual((sha(GEN),sha(REPORT),sha(MD)),(GEN_SHA,REPORT_SHA,MD_SHA))
 def test_complete_union(self):self.assertEqual(self.r["summary"]["positive_cells_total"],134);self.assertTrue(self.r["scope"]["complete_admission_union"]);self.assertFalse(self.r["scope"]["native_after_effects"])
 def test_authority_and_unknown_rejected(self):self.reject(lambda d:d["authorities"].__setitem__("source","0"*64));self.reject(lambda d:d.__setitem__("extra",1))
 def test_recanonicalized_transcript_rejected(self):
  def mutate(d):d["run_lines"][1]+=" altered";d["run_sha256"]=hashlib.sha256(("\n".join(d["run_lines"])+"\n").encode()).hexdigest()
  self.reject(mutate)
 def test_scope_escalation_rejected(self):self.reject(lambda d:d["scope"].__setitem__("native_after_effects",True));self.reject(lambda d:d["scope"].__setitem__("arbitrary_source_or_tuple",True));self.reject(lambda d:d["scope"].__setitem__("complete_admission_union",False))
if __name__=="__main__":unittest.main()
