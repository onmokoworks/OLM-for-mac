"""Serial acceptance runs; logs and build products stay in ticket scratch."""
import json,os,subprocess,sys,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[3];S=R/'orchestra/state/P04a-distancegradation-default-pf32';S.mkdir(exist_ok=True)
os.environ.update(TMPDIR=str(S),TMP=str(S),TEMP=str(S),OLM_TEST_JOBS='1',PYTHONDONTWRITEBYTECODE='1')
rows=[]
def run(label,extra):
 out=S/(label+'.json');work=S/label
 cmd=[sys.executable,str(R/'tools/fuzz/run.py'),'--plugin','olmdistancegradation','--jobs','1','--shrink-attempts','0','--scratch',str(work),'--corpus',str(S/(label+'-corpus')),'--report',str(out),*extra]
 with (S/(label+'.log')).open('w') as f:rc=subprocess.call(cmd,cwd=R,stdout=f,stderr=subprocess.STDOUT)
 data=json.loads(out.read_text()) if out.exists() else {}
 row=dict(label=label,command=cmd,returncode=rc,completed=data.get('completed'),counts=data.get('summary'),replay_matches_saved=data.get('replay_matches_saved'));rows.append(row)
 print(json.dumps(row),flush=True);(S/'verification.json').write_text(json.dumps(rows,indent=2))
 # Keep result JSON and logs; discard reproducible host products.
 shutil.rmtree(work,ignore_errors=True)
if sys.argv[1]=='campaigns':
 run('default-after',['--n','300','--seed','1'])
 for seed in (1,10424):run(f'realistic-{seed}',['--n','100','--seed',str(seed),'--geometry','realistic'])
 for seed in (2026,2027):run(f'odd-even-{seed}',['--n','150','--seed',str(seed),'--geometry','realistic','--size-sampler','odd-even-v1','--max-size','1920','--size-max-height','1080'])
else:
 for root in sorted((R/'tests/fuzz_corpus').glob('olmdistancegradation*')):
  for directory in [root,*sorted(p for p in root.rglob('*') if p.is_dir())]:
   files=sorted(directory.glob('*.json'))
   if not files:continue
   data=json.loads(files[0].read_text());flags=['--replay',str(directory),'--max-size',str(data['max_size'])]
   if data.get('geometry_sampler')=='realistic-v1':flags+=['--geometry','realistic']
   if data.get('size_sampler'):flags+=['--size-sampler',data['size_sampler']]
   if data.get('size_max_height'):flags+=['--size-max-height',str(data['size_max_height'])]
   run('replay-'+str(directory.relative_to(R/'tests/fuzz_corpus')).replace('/','-'),flags)
(S/(sys.argv[1]+'-verification.json')).write_text(json.dumps(rows,indent=2))
