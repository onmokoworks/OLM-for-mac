"""Serial standard-runner acceptance; logs and disposable builds stay in scratch."""
import json, os, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
S=ROOT/'orchestra/state/P04c2-smoother2-checkout-negotiation'
E=Path(__file__).resolve().parent
S.mkdir(parents=True,exist_ok=True)
env=dict(os.environ,TMPDIR=str(S),TMP=str(S),TEMP=str(S),OLM_TEST_JOBS='1',PYTHONDONTWRITEBYTECODE='1')
runs=[('default',['--seed','1','--n','300'])]
for g in ('realistic','realistic-v2'):
 for seed in (1,20261025):runs.append((f'{g}-{seed}',['--geometry',g,'--seed',str(seed),'--n','100']))
for seed in (2026,2027):runs.append((f'odd-{seed}',['--geometry','realistic','--size-sampler','odd-even-v1','--max-size','623','--seed',str(seed),'--n','150']))
for directory in sorted((ROOT/'tests/fuzz_corpus').rglob('*')):
 if directory.is_dir() and 'olmsmoother2' in str(directory) and list(directory.glob('*.json')):
  row=json.loads(next(directory.glob('*.json')).read_text());flags=['--replay',str(directory),'--max-size',str(row['max_size'])]
  if row.get('size_sampler')=='odd-even-v1':flags+=['--size-sampler','odd-even-v1']
  runs.append(('replay-'+directory.name,flags))
if len(sys.argv)>1:runs=[r for r in runs if r[0] in sys.argv[1:]]
results=[]
for label,flags in runs:
 cmd=[sys.executable,'tools/fuzz/run.py','--plugin','olmsmoother2','--jobs','1','--budget-minutes','25','--shrink-attempts','0','--scratch',str(S/label),'--report',str(E/(label+'.json')),'--corpus',str(S/'generated'),*flags]
 with (S/(label+'.log')).open('w') as f:r=subprocess.run(cmd,cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT)
 report=json.loads((E/(label+'.json')).read_text()) if (E/(label+'.json')).exists() else {}
 results.append(dict(label=label,command=cmd,returncode=r.returncode,summary=report.get('summary'),replay_matches_saved=report.get('replay_matches_saved'),completed=report.get('completed'),status=report.get('status')))
 (E/'campaign-summary.json').write_text(json.dumps(results,indent=2)+'\n')
 print(label,r.returncode,report.get('summary',report.get('replay_matches_saved')),flush=True)
