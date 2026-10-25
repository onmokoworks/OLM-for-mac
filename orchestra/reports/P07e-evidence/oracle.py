"""Run required Smart campaigns and unchanged standard corpus replays serially."""
import json, os, subprocess, sys
from pathlib import Path
root=Path(__file__).resolve().parents[3]
s=root/'orchestra/state/P07e-radialblur-rotation-parallel/oracle';s.mkdir(parents=True,exist_ok=True)
env=dict(os.environ,TMPDIR=str(s),TMP=str(s),TEMP=str(s),PYTHONDONTWRITEBYTECODE='1',OLM_TEST_JOBS='1')
campaigns=[('default',['--seed','1','--n','300'])]
for geometry in ('realistic','realistic-v2'):
 for seed in (1,20261026):campaigns.append((f'{geometry}-{seed}',['--geometry',geometry,'--seed',str(seed),'--n','100']))
odd=['--geometry','realistic','--size-sampler','odd-even-v1','--max-size','1920','--size-max-height','1080']
campaigns.append(('odd',['--seed','2026','--n','150',*odd]))
for label,path,flags in [('root','radialblur',[]),('realistic','radialblur_realistic_P02d',['--geometry','realistic']),('p05b','radialblur/P05b-rotation-performance',[]),('odd','radialblur/T15b-odd-even-realistic',odd)]:
 campaigns.append(('replay-'+label,['--replay','tests/fuzz_corpus/'+path,*flags]))
records=[]
for label,flags in campaigns:
 command=[sys.executable,'tools/fuzz/run.py','--plugin','radialblur','--jobs','1','--shrink-attempts','0','--scratch',str(s/label),'--corpus',str(s/(label+'-corpus')),'--report',str(s/(label+'.json')),*flags]
 with (s/(label+'.log')).open('w') as log:result=subprocess.run(command,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT)
 records.append(dict(label=label,command=command,returncode=result.returncode))
 (s/'commands.json').write_text(json.dumps(records,indent=2)+'\n')
 print(label,result.returncode,flush=True)
