#!/usr/bin/env python3
"""F38 serial current-default campaigns and corpus replay; no expectation writes."""
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
S = ROOT / 'orchestra/state/F38-x86-default-nan-sign'
S = S / ('after' if '--after' in sys.argv else 'before')
S.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / 'tools/fuzz'))
from run import default_worker

env = dict(os.environ, TMPDIR=str(S), TMP=str(S), TEMP=str(S),
           OLM_TEST_JOBS='1', OLM_UCRT_FMA='1', PYTHONDONTWRITEBYTECODE='1')
env['OLM_F38_BASELINE'] = '0' if '--after' in sys.argv else '1'
env.pop('OLM_AEX_WORKER', None)
os.environ.pop('OLM_AEX_WORKER', None)
worker = default_worker()
assert worker == Path.home()/'.cache/olm-emu/worker-F32-deep/aex-guest-worker'
plugins = ['colorkeep', 'olmblur', 'olmcolorkey', 'olmdirectionalblur',
           'olmdistancegradation', 'olmkirakira', 'olmsmoother', 'olmsmoother2',
           'olmtoondilate', 'radialblur']
jobs = []
for corpus in sorted((ROOT/'tests/fuzz_corpus').iterdir()):
    cases = sorted(corpus.glob('*.json')) if corpus.is_dir() else []
    if cases:
        jobs.append((json.loads(cases[0].read_text())['plugin'], corpus.name+'-replay',
                     ['--replay', str(corpus), '--worker', str(worker)]))
jobs += [(p, f'{p}-seed{seed}', ['--seed', str(seed)]) for p in plugins for seed in (1, 31)]
if '--plugin' in sys.argv:
    jobs = [j for j in jobs if j[0] == sys.argv[sys.argv.index('--plugin')+1]]
for plugin, label, extra in jobs:
    report = S/(label+'.json')
    if '--resume' in sys.argv and report.exists() and json.loads(report.read_text()).get('status') in ('complete', 'replay_complete'):
        continue
    cmd = [sys.executable, str(ROOT/'tools/fuzz/run_F38.py'), '--plugin', plugin,
           '--n', '300', '--jobs', '1', '--shrink-attempts', '0',
           '--budget-minutes', '120', '--scratch', str(S/'run'),
           '--report', str(report), '--corpus', str(S/'generated-corpus'), *extra]
    with (S/(label+'.log')).open('w') as log:
        proc = subprocess.run(cmd, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
    print(label, proc.returncode, flush=True)
    if not report.exists():
        raise RuntimeError('Missing report: '+label)
    measured = json.loads(report.read_text())
    expected = 'replay_complete' if '--replay' in extra else 'complete'
    if measured.get('status') != expected:
        raise RuntimeError(f'{label}: {measured.get("status")}; see its log')
