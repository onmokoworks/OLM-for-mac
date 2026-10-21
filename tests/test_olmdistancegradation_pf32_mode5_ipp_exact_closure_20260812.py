import copy,importlib.util,json,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];GEN=ROOT/"tools/emulation/test_olmdistancegradation_pf32_mode5_ipp_exact_closure_20260812.py";REPORT=ROOT/"refs/conformance/olmdistancegradation_pf32_mode5_ipp_exact_closure_20260812.json"
def module():
 s=importlib.util.spec_from_file_location("dg_mode5_exact",GEN);m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m);return m
class Closure(unittest.TestCase):
 @classmethod
 def setUpClass(c):c.m=module();c.report=json.loads(REPORT.read_text())
 def reject(c,f):
  p=copy.deepcopy(c.report);f(p)
  with c.assertRaises(AssertionError):c.m.validate(p)
 def test_validate(c):c.m.validate(copy.deepcopy(c.report))
 def test_validate_only(c):
  r=subprocess.run([sys.executable,str(GEN),"--validate-only"],cwd=ROOT,text=True,capture_output=True);c.assertEqual(r.returncode,0,r.stderr)
 def test_six_count(c):c.reject(lambda p:p["six_aexcompat_diagnostic_cells"].pop())
 def test_six_hash(c):c.reject(lambda p:p["six_aexcompat_diagnostic_cells"][0].__setitem__("actual_exported_raw_sha256","0"*64))
 def test_guard(c):c.reject(lambda p:p["six_aexcompat_diagnostic_cells"][1].__setitem__("guards_intact",False))
 def test_trace(c):c.reject(lambda p:p["natural_public_trace"]["suite_requests"].pop())
 def test_error(c):c.reject(lambda p:p["natural_public_trace"].__setitem__("render_error",1))
 def test_retained(c):c.reject(lambda p:p["matrix_summary"].__setitem__("exact_admitted",57))
 def test_counter(c):c.reject(lambda p:p["field_mechanism"]["counterfactuals"]["superseded_lut_early_spatial_fused"].__setitem__("different_words",36))
 def test_build(c):c.reject(lambda p:p["field_mechanism"]["builds"]["production_o0"].__setitem__("raw_exact",False))
 def test_compiler(c):c.reject(lambda p:p["compiler_proof"].__setitem__("canonical_fused_op_count",1))
 def test_assembly_hash(c):c.reject(lambda p:p["compiler_proof"].__setitem__("canonical_assembly_sha256","0"*64))
 def test_flags(c):c.reject(lambda p:p["compiler_proof"]["flags"].pop())
 def test_padding(c):c.reject(lambda p:p["public_contract"].__setitem__("padding_preserved",False))
 def test_power_boundary(c):c.reject(lambda p:p["bounded_admission"].__setitem__("power_requires_native_windows_ucrt_capture",False))
 def test_marker(c):c.reject(lambda p:p["public_contract"].__setitem__("marker","bad"))
 def test_admission(c):c.reject(lambda p:p["bounded_admission"].__setitem__("width",18))
 def test_boundary(c):c.reject(lambda p:p["not_promoted"].pop())
if __name__=="__main__":unittest.main()
