"""Recheck P05c Blur campaigns serially; all transient outputs stay in ticket scratch."""
import os, subprocess, sys, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
S=ROOT/'orchestra/state/P05c-blur-colorkey-smoother-performance'
S.mkdir(parents=True,exist_ok=True)
env=dict(os.environ,TMPDIR=str(S),TMP=str(S),TEMP=str(S),OLM_TEST_JOBS='1',PYTHONDONTWRITEBYTECODE='1')
commands=[('default-final',['--n','300','--seed','1']),
 ('realistic-final-1',['--geometry','realistic','--n','100','--seed','1']),
 ('realistic-final-20261024',['--geometry','realistic','--n','100','--seed','20261024']),
 ('odd-final-2026',['--geometry','realistic','--size-sampler','odd-even-v1','--max-size','1920','--size-max-height','1080','--n','150','--seed','2026']),
 ('odd-final-2027',['--geometry','realistic','--size-sampler','odd-even-v1','--max-size','1920','--size-max-height','1080','--n','150','--seed','2027']),
 ('replay-default',['--replay','tests/fuzz_corpus/olmblur']),
 ('replay-odd',['--geometry','realistic','--size-sampler','odd-even-v1','--max-size','1920','--replay','tests/fuzz_corpus/olmblur/T15b-odd-even-realistic'])]
for name,args in commands:
 name="parallel-"+name
 cmd=[sys.executable,'tools/fuzz/run.py','--plugin','olmblur','--jobs','1','--budget-minutes','25','--scratch',str(S/name),'--report',str(S/(name+'.json')),'--corpus',str(S/(name+'-corpus')),*args]
 with (S/(name+'.log')).open('w') as log:
  result=subprocess.run(cmd,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
 print(name,result.returncode,flush=True)
 if result.returncode:break
