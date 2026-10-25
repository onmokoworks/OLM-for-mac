"""Run each required contract-route campaign and every corpus directory, serially."""
import os,subprocess,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];plugin,label=sys.argv[1:]
S=ROOT/'orchestra/state/P07d-distancegradation-blur-colorkey-threading';S.mkdir(parents=True,exist_ok=True)
env=dict(os.environ,TMPDIR=str(S),TMP=str(S),TEMP=str(S),OLM_TEST_JOBS='1',PYTHONDONTWRITEBYTECODE='1')
bounds=json.loads((ROOT/f'orchestra/reports/T15b-evidence/{plugin}-summary.json').read_text())
odd=['--geometry','realistic','--size-sampler','odd-even-v1','--max-size',str(bounds['maximum']),'--size-max-height',str(bounds['height_maximum'])]
commands=[('default',['--n','300','--seed','1']),('realistic-1',['--geometry','realistic','--n','100','--seed','1']),('realistic-fresh',['--geometry','realistic','--n','100','--seed','2026102507']),('odd-2026',[*odd,'--n','150','--seed','2026']),('odd-2027',[*odd,'--n','150','--seed','2027'])]
commands += [(g+'-'+seed,['--geometry',g,'--n','100','--seed',seed]) for g in ('realistic-v2',) for seed in ('1','2026102507')]
commands = [x for x in commands if x[0]!='odd-2027']
if os.environ.get('P07D_REPLAY_ONLY')=='1':commands=[]
corpora=[p for p in (ROOT/'tests/fuzz_corpus').iterdir() if p.is_dir() and (p.name==plugin or p.name.startswith(plugin+'_'))]
folders=[folder for corpus in sorted(corpora) for folder in [corpus,*sorted(p for p in corpus.rglob('*') if p.is_dir())]]
for folder in folders:
 files=sorted(folder.glob('*.json'))
 if not files:continue
 record=json.loads(files[0].read_text());flags=['--max-size',str(record['max_size'])]
 if record.get('size_sampler')=='odd-even-v1':flags+=['--size-sampler','odd-even-v1']
 if record.get('geometry_sampler'):flags+=['--geometry','realistic']
 commands.append(('replay-'+folder.name,[*flags,'--replay',str(folder)]))
route='classic' if plugin=='olmsmoother' else 'smart'
for name,args in commands:
 name=label+'-'+name;report=S/(name+'.json')
 cmd=[sys.executable,'tools/fuzz/run.py','--plugin',plugin,'--jobs','1','--budget-minutes','25','--shrink-attempts','0','--scratch',str(S/name),'--report',str(report),'--corpus',str(S/(name+'-corpus')),*args]
 if not (os.environ.get('P07D_RESUME')=='1' and report.exists()):
  with (S/(name+'.log')).open('w') as log:r=subprocess.run(cmd,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
  assert r.returncode==0,(name,r.returncode)
 d=json.loads(report.read_text())
 if '--replay' in args:assert d['replay_matches_saved'],name
 else:
  assert d['completed']==int(args[args.index('--n')+1]),name
  assert d['seed']==int(args[args.index('--seed')+1]),name
  assert not d['summary'].get(route+'_mismatch',0),(name,d['summary'])
  assert all(c['result']['routes'][route]['status']=='exact' for c in d['cases'] if c['result'].get('oracles',{}).get(route,c['result']['oracle'])['status']=='ok'),name
  if '--geometry' not in args and os.environ.get('P07D_BASELINE_REPORT'):
   baseline=json.loads(Path(os.environ['P07D_BASELINE_REPORT']).read_text())
   assert len(baseline['cases'])==len(d['cases'])
   for before,after in zip(baseline['cases'],d['cases']):
    assert before['input_sha256']==after['input_sha256']
    old=before['result']['routes'][route];new=after['result']['routes'][route]
    if old['status']=='exact':assert new['status']=='exact' and old['raw_sha256']==new['raw_sha256'],(name,before['index'])
 print(name,d['completed'],'PASS',flush=True)
