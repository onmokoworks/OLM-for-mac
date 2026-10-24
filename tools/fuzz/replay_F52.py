#!/usr/bin/env python3
"""Replay saved corpora with unchanged default worker/geometry, serially."""
import json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];S=ROOT/'orchestra/state/F52-oracle-downsample-geometry/replay';S.mkdir(parents=True,exist_ok=True)
env=dict(os.environ,TMPDIR=str(S),TMP=str(S),TEMP=str(S),OLM_TEST_JOBS='1',PYTHONDONTWRITEBYTECODE='1')
for directory in sorted((ROOT/'tests/fuzz_corpus').iterdir()):
    cases=sorted(directory.glob('*.json')) if directory.is_dir() else []
    if not cases:continue
    plugin=json.loads(cases[0].read_text())['plugin']
    report=S/(directory.name+'.json')
    if '--resume' in sys.argv and report.exists():continue
    cmd=[sys.executable,str(ROOT/'tools/fuzz/run.py'),'--plugin',plugin,'--jobs','1','--replay',str(directory),'--scratch',str(S/'scratch'),'--report',str(report),'--budget-minutes','30']
    with (S/(directory.name+'.log')).open('w') as log:r=subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT)
    print(directory.name,r.returncode,flush=True)
    if not report.exists():raise RuntimeError('No report: '+directory.name)
