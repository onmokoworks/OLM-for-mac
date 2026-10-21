from __future__ import annotations
import copy, hashlib, importlib.util, json, subprocess, sys, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
GEN=ROOT/"tools/emulation/test_olmtoondilate_same_source_public_paired_replay_20260813.py"
REPORT=ROOT/"refs/conformance/olmtoondilate_same_source_public_paired_replay_20260813.json"
DOC=REPORT.with_suffix(".md")
spec=importlib.util.spec_from_file_location("toon_pair",GEN);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

class ToonPaired(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.report=json.loads(REPORT.read_text())
    def reject(self,fn):
        value=copy.deepcopy(self.report);fn(value)
        with self.assertRaises((RuntimeError,KeyError,IndexError)):mod.validate(value)
    def test_report(self):mod.validate(copy.deepcopy(self.report))
    def test_identity(self):self.reject(lambda r:r["identities"].__setitem__("production_source_sha256","0"*64))
    def test_cell_count(self):self.reject(lambda r:r["paired_cells"].pop())
    def test_cell_order(self):self.reject(lambda r:r["paired_cells"].reverse())
    def test_active_hash_recanonicalized(self):
        def mutate(r):
            r["paired_cells"][0]["shared"]["input_active_sha256"]="0"*64
            r["paired_cells_sha256"]=mod.canonical(r["paired_cells"])
        self.reject(mutate)
    def recanonicalized_cell(self,fn):
        def mutate(r):
            fn(r["paired_cells"][0])
            r["paired_cells_sha256"]=mod.canonical(r["paired_cells"])
        self.reject(mutate)
    def test_payload_recanonicalized(self):self.recanonicalized_cell(lambda r:r["shared"].__setitem__("input_payload_sha256","0"*64))
    def test_layout_recanonicalized(self):self.recanonicalized_cell(lambda r:r["shared"].__setitem__("input_extent",[0,0,7,5]))
    def test_dsy_recanonicalized(self):self.recanonicalized_cell(lambda r:r["shared"].__setitem__("downsample_y",[1,1]))
    def test_both_owner_output_recanonicalized(self):
        self.recanonicalized_cell(lambda r:r["shared"].__setitem__("output_active_sha256","1"*64))
    def test_owner_callback_recanonicalized(self):
        self.recanonicalized_cell(lambda r:r["mac_public_effectmain"]["callbacks"].__setitem__("release_world_suite",0))
    def test_cell_extra_key_recanonicalized(self):self.recanonicalized_cell(lambda r:r.__setitem__("extra",True))
    def test_positive_zero_bits(self):
        def mutate(r):
            r["paired_cells"][0]["shared"]["radius_f64_le"]="0000000000000080"
            r["paired_cells_sha256"]=mod.canonical(r["paired_cells"])
        self.reject(mutate)
    def test_authority_lifecycle(self):self.reject(lambda r:r["paired_cells"][0]["mac_public_effectmain"]["callbacks"].__setitem__("release_world_suite",0))
    def test_extra_pixels(self):self.reject(lambda r:r["smart_pre_relation"].__setitem__("windows_output_flags",0))
    def test_negative_count(self):self.reject(lambda r:r["world_suite_negative_rows"].pop())
    def test_negative_recanonicalized(self):
        def mutate(r):
            r["world_suite_negative_rows"][0]["output_storage_untouched"]=False
            r["world_suite_negative_rows_sha256"]=mod.canonical(r["world_suite_negative_rows"])
        self.reject(mutate)
    def recanonicalized_negative(self,fn):
        def mutate(r):
            fn(r["world_suite_negative_rows"][0])
            r["world_suite_negative_rows_sha256"]=mod.canonical(r["world_suite_negative_rows"])
        self.reject(mutate)
    def test_negative_error_recanonicalized(self):self.recanonicalized_negative(lambda r:r.__setitem__("actual_err",72))
    def test_negative_callback_recanonicalized(self):self.recanonicalized_negative(lambda r:r["callbacks"].__setitem__("acquire_world_suite",2))
    def test_negative_extra_recanonicalized(self):self.recanonicalized_negative(lambda r:r.__setitem__("extra",True))
    def test_negative_drop_recanonicalized(self):self.recanonicalized_negative(lambda r:r.pop("pre_render_lifecycle_exact"))
    def test_gate_extra(self):self.reject(lambda r:r["gates"].__setitem__("extra",True))
    def test_claim_drift(self):self.reject(lambda r:r.__setitem__("claim_boundary",r["claim_boundary"]+" No AEXCompat."))
    def test_extra_field(self):self.reject(lambda r:r.__setitem__("extra",True))
    def test_validate_only_byte_stable(self):
        before=(hashlib.sha256(REPORT.read_bytes()).hexdigest(),hashlib.sha256(DOC.read_bytes()).hexdigest())
        run=subprocess.run([sys.executable,str(GEN),"--validate-only"],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        self.assertEqual(before,(hashlib.sha256(REPORT.read_bytes()).hexdigest(),hashlib.sha256(DOC.read_bytes()).hexdigest()))

if __name__=="__main__":unittest.main()
