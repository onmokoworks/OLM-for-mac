from __future__ import annotations
import copy, hashlib, importlib.util, json, subprocess, sys, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TOOL=ROOT/'tools/emulation/audit_olm_hostless_batch4_prepared_install_20260813.py'
REPORT=ROOT/'refs/conformance/olm_hostless_batch4_prepared_install_20260813.json'
TOOL_SHA='da576909e463e646c7e62ead3e089de04c9ca6aa4c6f7a0d02c6dae1ba99a55f'
REPORT_SHA='3a58a47aeab0427103ee516135a145e675992fe5f30dcc2498fa584e49f93a90'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('prepared',TOOL); assert spec and spec.loader
audit=importlib.util.module_from_spec(spec); spec.loader.exec_module(audit)

class Prepared(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.data=json.loads(REPORT.read_text())
 def test_identities(self):self.assertEqual(sha(TOOL),TOOL_SHA);self.assertEqual(sha(REPORT),REPORT_SHA)
 def test_default_read_only(self):
  before=REPORT.read_bytes();subprocess.run([sys.executable,str(TOOL)],cwd=ROOT,check=True);self.assertEqual(REPORT.read_bytes(),before)
 def test_live(self):audit.validate(copy.deepcopy(self.data))
 def test_tamper(self):
  for mutate in (lambda d:d.update(extra=True),lambda d:d['authorities'].update(installer_sha256='0'*64),lambda d:d['plugins']['OLMBlur'].update(installed_backup_full_inventory_exact=False),lambda d:d['prepared_validation'].update(identity_exact=False),lambda d:d.update(after_effects_processes=[1]),lambda d:d['scope'].update(installed=True)):
   changed=copy.deepcopy(self.data);mutate(changed)
   with self.assertRaises((ValueError,RuntimeError)):audit.validate(changed)

if __name__=='__main__':unittest.main()
