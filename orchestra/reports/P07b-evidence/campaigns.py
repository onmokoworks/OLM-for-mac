import json,os,subprocess,sys
from pathlib import Path
r=Path(__file__).resolve().parents[3];s=r/'orchestra/state/P07b-smoother2-threading';e=r/'orchestra/reports/P07b-evidence'
env=dict(os.environ,TMPDIR=str(s),TMP=str(s),TEMP=str(s),OLM_TEST_JOBS='1',PYTHONDONTWRITEBYTECODE='1')
runs=[('default',['--n','300','--seed','1'])]
for geo in ('realistic','realistic-v2'):
 for seed in (1,20261025):runs.append((geo+'-'+str(seed),['--geometry',geo,'--n','100','--seed',str(seed)]))
runs.append(('odd-even',['--geometry','realistic','--size-sampler','odd-even-v1','--max-size','623','--size-max-height','623','--n','150','--seed','2026']))
results=[]
for name,args in runs:
 command=[sys.executable,'tools/fuzz/run.py','--plugin','olmsmoother2','--jobs','1','--budget-minutes','30','--scratch',str(s/name),'--report',str(e/(name+'.json')),'--corpus',str(s/name/'corpus'),*args]
 with (s/(name+'.log')).open('w') as log:
  proc=subprocess.run(command,cwd=r,env=env,stdout=log,stderr=subprocess.STDOUT)
 results.append(dict(name=name,command=command,exit=proc.returncode))
 (e/'campaign-commands.json').write_text(json.dumps(results,indent=2)+'\n')
 print(name,proc.returncode,flush=True)
