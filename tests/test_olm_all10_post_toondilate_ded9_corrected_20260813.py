import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RUNNER=ROOT/"scripts/run_olm_all10_post_toondilate_ded9_corrected_20260813.py"
PAYLOAD=ROOT/"scripts/ae_host_all10_post_toondilate_ded9_corrected_20260813.jsx"
CONTRACT=ROOT/"refs/conformance/olm_all10_post_toondilate_ded9_corrected_contract_20260813.json"
EXPECTED_RUNNER_SHA256="2246fb4b50929c948386a2e4b1fc8e9bd153d7e34768e44c2ee9b7a6ae501f70"
EXPECTED_CONTRACT_SHA256="bd55cf886b2f823eacb8a3e836184edbf3f089742e36c6d98b3193b694404767"
OLD={
 ROOT/"refs/conformance/olm_all10_post_toondilate_ded9_fresh_ae_smoke_raw_20260813.json":"17a728f155c292a45b4c1ed83fcc9ba2e0f7d72785732c97eec8780a8f4d0e0e",
 ROOT/"refs/conformance/olm_all10_post_toondilate_ded9_fresh_ae_smoke_20260813.json":"055820bf760d8c31d627e352c0fb87d11ecf263804f1bc3f8dcbc51c33c1972b",
 ROOT/"handoffs/olm_all10_post_toondilate_ded9_fresh_ae_smoke_20260813.invocation-receipt.json":"ed52902307f2e098c46dfb1343ac4105d3067657ac4d8a5a8001b2f71abaae7b",
}
spec=importlib.util.spec_from_file_location("corrected",RUNNER);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

BASE_TEST=ROOT/"tests/test_olm_all10_current_install_fresh_ae_smoke_20260812.py"
base_spec=importlib.util.spec_from_file_location("base_smoke_contract_fixture",BASE_TEST)
base_test=importlib.util.module_from_spec(base_spec);base_spec.loader.exec_module(base_test)

def corrected_synthetic():
 summary,raw=base_test.synthetic()
 for owner in (summary["plugins"],raw["plugins"],raw["ae_return"]["plugins"]):
  for row in owner:
   row["numerical_render_supported"]=None
   row["numerical_render_assessment"]="not_assessed"
  toon=next(row for row in owner if row["plugin"]=="OLMToonDilate")
  toon["host_smoke_expectation"]="disabled_host_frame_render"
  toon["effect_enabled_host_frame_attempted"]=False
  toon["effect_enabled_host_frame_succeeded"]=False
  toon["effect_disabled_during_host_frame"]=True
  if "effect_enabled_during_render" in toon: toon["effect_enabled_during_render"]=False
 summary["claim_boundary"]=raw["claim_boundary"]=mod.CLAIM_BOUNDARY
 raw["ae_return"]["claim_boundary"]=mod.CLAIM_BOUNDARY
 summary["corrected_contract"]=raw["corrected_contract"]=mod.corrected_contract()
 summary["toondilate_numerical_authorities"]=mod.numerical_authorities()
 summary["raw_report"]={"path":str(mod.RAW.relative_to(ROOT)),"sha256":"synthetic"}
 return summary,raw

