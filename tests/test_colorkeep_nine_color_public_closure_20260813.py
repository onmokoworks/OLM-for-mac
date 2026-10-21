from __future__ import annotations
import copy, hashlib, importlib.util, json, subprocess, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
GEN=ROOT/"tools/emulation/test_colorkeep_nine_color_public_closure_20260813.py"
REPORT=ROOT/"refs/conformance/colorkeep_nine_color_public_closure_20260813.json"
spec=importlib.util.spec_from_file_location("ck9",GEN); module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class ColorKeepNineClosure(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.report=json.loads(REPORT.read_text())
    def test_report(self): module.validate(copy.deepcopy(self.report))
    def rejected(self,fn):
        value=copy.deepcopy(self.report);fn(value)
        with self.assertRaises((RuntimeError,KeyError,IndexError)): module.validate(value)
    def test_identity(self): self.rejected(lambda r:r["identity"].__setitem__("aex_sha256","0"*64))
    def test_oracle_hash(self): self.rejected(lambda r:r["oracle"]["depths"]["PF16"].__setitem__("output_active","0"*64))
    def test_exported_owner(self): self.rejected(lambda r:r["oracle"]["exported_smart_owner"][2].__setitem__("smart_render_complete",False))
    def test_exported_suite(self): self.rejected(lambda r:r["oracle"]["exported_smart_owner"][0].__setitem__("suite_requests",[]))
    def test_smart_static_owner(self): self.rejected(lambda r:r["oracle"]["smart_static_anchors"].__setitem__("pixel_owner","checkin +0x8"))
    def test_path(self): self.rejected(lambda r:r["public_paths"][0].__setitem__("color_conversions",100))
    def test_lifecycle(self): self.rejected(lambda r:r["public_paths"][4].__setitem__("smart_layer_checkin",1))
    def test_negative(self): self.rejected(lambda r:r["negative"].__setitem__("rejects",135))
    def test_negative_digest(self): self.rejected(lambda r:r["negative"].__setitem__("cases_sha256","0"*64))
    def test_inactive_tail_case(self):
        self.rejected(lambda r: next(row for row in r["negative"]["cases"] if row["path"]=="Smart" and row["depth"]=="PF8" and row["case"]=="inactive_tail_first").__setitem__("return","nonzero"))
    def test_format_case(self):
        self.rejected(lambda r: next(row for row in r["negative"]["cases"] if row["path"]=="Smart" and row["depth"]=="PF32" and row["case"]=="output_format").__setitem__("iterate_hits",1))
    def test_classic_pf32_case(self):
        self.rejected(lambda r:r["negative"]["cases"].__delitem__(next(i for i,row in enumerate(r["negative"]["cases"]) if row["path"]=="Classic" and row["depth"]=="PF32")))
    def test_negative_category_evidence(self):
        self.rejected(lambda r:r["negative"]["category_evidence"]["smart_inactive_tail_first_last"].__setitem__("callback_counts",[10,9,10]))
    def test_claim(self): self.rejected(lambda r:r.__setitem__("claim_boundary","arbitrary source"))
    def test_field_injection(self): self.rejected(lambda r:r.__setitem__("extra",True))
    def test_candidate_arch(self): self.rejected(lambda r:r["candidate"].__setitem__("architectures",["arm64"]))
    def test_candidate_log(self): self.rejected(lambda r:r["candidate"].__setitem__("build_log_sha256","0"*64))
    def test_default_validate_is_byte_stable(self):
        before=hashlib.sha256(REPORT.read_bytes()).hexdigest()
        run=subprocess.run(["python3",str(GEN)],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        self.assertEqual(hashlib.sha256(REPORT.read_bytes()).hexdigest(),before)

if __name__=="__main__": unittest.main()
