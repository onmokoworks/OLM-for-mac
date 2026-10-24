#!/usr/bin/env python3
"""Verify the refreshed metadata and unchanged strict consumers."""
import json,os,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
S=ROOT/'orchestra/state/R05-regenerate-stale-bindings'
S.mkdir(parents=True,exist_ok=True)
PY=str(ROOT.parent.parent/'tools/emulation/.venv/bin/python3')
env=dict(os.environ,TMPDIR=str(S),TMP=str(S),TEMP=str(S),OLM_TEST_JOBS='2',PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(ROOT))
rows=[]
for name,args in (
    ('matrix',['refs/scripts/audit_olmblur_pf32_formal_worker_matrix_20260805.py']),
    ('owner-validate',['tools/emulation/test_olmblur_pf16_worker_sources_exported_public_owner_20260813.py','--validate-only']),
    ('owner-tests',['tests/test_olmblur_pf16_worker_sources_exported_public_owner_20260813.py','-v']),
    ('path-tests',['tests/test_release_archive_resolution_R05.py']),
):
    command=[PY,'-B',*args];start=time.monotonic()
    with (S/f'focused-{name}.log').open('w') as out:
        proc=subprocess.run(command,cwd=ROOT,env=env,stdout=out,stderr=subprocess.STDOUT)
    rows.append(dict(name=name,command=command,exit=proc.returncode,seconds=round(time.monotonic()-start,2)))
(S/'focused.json').write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps(rows,indent=2))
raise SystemExit(0 if all(r['exit']==0 for r in rows) else 1)