class Contract(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  if hashlib.sha256(RUNNER.read_bytes()).hexdigest()!=EXPECTED_RUNNER_SHA256:
   raise AssertionError("corrected runner identity drift")
  if hashlib.sha256(CONTRACT.read_bytes()).hexdigest()!=EXPECTED_CONTRACT_SHA256:
   raise AssertionError("corrected contract manifest identity drift")

 def test_failed_attempt_is_immutable_and_never_reused(self):
  for path,want in OLD.items(): self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),want)
  self.assertNotEqual(mod.RAW, next(iter(OLD)))
  self.assertNotEqual(mod.SUMMARY, list(OLD)[1])
  self.assertNotEqual(mod.RECEIPT, list(OLD)[2])
  self.assertTrue(mod.validate_failed_attempt(mod.failed_attempt_evidence()))
  self.assertTrue(mod.validate_superseded_host(mod.superseded_host_authority()))
  self.assertNotEqual(
   mod.superseded_host_authority()["historical_identity_sha256"],
   mod.superseded_host_authority()["current_identity_sha256"],
  )

 def test_corrected_enable_contract_and_authorities(self):
  self.assertEqual(mod.ENABLED_HOST_FRAME_PLUGINS,{"OLMBlur","OLMDirectionalBlur"})
  text=PAYLOAD.read_text();self.assertIn("oldSpec",text);self.assertIn("newSpec",text)
  self.assertIn("text.split(oldSpec).length !== 2",text)
  self.assertIn("text.split(oldClaim).length !== 2",text)
  self.assertIn("Numerical behavior is not assessed by this AE smoke.",text)
  self.assertIn("disabled before generic saveFrameToPng",mod.CLAIM_BOUNDARY)
  self.assertTrue(mod.validate_authorities(mod.numerical_authorities()))
  self.assertTrue(mod.validate_dependencies(mod.execution_dependencies()))
  self.assertTrue(mod.validate_contract(mod.corrected_contract()))
  self.assertTrue(mod.validate_contract_report())
  self.assertTrue(mod.validate_failed_attempt(mod.failed_attempt_evidence()))

 def test_default_is_read_only_and_exact_paths_are_absent(self):
  self.assertTrue(mod.outputs_absent())
  before={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in OLD}
  contract_before=hashlib.sha256(CONTRACT.read_bytes()).hexdigest()
  result=subprocess.run([sys.executable,str(RUNNER)],cwd=ROOT,capture_output=True,text=True)
  self.assertEqual(result.returncode,0,result.stdout+result.stderr)
  value=json.loads(result.stdout)
  self.assertEqual(value["status"],"ready_read_only")
  self.assertTrue(value["outputs_absent"])
  self.assertEqual(value["contract"],mod.corrected_contract())
  self.assertEqual(before,{p:hashlib.sha256(p.read_bytes()).hexdigest() for p in OLD})
  self.assertEqual(contract_before,hashlib.sha256(CONTRACT.read_bytes()).hexdigest())

 def test_end_to_end_corrected_synthetic_and_recanonicalized_tamper(self):
  summary,raw=corrected_synthetic()
  self.assertTrue(mod.validate_summary_data(summary,raw))
  mutations=(
   lambda s,r:next(x for x in s["plugins"] if x["plugin"]=="OLMToonDilate").update(effect_enabled_host_frame_attempted=True),
   lambda s,r:next(x for x in r["ae_return"]["plugins"] if x["plugin"]=="OLMToonDilate").update(effect_enabled_during_render=True),
   lambda s,r:s["corrected_contract"].update(enabled_host_frame_plugins=["OLMBlur","OLMDirectionalBlur","OLMToonDilate"]),
   lambda s,r:r["corrected_contract"]["execution_dependencies"]["base_python_runner"].update(sha256="0"*64),
   lambda s,r:s["toondilate_numerical_authorities"]["same_source_paired_exact12"].update(sha256="0"*64),
   lambda s,r:(s.update(claim_boundary="pixel exact"),r.update(claim_boundary="pixel exact")),
   lambda s,r:r["ae_return"].update(claim_boundary="host claim drift"),
   lambda s,r:next(x for x in r["ae_return"]["plugins"] if x["plugin"]=="OLMToonDilate").update(numerical_render_supported=False),
   lambda s,r:next(x for x in s["plugins"] if x["plugin"]=="OLMToonDilate").update(numerical_render_assessment="unsupported"),
  )
  for mutation in mutations:
   bad_summary,bad_raw=copy.deepcopy(summary),copy.deepcopy(raw)
   mutation(bad_summary,bad_raw)
   self.assertFalse(mod.validate_summary_data(bad_summary,bad_raw))

 def test_authority_tamper_rejected(self):
  value=mod.numerical_authorities()
  for mutate in (
   lambda x:x.update(extra=True),
   lambda x:x.update(classification="ae_pixel_exact"),
   lambda x:x["same_source_paired_exact12"].update(sha256="0"*64),
   lambda x:x["same_source_paired_exact12"].update(case_count=13),
   lambda x:x["public_admission_negative"].update(row_count=575),
  ):
   bad=copy.deepcopy(value);mutate(bad);self.assertFalse(mod.validate_authorities(bad))

 def test_dependency_and_contract_tamper_rejected(self):
  value=mod.execution_dependencies()
  for mutate in (
   lambda x:x.update(extra=True),
   lambda x:x["base_python_runner"].update(sha256="0"*64),
   lambda x:x["base_jsx_payload"].update(path="wrong.jsx"),
   lambda x:x["accepted_installed_identity"].update(sha256="0"*64),
   lambda x:x["toondilate_post_install_identity"].update(sha256="0"*64),
  ):
   bad=copy.deepcopy(value);mutate(bad);self.assertFalse(mod.validate_dependencies(bad))
  value=mod.corrected_contract();value["raw_report"]="refs/conformance/wrong.json"
  self.assertFalse(mod.validate_contract(value))

 def test_persisted_adapter_preserves_actual_corrected_host_return(self):
  summary,raw=corrected_synthetic()
  seen={}
  original=mod._validate_persisted
  def fake(value_summary,value_raw,value_path):
   seen["raw"]=value_raw
   return True
  mod._validate_persisted=fake
  try:
   self.assertTrue(mod.validate_persisted_summary(summary,raw,mod.RAW))
  finally:
   mod._validate_persisted=original
  returned=seen["raw"]["ae_return"]["plugins"]
  self.assertTrue(all(row["numerical_render_supported"] is None for row in returned))
  self.assertTrue(all(row["numerical_render_assessment"]=="not_assessed" for row in returned))

if __name__=="__main__":unittest.main()
