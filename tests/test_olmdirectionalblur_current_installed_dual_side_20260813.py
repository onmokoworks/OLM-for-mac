from __future__ import annotations
import copy,hashlib,importlib.util,json,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];GEN=ROOT/"tools/emulation/test_olmdirectionalblur_current_installed_dual_side_20260813.py";REPORT=ROOT/"refs/conformance/olmdirectionalblur_current_installed_dual_side_20260813.json";MD=REPORT.with_suffix(".md")
GEN_SHA="e15da8d8825bfef6a9f74837f650abed88557a556a0f88e1d9e003bd85bba638";REPORT_SHA="c22568d5af1f851e6845ac3bb5a24ad8f97e09f9af7b936d5813385ce9c9453e";MD_SHA="e1f52af47a01aa698ec3aacef9af707a2dbd76c0c2dc2b3076c0a473ac5c8fe6"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load():s=importlib.util.spec_from_file_location("directional_installed",GEN);m=importlib.util.module_from_spec(s);assert s.loader;s.loader.exec_module(m);return m
class DirectionalInstalledDualSideTest(unittest.TestCase):
 @classmethod
 def setUpClass(c):c.g=load();c.r=json.loads(REPORT.read_text())
 def reject(self,f):
  r=copy.deepcopy(self.r);f(r)
  with self.assertRaises(RuntimeError):self.g.validate(r)
 def test_live_read_only(self):
  b=(REPORT.read_bytes(),MD.read_bytes());p=subprocess.run([sys.executable,str(GEN)],cwd=ROOT,text=True,capture_output=True);self.assertEqual(p.returncode,0,p.stdout+p.stderr);self.assertEqual(b,(REPORT.read_bytes(),MD.read_bytes()))
 def test_hashes(self):self.assertEqual(sha(GEN),GEN_SHA);self.assertEqual(sha(REPORT),REPORT_SHA);self.assertEqual(sha(MD),MD_SHA)
 def test_relation(self):self.assertEqual(self.r["summary"],self.g.SUMMARY);self.assertEqual(self.r["summary"]["depths"],[8,16,32]);self.assertEqual(self.r["summary"]["architectures"],["arm64","x86_64"]);self.assertEqual(self.r["summary"]["positive_cells_total"],6)
 def test_recanonicalized_transcript_rejected(self):
  def f(r):r["run_lines"][0]+=" altered=1";r["run_sha256"]=hashlib.sha256(("\n".join(r["run_lines"])+"\n").encode()).hexdigest()
  self.reject(f)
 def test_authority_summary_unknown_rejected(self):self.reject(lambda r:r["authorities"].__setitem__("source","0"*64));self.reject(lambda r:r["summary"].__setitem__("positive_cells_total",7));self.reject(lambda r:r.__setitem__("extra",1))
 def test_scope_escalation_rejected(self):self.reject(lambda r:r["scope"].__setitem__("native_after_effects",True));self.reject(lambda r:r["scope"].__setitem__("arbitrary_source_tuple_geometry",True));self.reject(lambda r:r["after_effects_processes"].append("After Effects:1"))
if __name__=="__main__":unittest.main()
