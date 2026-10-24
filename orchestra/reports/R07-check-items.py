#!/usr/bin/env python3
"""Reproduce R07 checks without changing evidence or reserved Radial fixtures."""
import json, os, subprocess, time, argparse, signal
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
S=ROOT/'orchestra/state/R07-gate-contracts-and-bindings'
MAIN=ROOT.parent.parent
parser=argparse.ArgumentParser();parser.add_argument('--group',choices=['contracts','bindings','f40'],required=True);args=parser.parse_args()
S.mkdir(parents=True,exist_ok=True)
env=dict(os.environ,TMPDIR=str(S),TMP=str(S),TEMP=str(S),PYTHONDONTWRITEBYTECODE='1',OLM_TEST_JOBS='2',OLM_MAIN_ASSETS=str(MAIN),PYTHONPATH=str(ROOT))
r03=json.loads((ROOT/'orchestra/reports/R03-results.json').read_text())
r05=json.loads((ROOT/'orchestra/reports/R05-results.json').read_text())
rows=[r for r in r03['results'] if r['outcome']=='runtime/contract failure' and r['key'] not in ['fixture-162','fixture-163','fixture-164']] if args.group=='contracts' else [dict(key=r['test'],command=r['command']) for r in r05['generic_entries'] if r['test'] in ['tests/test_generic_beta_perf_smoke_runner.py','tests/test_beta_support_documentation.py']]
if args.group=='f40':
 covered={int(r['key'].split('-')[1]) for r in r03['results'] if r['key'].startswith('fixture-') and r['outcome']=='runtime/contract failure'}
 indices={r['index'] for r in json.loads((ROOT/'orchestra/reports/F40-adjudication.json').read_text())['commands']}
 rows=[dict(key=f"fixture-{r['index']:03d}",command=r['command']) for r in r05['fixtures'] if r['index'] in indices and r['index'] not in covered and r['index']<201 and not 152<=r['index']<=181]
results=[]
for i,row in enumerate(rows):
 command=[a.replace(str(MAIN/'worktrees/R03-harness-ucrt-link'),str(ROOT)).replace(str(MAIN/'worktrees/R05-regenerate-stale-bindings'),str(ROOT)) for a in row['command']]
 log=S/f'{args.group}-{i:02d}.log';start=time.monotonic()
 # Some historical runners overwrite their reports; preserve each tracked report.
 assert not subprocess.check_output(['git','diff','--name-only','HEAD','--','refs/conformance'],cwd=ROOT,text=True).strip()
 with log.open('w') as out:
  p=subprocess.Popen(command,cwd=ROOT,env=env,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
  try: code=p.wait(timeout=600)
  except subprocess.TimeoutExpired:
   os.killpg(p.pid,signal.SIGTERM);p.wait();code=124
 for rel in subprocess.check_output(['git','diff','--name-only','HEAD','--','refs/conformance'],cwd=ROOT,text=True).splitlines():
  import shutil
  dest=S/'generated'/args.group/str(i)/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/rel,dest)
  with (ROOT/rel).open('wb') as restored: subprocess.run(['git','show','HEAD:'+rel],cwd=ROOT,stdout=restored,check=True)
 results.append(dict(key=row['key'],command=command,exit=code,seconds=round(time.monotonic()-start,2),log=str(log.relative_to(ROOT))))
 (S/f'{args.group}.json').write_text(json.dumps(results,indent=2)+'\n')
 print(row['key'],code,flush=True)
