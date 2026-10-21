#!/usr/bin/env python3
"""Tamper-close tests for the Smoother public guard closure validator."""
from __future__ import annotations
import copy, importlib.util, json, unittest
from pathlib import Path

SCRIPT=Path(__file__).with_name('test_olmsmoother_public_admission_guard_closure_20260812.py')
SPEC=importlib.util.spec_from_file_location('smoother_guard_closure',SCRIPT)
MOD=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(MOD)

class ClosureTamper(unittest.TestCase):
 def setUp(self):
  self.report=MOD.REPORT.read_bytes();self.doc=MOD.DOC.read_bytes()
 def tearDown(self):
  MOD.REPORT.write_bytes(self.report);MOD.DOC.write_bytes(self.doc)
 def tamper(self,field,value):
  data=json.loads(self.report);data[field]=value
  MOD.REPORT.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
  with self.assertRaises(RuntimeError):MOD.validate_report()
 def test_schema_tamper(self):self.tamper('schema','forged')
 def test_unknown_top_level_tamper(self):self.tamper('extra',{'forged':True})
 def test_oracle_tamper(self):self.tamper('actual_aex_sha256',{'OLMSmoother':'0','OLMSmoother2':'0'})
 def test_case_ids_tamper(self):self.tamper('case_ids',{})
 def test_admission_tamper(self):self.tamper('admission_map',{})
 def test_contract_tamper(self):self.tamper('world_contract',[])
 def test_real_sdk_suite_tamper(self):self.tamper('real_sdk_suite_lifecycle',{})
 def test_claim_tamper(self):self.tamper('claims_not_made',[])
 def test_doc_tamper(self):
  MOD.DOC.write_text('forged\n')
  with self.assertRaises(RuntimeError):MOD.validate_report()

if __name__=='__main__':unittest.main()
