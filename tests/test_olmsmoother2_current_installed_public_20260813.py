from __future__ import annotations
import copy, hashlib, importlib.util, json, subprocess, sys, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
GENERATOR=ROOT/"tools/emulation/test_olmsmoother2_current_installed_public_20260813.py"
REPORT=ROOT/"refs/conformance/olmsmoother2_current_installed_public_20260813.json"; MARKDOWN=REPORT.with_suffix(".md")
GENERATOR_SHA256="3e9a739dafd12be47b376b31e9f4c911f754aff4e32864493fd06fb295219ca6"
REPORT_SHA256="3e1ba25a3f259a8f26ccea21b38c7f4bfc3d63e61881b455e5811711e0810f4f"
MARKDOWN_SHA256="b3082d66f8b9d1989db50f89998a3a557ea14cc12aef7f6a87ab2c71a483d604"
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def load():
 spec=importlib.util.spec_from_file_location("olmsmoother2_installed",GENERATOR); module=importlib.util.module_from_spec(spec); assert spec.loader; spec.loader.exec_module(module); return module
class OLMSmoother2CurrentInstalledPublicTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls): cls.generator=load(); cls.report=json.loads(REPORT.read_text())
 def reject(self,mutation):
  changed=copy.deepcopy(self.report); mutation(changed)
  with self.assertRaises(RuntimeError): self.generator.validate(changed)
 def test_default_live_read_only(self):
  before=(REPORT.read_bytes(),MARKDOWN.read_bytes()); run=subprocess.run([sys.executable,str(GENERATOR)],cwd=ROOT,text=True,capture_output=True)
  self.assertEqual(run.returncode,0,run.stdout+run.stderr); self.assertEqual(before,(REPORT.read_bytes(),MARKDOWN.read_bytes()))
 def test_canonical_hashes(self):
  self.assertEqual(sha(GENERATOR),GENERATOR_SHA256); self.assertEqual(sha(REPORT),REPORT_SHA256); self.assertEqual(sha(MARKDOWN),MARKDOWN_SHA256)
 def test_relation(self): self.assertEqual(self.report["summary"],self.generator.SUMMARY); self.assertEqual(self.report["run_sha256"],self.generator.RUN_SHA256); self.assertEqual(self.report["summary"]["architectures"],["arm64","x86_64"]); self.assertEqual(self.report["summary"]["positive_cells_total"],78); self.assertEqual(self.report["summary"]["new_public_rows_per_slice"],94); self.assertTrue(self.report["scope"]["complete_admission_union"])
 def test_recanonicalized_transcript_rejected(self):
  def mutation(report): report["run_lines"][0]+=" altered=1"; report["run_sha256"]=hashlib.sha256(("\n".join(report["run_lines"])+"\n").encode()).hexdigest()
  self.reject(mutation)
 def test_authority_summary_unknown_rejected(self):
  self.reject(lambda r:r["authorities"].__setitem__("source","0"*64)); self.reject(lambda r:r["summary"].__setitem__("positive_cells_total",5)); self.reject(lambda r:r.__setitem__("extra",True))
 def test_scope_escalation_rejected(self):
  self.reject(lambda r:r["scope"].__setitem__("native_after_effects",True)); self.reject(lambda r:r["scope"].__setitem__("complete_admission_union",False)); self.reject(lambda r:r["scope"].__setitem__("arbitrary_source_or_tuple",True)); self.reject(lambda r:r["after_effects_processes"].append("After Effects:1"))
if __name__=="__main__": unittest.main()
