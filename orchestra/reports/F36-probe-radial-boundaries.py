#!/usr/bin/env python3
"""Sequential cross-witness checks of the identified Rotation boundary."""
import json
from pathlib import Path
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[2]
SCRATCH = ROOT / 'orchestra/state/F36-fixture-runner-worktree-and-triage'
PROFILES = {
    'ellipse9': ['--ratio','2'],
    'ellipse32': ['--geometry32','--ratio','2'],
    'strength5noise25': ['--strength','5','--noise','25'],
    'offset2noise25': ['--offset-mode','3','--offset','2','--noise','25'],
    'pf16neutral': ['--depth','16'],
    'strength5': ['--strength','5'],
    'pf16strength5': ['--depth','16','--strength','5'],
    'offset2': ['--offset-mode','3','--offset','2'],
    'offset3': ['--offset-mode','3','--offset','3'],
    'offset4': ['--offset-mode','3','--offset','4'],
    'pf16offset2': ['--depth','16','--offset-mode','3','--offset','2'],
    'pf16offset3': ['--depth','16','--offset-mode','3','--offset','3'],
    'outerfade50': ['--outer-fade','50'],
}
rows=[]
for label,extra in PROFILES.items():
    command=[sys.executable,'-B',str(ROOT/'orchestra/reports/F36-bisect-radial.py'),
        '--label',label,*extra,'--revision','f5a74754^1','--revision','f5a74754','--revision','24e8b60d']
    with (SCRATCH/f'boundary-{label}.log').open('w') as log:
        result=subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
    row=dict(label=label,command=command,returncode=result.returncode)
    rows.append(row)
    print(json.dumps(row),flush=True)
    (SCRATCH/'boundary-probes.json').write_text(json.dumps(rows,indent=2)+'\n')
