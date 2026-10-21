#!/usr/bin/env python3
"""Post-install identity and rollback audit for the four-plugin batch."""

from __future__ import annotations

import argparse, copy, hashlib, importlib.util, json, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
INSTALLER=ROOT/'scripts/install_olm_hostless_batch4_20260813.py'
INSTALLER_SHA='9c585ad852e114bff25bc144d32fd79e442df7cc507e20f871350526e40d678f'
INSTALLER_UNIT=ROOT/'tests/test_olm_hostless_batch4_transactional_installer_20260813.py'
INSTALLER_UNIT_SHA='41fcd540a2c5d1cc07e1ba88775bf3b5dbca946df7fea6c09e64321b8287e698'
IDENTITY_SHA='426dce713a9595157fe4c9fa3731c464e4ef10afd5db269335a12fa4b38beccc'
TRANSACTION_SHA='984a2c2766b76d9a729a71cbb9ce2bfa5662b6cfa1d4c682f5c40399bf168304'
REPORT=ROOT/'refs/conformance/olm_hostless_batch4_incremental_install_20260813.json'
DOC=REPORT.with_suffix('.md')
DOC_TEXT='''# Four-plugin incremental install

Verdict: `PASS_BATCH4_INSTALLED_IDENTITY_AND_ROLLBACK_CLOSED_PENDING_ONE_AE_SMOKE`.

OLMBlur, OLMSmoother, OLMSmoother2, and OLMColorKey are installed from their reviewed Universal macOS 11 candidates. Candidate and installed full bundle inventories are exact. For every plugin the old bundle is retained in three inventory-exact copies: `installed_backup`, `pre_swap_original`, and `moved_old`.

Only the four target identity rows and the two top-level timestamps changed; the other six rows are byte-semantic exact. Two all-ten preflights are byte-identical, report ten unique Universal strictly signed bundles, and observe no After Effects process. This is an installed identity closure only; the single batched AE smoke and formal gate remain pending.
'''

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def canonical(v:object)->bytes:return (json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=True)+'\n').encode()
def load():
 spec=importlib.util.spec_from_file_location('batch4_post_installer',INSTALLER);assert spec and spec.loader
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def generate()->dict:
 if sha(INSTALLER)!=INSTALLER_SHA or sha(INSTALLER_UNIT)!=INSTALLER_UNIT_SHA:raise RuntimeError('installer authority drift')
 m=load()
 if m.artifact_state()!='installed' or sha(m.IDENTITY)!=IDENTITY_SHA or sha(m.TRANSACTION)!=TRANSACTION_SHA:raise RuntimeError('installed transaction drift')
 before=json.loads(m.PRE_IDENTITY.read_text());after=json.loads(m.IDENTITY.read_text())
 b={r['plugin']:r for r in before['plugins']};a={r['plugin']:r for r in after['plugins']};targets=set(m.PLUGINS)
 if any(a[k]!=b[k] for k in a if k not in targets):raise RuntimeError('non-target identity changed')
 if {k for k in a if a[k]!=b[k]}!=targets:raise RuntimeError('target identity set drift')
 top={k for k in after if k!='plugins' and after[k]!=before[k]}
 if top!={'accepted_at','installed_after'}:raise RuntimeError(f'top identity drift: {top}')
 plugins={}
 for name,spec in m.PLUGINS.items():
  p=m.paths(name);candidate=m.verify_bundle(name,spec['candidate'],spec['new'],require_macos11=True)
  installed=m.verify_bundle(name,p['installed'],spec['new'],require_macos11=True)
  if installed['manifest']!=candidate['manifest']:raise RuntimeError(f'candidate/install drift: {name}')
  old=[]
  for key in ('backup','pre_swap','moved_old'):
   row=m.verify_bundle(name,p[key],spec['old'],require_macos11=False)
   if row['manifest']!=m.verify_bundle(name,p['backup'],spec['old'],require_macos11=False)['manifest']:raise RuntimeError(f'old copy drift: {name}/{key}')
   old.append(key)
  plugins[name]={'old_sha256':spec['old'],'new_sha256':spec['new'],'candidate_installed_full_inventory_exact':True,'old_full_inventory_exact_copies':old}
 cmd=[sys.executable,str(ROOT/'scripts/preflight_olm_all_universal_installs_20260805.py')]
 passes=[]
 for _ in range(2):
  result=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True)
  if result.returncode!=2:raise RuntimeError(f'preflight rc: {result.returncode}')
  data=json.loads(result.stdout)
  if data['status']!='ae_not_running' or data['after_effects'] or len(data['bundles'])!=10 or not all(r['bundle_count']==1 and r['sha256_exact'] and r['universal_exact'] and r['codesign_exact'] for r in data['bundles']):raise RuntimeError('preflight contract')
  passes.append(result.stdout.encode())
 if passes[0]!=passes[1]:raise RuntimeError('preflight passes differ')
 if m.ae_pids():raise RuntimeError('After Effects running')
 return {'schema':'olm.hostless-batch4-incremental-install/1','status':'PASS_BATCH4_INSTALLED_IDENTITY_AND_ROLLBACK_CLOSED_PENDING_ONE_AE_SMOKE',
  'authorities':{'installer_sha256':INSTALLER_SHA,'installer_unit_sha256':INSTALLER_UNIT_SHA,'transaction_sha256':TRANSACTION_SHA,'pre_identity_sha256':m.EXPECTED_PRE_IDENTITY,'post_identity_sha256':IDENTITY_SHA},
  'plugins':plugins,'identity_change':{'target_plugins':sorted(targets),'other_six_rows_exact':True,'top_level_changed_fields':sorted(top)},
  'all10_preflight':{'passes':2,'returncode':2,'status':'ae_not_running','stdout_sha256':hashlib.sha256(passes[0]).hexdigest(),'byte_identical':True,'exact_bundles':10},
  'after_effects_processes':[],'scope':{'installed':True,'rollback_copies_per_plugin':3,'after_effects_launched':False,'batched_smoke_complete':False,'formal_gate_complete':False}}

def validate(d:object)->None:
 if not isinstance(d,dict) or set(d)!={'schema','status','authorities','plugins','identity_change','all10_preflight','after_effects_processes','scope'}:raise ValueError('schema')
 if d!=generate():raise ValueError('live state drift')
 if d['scope']!={'installed':True,'rollback_copies_per_plugin':3,'after_effects_launched':False,'batched_smoke_complete':False,'formal_gate_complete':False}:raise ValueError('scope')
 if DOC.read_text()!=DOC_TEXT:raise ValueError('doc')

def main()->int:
 p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args();d=generate()
 if a.write:REPORT.write_bytes(canonical(d));DOC.write_text(DOC_TEXT)
 if not REPORT.is_file() or not DOC.is_file():raise SystemExit('missing; use --write')
 before=REPORT.read_bytes();validate(json.loads(before))
 if before!=canonical(d) or REPORT.read_bytes()!=before:raise SystemExit('not read-only exact')
 print(d['status']);return 0
if __name__=='__main__':raise SystemExit(main())
