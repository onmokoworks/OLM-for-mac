#!/usr/bin/env python3
"""Replay every Blur corpus with each corpus's hash-bound worker, serially."""
import os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
S=ROOT/'orchestra/state/P02h-blur-geometry'
E=ROOT/'orchestra/reports/P02h-evidence'
os.environ.update(TMPDIR=str(S),TMP=str(S),TEMP=str(S),PYTHONDONTWRITEBYTECODE='1',OLM_TEST_JOBS='1')
failed=False
for corpus in sorted((ROOT/'tests/fuzz_corpus').glob('olmblur*')):
 cmd=[sys.executable,'tools/fuzz/run.py','--plugin','olmblur','--jobs','1','--replay',str(corpus),'--scratch',str(S/'replay'),'--report',str(E/('replay-'+corpus.name+'.json'))]
 with (S/('replay-'+corpus.name+'.log')).open('w') as log:r=subprocess.run(cmd,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
 print(corpus.name,r.returncode,flush=True)
 failed|=bool(r.returncode)
sys.exit(failed)
