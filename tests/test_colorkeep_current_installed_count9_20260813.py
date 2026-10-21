from __future__ import annotations
import copy,hashlib,importlib.util,json,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];GEN=ROOT/"tools/emulation/test_colorkeep_current_installed_count9_20260813.py";REPORT=ROOT/"refs/conformance/colorkeep_current_installed_count9_20260813.json";MD=REPORT.with_suffix(".md")
GEN_SHA="8c5afa370e73536a0566c789f1b46a18866e5fc7aa6eee48de6bf7aaa126d273";REPORT_SHA="ce057af28546ef49c71b31c5bfad7e03c45a9eb49222abef7f563dcb0d98a5a3";MD_SHA="71b6ce5fc8a54e8a9736cece5af0ce0189d6e656606f04a5deda40c66fc3e47b"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load():s=importlib.util.spec_from_file_location("ck_installed",GEN);m=importlib.util.module_from_spec(s);assert s.loader;s.loader.exec_module(m);return m
class ColorKeepInstalledCount9Test(unittest.TestCase):
 @classmethod
 def setUpClass(c):c.g=load();c.r=json.loads(REPORT.read_text())
 def reject(self,f):
  r=copy.deepcopy(self.r);f(r)
  with self.assertRaises(RuntimeError):self.g.validate(r)
 def test_live_read_only(self):
  b=(REPORT.read_bytes(),MD.read_bytes());p=subprocess.run([sys.executable,str(GEN)],cwd=ROOT,text=True,capture_output=True);self.assertEqual(p.returncode,0,p.stdout+p.stderr);self.assertEqual(b,(REPORT.read_bytes(),MD.read_bytes()))
 def test_hashes(self):self.assertEqual(sha(GEN),GEN_SHA);self.assertEqual(sha(REPORT),REPORT_SHA);self.assertEqual(sha(MD),MD_SHA)
 def test_relation(self):self.assertEqual(self.r["summary"],self.g.SUMMARY);self.assertEqual(self.r["summary"]["architectures"],["arm64","x86_64"]);self.assertEqual(self.r["summary"]["public_paths_total"],10);self.assertEqual(self.r["negative"]["arm64"]["rejects"],136);self.assertEqual(self.r["negative"]["x86_64"]["rejects"],136)
 def test_owner_tamper_rejected(self):self.reject(lambda r:r["owner_rows"][0].__setitem__("raw_sha256","0"*64))
 def test_authority_summary_unknown_rejected(self):self.reject(lambda r:r["authorities"].__setitem__("installed_binary","0"*64));self.reject(lambda r:r["summary"].__setitem__("public_paths_total",11));self.reject(lambda r:r.__setitem__("extra",1))
 def test_scope_escalation_rejected(self):self.reject(lambda r:r["scope"].__setitem__("native_after_effects",True));self.reject(lambda r:r["scope"].__setitem__("arbitrary_source_palette_tuple",True));self.reject(lambda r:r["after_effects_processes"].append("After Effects:1"))
if __name__=="__main__":unittest.main()
