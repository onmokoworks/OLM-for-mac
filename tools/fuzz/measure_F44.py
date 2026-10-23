#!/usr/bin/env python3
"""Serial F44 campaigns (two seeds) and all saved corpora; never changes expectations."""
import json
import os
from pathlib import Path
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[2]
S = ROOT/'orchestra/state/F44-integrate-ms-float'
S.mkdir(parents=True, exist_ok=True)
worker = Path.home()/'.cache/olm-emu/worker-F44-msfloat/aex-guest-worker'
env = dict(os.environ, TMPDIR=str(S), TMP=str(S), TEMP=str(S), OLM_TEST_JOBS='1', OLM_UCRT_FMA='1', PYTHONDONTWRITEBYTECODE='1')
plugins = ['colorkeep','olmblur','olmcolorkey','olmdirectionalblur','olmdistancegradation','olmkirakira','olmsmoother','olmsmoother2','olmtoondilate','radialblur']
jobs = [(p, f'{p}-seed{seed}', ['--seed',str(seed)]) for p in plugins for seed in (1,44)]
for corpus in sorted((ROOT/'tests/fuzz_corpus').iterdir()):
    cases = sorted(corpus.glob('*.json')) if corpus.is_dir() else []
    if cases:
        jobs.append((json.loads(cases[0].read_text())['plugin'], corpus.name+'-replay', ['--replay',str(corpus)]))
if '--plugin' in sys.argv:
    selected=sys.argv[sys.argv.index('--plugin')+1]
    jobs=[job for job in jobs if job[0]==selected]
if '--campaigns-only' in sys.argv:
    jobs=[job for job in jobs if not job[1].endswith('-replay')]
before = '--before' in sys.argv
if before: worker = Path.home()/'.cache/olm-emu/worker-F32-deep/aex-guest-worker'
for plugin,label,extra in jobs:
    if before: label = 'before-' + label
    report=S/(label+'.json')
    if '--resume' in sys.argv and report.exists() and json.loads(report.read_text()).get('status') in ('complete','replay_complete'):
        continue
    cmd=[sys.executable,str(ROOT/('tools/fuzz/before_F44.py' if before else 'tools/fuzz/run.py')),'--plugin',plugin,'--n','300','--jobs','1','--shrink-attempts','0','--budget-minutes','120','--worker',str(worker),'--scratch',str(S/('run-before' if before else 'run')),'--report',str(report),'--corpus',str(S/('before-generated-corpus' if before else 'generated-corpus')),*extra]
    with (S/(label+'.log')).open('w') as log:
        proc=subprocess.run(cmd,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
    print(label,proc.returncode,flush=True)
    if not report.exists():
        raise RuntimeError('Missing report: '+label)
