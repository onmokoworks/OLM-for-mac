from __future__ import annotations
import copy, hashlib, importlib.util, json, subprocess, sys, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
GEN=ROOT/'tools/emulation/test_olmsmoother2_case07_public_smart_closure_20260814.py'
REPORT=ROOT/'refs/conformance/olmsmoother2_case07_public_smart_closure_20260814.json'
NOTE=REPORT.with_suffix('.md')

def load():
 spec=importlib.util.spec_from_file_location('case07_public',GEN);assert spec and spec.loader
 mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

class Case07PublicSmart(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.mod=load();cls.data=json.loads(REPORT.read_text())
 def test_fresh_default_and_validate_read_only(self):
  before={p:p.read_bytes() for p in (REPORT,NOTE)}
  for args in ([],['--validate-only']):
   run=subprocess.run([sys.executable,str(GEN),*args],cwd=ROOT,capture_output=True,text=True)
   self.assertEqual(run.returncode,0,run.stdout+run.stderr)
  self.assertEqual(before,{p:p.read_bytes() for p in before})
 def test_exact_case_matrix(self):
  self.assertEqual(len(self.data['cases']),24);self.assertEqual(self.data['contract']['positive_count'],1)
  self.assertEqual(self.data['contract']['negative_count'],23);self.assertTrue(all(x['pass'] for x in self.data['cases']))
 def test_recanonicalized_tamper_rejected(self):
  attacks=[]
  for section,key,value in [('contract','rowbytes',30721),('contract','gamma_value_binary64','0'*16)]:
   d=copy.deepcopy(self.data);d[section][key]=value;attacks.append(d)
  d=copy.deepcopy(self.data);d['cases'][1]['err']=0;attacks.append(d)
  d=copy.deepcopy(self.data);d['cases'][0]['unexpected']=1;attacks.append(d)
  d=copy.deepcopy(self.data);d['claims_not_made'].pop();attacks.append(d)
  d=copy.deepcopy(self.data);d['extra']=1;attacks.append(d)
  for d in attacks:self.assertFalse(self.mod.validate(d,live=False))
 def test_no_ae_tokens(self):
  source=GEN.read_text()+(ROOT/'tools/emulation/olmsmoother2_case07_public_smart_harness_20260814.cpp').read_text()
  for token in ('AfterFX','aerender','DoScriptFile'):self.assertNotIn(token,source)

if __name__=='__main__':unittest.main()
