"""Smoother unit baseline/final; all scratch stays inside this ticket."""
import os, subprocess, sys, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
S=ROOT/'orchestra/state/P07c-smoother-threading'/sys.argv[1]
S.mkdir(parents=True,exist_ok=True)
env=dict(os.environ,TMPDIR=str(S),TMP=str(S),TEMP=str(S),OLM_TEST_JOBS='1',PYTHONDONTWRITEBYTECODE='1')
rows=[]
for p in sorted((ROOT/'tests').glob('test_olmsmoother*.py')):
    if p.name.startswith('test_olmsmoother2'):continue
    for mode in ['--classes-module']+(['--module'] if '\ndef test_' in p.read_text() else []):
        with (S/(p.stem+mode+'.log')).open('w') as log:
            r=subprocess.run([sys.executable,str(ROOT/'orchestra/reports/P05c-evidence/functions.py'),mode,str(p),str(S)],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
        rows.append(dict(file=p.name,mode=mode,returncode=r.returncode))
(S/'summary.json').write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps(rows))
