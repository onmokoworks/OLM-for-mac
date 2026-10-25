import json,os,subprocess,sys
from pathlib import Path
r=Path(__file__).resolve().parents[3];s=r/'orchestra/state/P07b-smoother2-threading';e=r/'orchestra/reports/P07b-evidence'
env=dict(os.environ,TMPDIR=str(s),TMP=str(s),TEMP=str(s),OLM_TEST_JOBS='1',PYTHONDONTWRITEBYTECODE='1')
groups={}
for p in (r/'tests/fuzz_corpus/olmsmoother2').rglob('*.json'):
 value=json.loads(p.read_text());groups.setdefault(value['max_size'],[]).append(p)
commands=[]
for maximum,paths in sorted(groups.items()):
 directory=s/('replay-input-'+str(maximum));directory.mkdir(exist_ok=True)
 for index,p in enumerate(sorted(paths)):
  link=directory/(str(index)+'.json')
  if not link.exists():link.symlink_to(p)
 flags=['--geometry','realistic-v2'] if maximum==256 else ['--geometry','realistic','--size-sampler','odd-even-v1','--size-max-height',str(maximum)]
 command=[sys.executable,'tools/fuzz/run.py','--plugin','olmsmoother2','--jobs','1','--max-size',str(maximum),'--replay',str(directory),'--scratch',str(s/('replay-'+str(maximum))),'--report',str(e/('replay-'+str(maximum)+'.json')),*flags]
 with (s/('replay-'+str(maximum)+'.log')).open('w') as log: result=subprocess.run(command,cwd=r,env=env,stdout=log,stderr=subprocess.STDOUT)
 commands.append(dict(command=command,exit=result.returncode,paths=[str(p.relative_to(r)) for p in sorted(paths)]))
 (e/'replay-commands.json').write_text(json.dumps(commands,indent=2)+'\n')
 print(maximum,result.returncode,flush=True)
