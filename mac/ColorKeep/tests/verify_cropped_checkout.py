"""P04d serial regression campaigns using the retained F53 oracle."""
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
S = ROOT/'orchestra/state/P04d-colorkeep-cropped-checkout'
S.mkdir(parents=True, exist_ok=True)
env = dict(os.environ, TMPDIR=str(S), PYTHONDONTWRITEBYTECODE='1', OLM_TEST_JOBS='1')
worker = Path.home()/'.cache/olm-emu/worker-F53-geom/aex-guest-worker'
campaigns = [('default', ['--seed','1','--n','300'])]
for mode in ('realistic', 'realistic-v2'):
    for seed in (1, 20261025):
        campaigns.append((f'{mode}-{seed}', ['--geometry',mode,'--seed',str(seed),'--n','100']))
for seed in (2026,2027):
    campaigns.append((f'odd-{seed}', ['--geometry','realistic','--seed',str(seed),'--n','150',
                      '--size-sampler','odd-even-v1','--max-size','1920','--size-max-height','1080']))
for name, flags in campaigns:
    cmd = [sys.executable, 'tools/fuzz/run.py','--plugin','colorkeep','--jobs','1',
           '--worker',str(worker),'--shrink-attempts','0','--corpus-max-bytes','0',
           '--scratch',str(S/name),'--report',str(S/(name+'.json')),
           '--corpus',str(S/'generated-corpus'), *flags]
    with (S/(name+'.log')).open('w') as log:
        subprocess.run(cmd, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
    report=json.loads((S/(name+'.json')).read_text())
    print(name, report['status'], report['summary'], flush=True)
    assert report['status']=='complete'
    assert report['summary'].get('smart_exact')==report['requested'], name
