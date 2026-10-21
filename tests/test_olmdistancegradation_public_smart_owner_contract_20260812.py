import copy, importlib.util, json, subprocess, sys, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
GEN=ROOT/"tools/emulation/test_olmdistancegradation_public_smart_owner_contract_20260812.py"
REPORT=ROOT/"refs/conformance/olmdistancegradation_public_smart_owner_contract_20260812.json"

def module():
    spec=importlib.util.spec_from_file_location("dg_public_contract",GEN);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);return m

class DistanceGradationPublicSmartOwnerContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.m=module();cls.report=json.loads(REPORT.read_text())
    def test_validate_only(self):
        r=subprocess.run([sys.executable,str(GEN),"--validate-only"],cwd=ROOT,text=True,capture_output=True)
        self.assertEqual(r.returncode,0,r.stderr)
    def test_report(self):self.m.validate_report(copy.deepcopy(self.report))
    def rejected(self,mutate):
        value=copy.deepcopy(self.report);mutate(value)
        with self.assertRaises(AssertionError):self.m.validate_report(value)
    def test_identity_tamper(self):self.rejected(lambda r:r.__setitem__("aex_sha256","0"*64))
    def test_worker_checkout_tamper(self):self.rejected(lambda r:r.__setitem__("aexcompat_checkout_head","0"*40))
    def test_worker_build_revision_tamper(self):self.rejected(lambda r:r.__setitem__("worker_build_revision","1"*40))
    def test_selector_tamper(self):self.rejected(lambda r:r["actual_public_owner"].__setitem__("selector","PF_Cmd_RENDER (0x0b)"))
    def test_chain_tamper(self):self.rejected(lambda r:r["actual_public_owner"]["chain"].pop())
    def test_field_word_tamper(self):self.rejected(lambda r:r["natural_public_trace"].__setitem__("post_ipp_field_sha256","1"*64))
    def test_public_selector_tamper(self):self.rejected(lambda r:r["natural_public_trace"]["selectors"].remove("SMART_RENDER"))
    def test_matrix_one_away(self):self.rejected(lambda r:r["bounded_matrix"].__setitem__("pf32_exact",31))
    def test_mode5_public_count_tamper(self):self.rejected(lambda r:r["production_public_contract"].__setitem__("pf32_mode5_positive_cases",7))
    def test_power_fail_closed_count_tamper(self):self.rejected(lambda r:r["production_public_contract"].__setitem__("pf32_power_fail_closed_cases",7))
    def test_power_oracle_tamper(self):self.rejected(lambda r:r["power_oracle_boundary"].__setitem__("native_windows_ucrt_capture_available",True))
    def test_lifecycle_tamper(self):self.rejected(lambda r:r["production_public_contract"].__setitem__("parameter_checkins",11))
    def test_exception_cleanup_tamper(self):self.rejected(lambda r:r["production_public_contract"].__setitem__("exception_cleanup",False))
    def test_alpha_bits_tamper(self):self.rejected(lambda r:r["production_public_contract"].__setitem__("canonical_alpha_bits",False))
    def test_color_suite_tamper(self):self.rejected(lambda r:r["production_public_contract"].__setitem__("color_suite_error_propagation",False))
    def test_boundary_tamper(self):self.rejected(lambda r:r["not_promoted"].remove("unlisted PF32 Smart tuple or geometry"))
    def test_source_has_exact_guards(self):
        s=(ROOT/"mac/OLMDistanceGradation/OLMDistanceGradation.cpp").read_text()
        self.assertIn("is_admitted_pf32_smart_exported_matrix",s)
        self.assertIn("p.interp_mode == INTERP_POWER",s)
        self.assertIn("input_format != expected_format || output_format != expected_format",s)
        self.assertIn("param_checked_out[i]",s)
        self.assertIn("checkin_layer_pixels(in_data->effect_ref, DG_INPUT)",s)

if __name__=="__main__":unittest.main()
