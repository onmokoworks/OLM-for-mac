from __future__ import annotations
import copy,hashlib,importlib.util,json,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
GEN=ROOT/"tools/emulation/test_olmdistancegradation_current_installed_mode5_20260813.py";REPORT=ROOT/"refs/conformance/olmdistancegradation_current_installed_mode5_20260813.json";MD=REPORT.with_suffix(".md")
GEN_SHA="d810d2fea5bdf59869bd5e3aeb34bff8f66414c2e7280f45ed2e3675f3bfc1b1";REPORT_SHA="98f3b2ecc66a1cb56e105fb7697dca46b1e654f8b66ae3a0596166bced1b2ceb";MD_SHA="adb62c5756a75c354398697bb3888e82554e0ef31f3666762ca1adaa53918a6d"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load():
 s=importlib.util.spec_from_file_location("dg_installed_mode5",GEN);m=importlib.util.module_from_spec(s);assert s.loader;s.loader.exec_module(m);return m
class DistanceInstalledMode5Test(unittest.TestCase):
 @classmethod
 def setUpClass(c):c.g=load();c.r=json.loads(REPORT.read_text())
 def reject(self,f):
  r=copy.deepcopy(self.r);f(r)
  with self.assertRaises(RuntimeError):self.g.validate(r)
 def test_live_read_only(self):
  before=(REPORT.read_bytes(),MD.read_bytes());p=subprocess.run([sys.executable,str(GEN)],cwd=ROOT,text=True,capture_output=True);self.assertEqual(p.returncode,0,p.stdout+p.stderr);self.assertEqual(before,(REPORT.read_bytes(),MD.read_bytes()))
 def test_hashes(self):self.assertEqual(sha(GEN),GEN_SHA);self.assertEqual(sha(REPORT),REPORT_SHA);self.assertEqual(sha(MD),MD_SHA)
 def test_boundary(self):self.assertEqual(self.r["summary"],self.g.SUMMARY);self.assertFalse(self.r["scope"]["native_windows_ucrt_powf"]);self.assertEqual(self.r["summary"]["architectures"],["arm64","x86_64"]);self.assertEqual(self.r["summary"]["mode5_positive_cells_total"],12);self.assertEqual(self.r["summary"]["power_fail_closed_cells_total"],16)
 def test_recanonicalized_transcript_rejected(self):
  def f(r):r["run_lines"][0]+=" altered=1";r["run_sha256"]=hashlib.sha256(("\n".join(r["run_lines"])+"\n").encode()).hexdigest()
  self.reject(f)
 def test_authority_summary_unknown_rejected(self):self.reject(lambda r:r["authorities"].__setitem__("source","0"*64));self.reject(lambda r:r["summary"].__setitem__("mode5_positive_cells_total",13));self.reject(lambda r:r.__setitem__("extra",1))
 def test_scope_escalation_rejected(self):self.reject(lambda r:r["scope"].__setitem__("native_after_effects",True));self.reject(lambda r:r["scope"].__setitem__("native_windows_ucrt_powf",True));self.reject(lambda r:r["after_effects_processes"].append("After Effects:1"))
if __name__=="__main__":unittest.main()
