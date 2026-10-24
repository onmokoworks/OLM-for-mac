#!/usr/bin/env python3
"""Run every unchanged consumer/tamper suite for the three refreshed reports."""
import json,os,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];S=ROOT/'orchestra/state/R07-gate-contracts-and-bindings';S.mkdir(parents=True,exist_ok=True)
env=dict(os.environ,TMPDIR=str(S),TMP=str(S),TEMP=str(S),OLM_TEST_JOBS='2',PYTHONDONTWRITEBYTECODE='1')
py=str(ROOT.parent.parent/'tools/emulation/.venv/bin/python3');rows=[]
for index,name in [(12,'7x5'),(18,'retained_tuples'),(20,'legacy_retained')]:
 for offset,directory in enumerate(['tools/emulation','tests']):
  command=[py,'-B',str(ROOT/directory/f'test_olmblur_pf16_{name}_exported_public_owner_20260813.py')]
  log=S/f'blur-after-{index+offset:03d}.log';start=time.monotonic()
  with log.open('w') as out:p=subprocess.run(command,cwd=ROOT,env=env,stdout=out,stderr=subprocess.STDOUT)
  rows.append(dict(key=f'fixture-{index+offset:03d}',command=command,exit=p.returncode,seconds=round(time.monotonic()-start,2),log=str(log.relative_to(ROOT))))
  print(rows[-1]['key'],p.returncode,flush=True)
(S/'blur-after.json').write_text(json.dumps(rows,indent=2)+'\n')
raise SystemExit(any(r['exit'] for r in rows))
