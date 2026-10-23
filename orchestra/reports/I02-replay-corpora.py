#!/usr/bin/env python3
"""Read-only corpus replay; use each saved hash-bound worker, two jobs."""
import json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SCRATCH=ROOT/'orchestra/state/I02-integration-finish'
rows=[]
for corpus in sorted((ROOT/'tests/fuzz_corpus').iterdir()):
    if not corpus.is_dir(): continue
    files=sorted(corpus.glob('*.json'))
    plugin=json.loads(files[0].read_text())['plugin'] if files else corpus.name
    report=SCRATCH/f'corpus-{corpus.name}.json'
    cmd=[sys.executable,'-B',str(ROOT/'tools/fuzz/run.py'),'--plugin',plugin,'--replay',str(corpus),'--jobs','2','--budget-minutes','30','--scratch',str(SCRATCH/'replay'),'--report',str(report)]
    with (SCRATCH/f'corpus-{corpus.name}.log').open('w') as log:
        rc=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,cwd=ROOT).returncode
    data=json.loads(report.read_text()) if report.exists() else {}
    replays=data.get('replays',[])
    row=dict(corpus=corpus.name,command=cmd,exit=rc,saved=len(files),replayed=len(replays),matches=sum(bool(r['matches_saved']) for r in replays),status=data.get('status'))
    rows.append(row)
    print(json.dumps(row),flush=True)
    (SCRATCH/'corpus-summary.json').write_text(json.dumps(rows,indent=2)+'\n')
