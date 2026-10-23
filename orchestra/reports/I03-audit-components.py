#!/usr/bin/env python3
"""Retain release component audits even when the aggregate stops at an absent archive."""
import hashlib, importlib.util, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];S=ROOT/'orchestra/state/I03-integration-check'
spec=importlib.util.spec_from_file_location('i03_release',ROOT/'scripts/run_olm_release_gate_20260806.py')
gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
manifest=json.loads(gate.MANIFEST.read_text())
result={'boundary':'Diagnostic component calls; not an aggregate release PASS or a new native AE run.'}
for name,call in [('host_smoke',lambda:gate.validate_current_host_smoke(manifest)),('installed',gate.installed_gate),('parameter_ui',gate.parameter_ui_gate),('windows_boundary',gate.windows_boundary_gate)]:
    try:result[name]=call()
    except Exception as exc:result[name]={'exception':type(exc).__name__,'message':str(exc)}
intake=json.loads(gate.WINDOWS_BOUNDARY_INTAKE.read_text());assets={}
for field in ('contract_archive','return_archive'):
    local=ROOT/intake[field];main=ROOT.parent.parent/intake[field]
    def sha(path):
        if not path.is_file():return None
        with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
    assets[field]={'worktree_path':str(local),'worktree_sha256':sha(local),'main_path':str(main),'main_sha256':sha(main),'expected_sha256':intake[field+'_sha256']}
result['read_only_asset_audit']=assets
(S/'release-component-audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v.get('state',v.get('exception')) if isinstance(v,dict) else len(v) for k,v in result.items() if k!='boundary'},sort_keys=True))
