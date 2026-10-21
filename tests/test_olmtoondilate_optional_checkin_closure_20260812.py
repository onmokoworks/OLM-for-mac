from __future__ import annotations
import copy,hashlib,importlib.util,json,subprocess,sys,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
GEN=ROOT/"tools/emulation/test_olmtoondilate_optional_checkin_closure_20260812.py"
REPORT=ROOT/"refs/conformance/olmtoondilate_optional_checkin_closure_20260812.json"
DOC=REPORT.with_suffix(".md")
spec=importlib.util.spec_from_file_location("toon_optional",GEN);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

class OptionalCheckinRoute(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.value=json.loads(REPORT.read_text())
    def reject(self,fn):
        value=copy.deepcopy(self.value);fn(value)
        with self.assertRaises(RuntimeError):mod.validate(value)
    def test_current(self):mod.validate(copy.deepcopy(self.value))
    def test_source_identity(self):self.reject(lambda r:r["production"].__setitem__("source_sha256","0"*64))
    def test_paired_identity(self):self.reject(lambda r:r["current_authorities"].__setitem__("paired_report_sha256","0"*64))
    def test_negative_identity(self):self.reject(lambda r:r["current_authorities"].__setitem__("negative_report_sha256","0"*64))
    def test_optional_positive(self):self.reject(lambda r:r["current_authorities"].__setitem__("positive_optional_checkin_calls_per_cell",1))
    def test_old_claim_not_restored(self):self.reject(lambda r:r["supersedes"].__setitem__("reason","candidate numerical authority"))
    def test_extra(self):self.reject(lambda r:r.__setitem__("extra",True))
    def test_default_read_only(self):
        before=(hashlib.sha256(REPORT.read_bytes()).hexdigest(),hashlib.sha256(DOC.read_bytes()).hexdigest())
        run=subprocess.run([sys.executable,str(GEN)],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        self.assertEqual(before,(hashlib.sha256(REPORT.read_bytes()).hexdigest(),hashlib.sha256(DOC.read_bytes()).hexdigest()))

if __name__=="__main__":unittest.main()
