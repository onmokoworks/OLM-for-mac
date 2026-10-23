#!/usr/bin/env python3
"""Serial all-plugin campaigns and saved corpora; defaults/corpora are read-only."""
import argparse, json, os, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
S=ROOT/'orchestra/state/F30-oracle-worker-ucrtmath'
workers={
 'default':Path('/Users/onmk/Documents/Codex/2026-10-05/task-3/AEXCompat-containment/guest/target/release/aex-guest-worker'),
 'f29':Path.home()/'.cache/olm-emu/worker-F29-ssenan/aex-guest-worker',
 'f30':Path.home()/'.cache/olm-emu/worker-F30-ucrtmath/aex-guest-worker'}
plugins=['colorkeep','olmblur','olmcolorkey','olmdirectionalblur','olmdistancegradation','olmkirakira','olmsmoother','olmsmoother2','olmtoondilate','radialblur']
S.mkdir(parents=True,exist_ok=True)
env=dict(os.environ,TMPDIR=str(S),TMP=str(S),TEMP=str(S),PYTHONDONTWRITEBYTECODE='1',OLM_TEST_JOBS='1',OLM_UCRT_FMA='1')
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--resume',action='store_true',help='reuse completed reports; default reruns all requested measurements')
parser.add_argument('variants',nargs='*')
args=parser.parse_args()
if any(v not in workers for v in args.variants):parser.error("variants must be default, f29, or f30")
for variant in args.variants or ['default','f29','f30']:
 jobs=[(p,p+'-seed1',[]) for p in plugins]
 for corpus in sorted((ROOT/'tests/fuzz_corpus').iterdir()):
  cases=sorted(corpus.glob('*.json')) if corpus.is_dir() else []
  if cases: jobs.append((json.loads(cases[0].read_text())['plugin'],corpus.name+'-replay',['--replay',str(corpus)]))
 for plugin,label,extra in jobs:
  report=S/f'{variant}-{label}.json'
  if args.resume and report.exists() and json.loads(report.read_text()).get('status') in ('complete','replay_complete'):continue
  cmd=[sys.executable,str(ROOT/'tools/fuzz/run.py'),'--plugin',plugin,'--n','300','--seed','1','--jobs','1','--shrink-attempts','0','--budget-minutes','120','--worker',str(workers[variant]),'--scratch',str(S/variant),'--report',str(report),'--corpus',str(S/f'{variant}-generated-corpus'),*extra]
  with (S/f'{variant}-{label}.log').open('w') as log:
   p=subprocess.run(cmd,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
  print(variant,label,'exit',p.returncode,flush=True)
  if not report.exists():raise RuntimeError('No report')
