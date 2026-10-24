"""Replay every retained ColorKeep corpus with its matching generation flags."""
import json
import os
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[3]
S=ROOT/'orchestra/state/P04d-colorkeep-cropped-checkout'
env=dict(os.environ,TMPDIR=str(S),PYTHONDONTWRITEBYTECODE='1',OLM_TEST_JOBS='1')
for corpus,flags in [
    ('colorkeep_realistic_P02a',[]),
    ('colorkeep/P04d-cropped-checkout',[]),
    ('colorkeep/T15b-odd-even-realistic',['--size-sampler','odd-even-v1','--max-size','1920'])]:
    name=corpus.split('/')[-1]
    cmd=[sys.executable,'tools/fuzz/run.py','--plugin','colorkeep','--jobs','1',
         '--replay','tests/fuzz_corpus/'+corpus,'--scratch',str(S/('replay-'+name)),
         '--report',str(S/('replay-'+name+'.json')),*flags]
    with (S/('replay-'+name+'.log')).open('w') as log:
        subprocess.run(cmd,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    r=json.loads((S/('replay-'+name+'.json')).read_text())
    print(name,r.get('status'),r.get('summary'),flush=True)
    assert r['status']=='replay_complete' and r['replay_matches_saved'] is True
