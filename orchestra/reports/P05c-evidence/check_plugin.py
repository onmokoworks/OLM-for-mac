"""Run each required contract-route campaign and every corpus directory, serially."""
import os,subprocess,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];plugin,label=sys.argv[1:]
S=ROOT/'orchestra/state/P05c-blur-colorkey-smoother-performance';S.mkdir(parents=True,exist_ok=True)
env=dict(os.environ,TMPDIR=str(S),TMP=str(S),TEMP=str(S),OLM_TEST_JOBS='1',PYTHONDONTWRITEBYTECODE='1')
bounds=json.loads((ROOT/f'orchestra/reports/T15b-evidence/{plugin}-summary.json').read_text())
odd=['--geometry','realistic','--size-sampler','odd-even-v1','--max-size',str(bounds['maximum']),'--size-max-height',str(bounds['height_maximum'])]
commands=[('default',['--n','300','--seed','1']),('realistic-1',['--geometry','realistic','--n','100','--seed','1']),('realistic-fresh',['--geometry','realistic','--n','100','--seed','20261024']),('odd-2026',[*odd,'--n','150','--seed','2026']),('odd-2027',[*odd,'--n','150','--seed','2027'])]
corpus=ROOT/'tests/fuzz_corpus'/plugin
for folder in [corpus,*sorted(p for p in corpus.rglob('*') if p.is_dir())]:
 files=sorted(folder.glob('*.json'))
 if not files:continue
 record=json.loads(files[0].read_text());flags=['--max-size',str(record['max_size'])]
 if record.get('size_sampler')=='odd-even-v1':flags+=['--size-sampler','odd-even-v1']
 if record.get('geometry_sampler'):flags+=['--geometry','realistic']
 commands.append(('replay-'+folder.name,[*flags,'--replay',str(folder)]))
route='classic' if plugin=='olmsmoother' else 'smart'
for name,args in commands:
 name=label+'-'+name;report=S/(name+'.json')
 cmd=[sys.executable,'tools/fuzz/run.py','--plugin',plugin,'--jobs','1','--budget-minutes','25','--scratch',str(S/name),'--report',str(report),'--corpus',str(S/(name+'-corpus')),*args]
 if not (os.environ.get('P05C_RESUME')=='1' and report.exists()):
  with (S/(name+'.log')).open('w') as log:r=subprocess.run(cmd,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
  assert r.returncode==0,(name,r.returncode)
 d=json.loads(report.read_text())
 if '--replay' in args:assert d['replay_matches_saved'],name
 else:
  assert d['completed']==int(args[args.index('--n')+1]),name
  assert not d['summary'].get(route+'_mismatch',0),(name,d['summary'])
  assert all(c['result']['routes'][route]['status']!='refusal' for c in d['cases'] if c['result'].get('oracles',{}).get(route,c['result']['oracle'])['status']=='ok'),name
  if '--geometry' not in args:assert d['summary'].get(route+'_exact')==d['completed'],(name,d['summary'])
 print(name,d['completed'],'PASS',flush=True)
