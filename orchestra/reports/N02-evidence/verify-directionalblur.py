"""Serial, standard CLI reproducer; stores large outputs in ticket scratch."""
import hashlib, json, os, pathlib, subprocess, sys
R=pathlib.Path(__file__).resolve().parents[3]
S=R/'orchestra/state/N02-olmdirectionalblur-nightly-20261025'
E=pathlib.Path(__file__).resolve().parent
S.mkdir(parents=True,exist_ok=True)
os.environ.update(TMPDIR=str(S),TMP=str(S),TEMP=str(S),OLM_TEST_JOBS='1',PYTHONDONTWRITEBYTECODE='1')
def flags(d):
 a=['--geometry',d.get('geometry_sampler','default').replace('realistic-v1','realistic'),'--max-size',str(d['max_size'])]
 if d.get('size_sampler')=='odd-even-v1': a+=['--size-sampler','odd-even-v1','--size-max-height',str(d.get('size_max_height',1080))]
 return a
commands=[]
def run(label,args):
 if mode=='refresh-campaigns' and (S/(label+'.json')).exists():
  old=json.loads((S/(label+'.json')).read_text())
  deps=old.get('provenance',{}).get('dependencies_sha256',{})
  if old.get('completed')==old.get('requested') and all(deps.get(f)==hashlib.sha256((R/f).read_bytes()).hexdigest() for f in ('core/dblur_frontonly.cpp','core/dblur_rowdriver.cpp')):
   print(label,'reused verified final source',flush=True)
   return old
 cmd=[sys.executable,'tools/fuzz/run.py','--plugin','olmdirectionalblur','--jobs','1','--scratch',str(S/'run'),'--corpus',str(S/'failures'),'--shrink-attempts','0','--report',str(S/(label+'.json'))]+args
 with (S/(label+'.log')).open('w') as f: rc=subprocess.run(cmd,cwd=R,stdout=f,stderr=subprocess.STDOUT).returncode
 commands.append(dict(label=label,command=cmd,returncode=rc))
 (E/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
 print(label,rc,flush=True)
 return json.loads((S/(label+'.json')).read_text())
mode=sys.argv[1]
if mode=='reference-witnesses':
 for p in sorted((R/'tests/fuzz_corpus/olmdirectionalblur/N02-nightly-20261025').glob('*.json')):
  d=json.loads(p.read_text())
  result=run('reference-'+p.stem,['--reference-build','--replay',str(p)]+flags(d))
  assert result['replay_matches_saved']
elif mode=='witnesses':
 for p in sorted((R/'orchestra/reports/nightly-20261025/witnesses').glob('*.json')):
  d=json.loads(p.read_text())
  if d.get('plugin')!='olmdirectionalblur':continue
  report=run('nightly-'+p.stem,['--replay',str(p)]+flags(d))
  observed=report['replays'][0]['result']
  assert observed['routes']['smart']['status']=='exact'
  assert observed['oracle']==d['result']['oracle']
  d['result']=observed
  d['provenance']=report['provenance']
  d['label']='N02 nightly 20261025; initialized Back Alpha Fade weights; both routes'
  out=R/'tests/fuzz_corpus/olmdirectionalblur/N02-nightly-20261025'/p.name
  out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(d,indent=2)+'\n')
  (E/('nightly-'+p.stem+'.json')).write_text(json.dumps(report,indent=2)+'\n')
elif mode in ('campaigns','refresh-campaigns'):
 for sampler in ['realistic','realistic-v2','odd-even-v1']:
  for seed in [2026102601,2026102602,2026102603]:
   a=['--geometry',sampler if sampler!='odd-even-v1' else 'realistic']
   if sampler=='odd-even-v1':a+=['--size-sampler',sampler,'--max-size','1920','--size-max-height','1080']
   run(f'{sampler}-{seed}',a+['--seed',str(seed),'--n','200'])
 run('default-1',['--seed','1','--n','300'])
elif mode=='corpora':
 groups={}
 for p in (R/'tests/fuzz_corpus').rglob('*.json'):
  if not p.relative_to(R/'tests/fuzz_corpus').parts[0].startswith('olmdirectionalblur'):continue
  d=json.loads(p.read_text());groups.setdefault((p.parent,tuple(flags(d))),[]).append(p)
 for (directory,f),paths in sorted(groups.items()):
  mixed=sum(k[0]==directory for k in groups)>1
  for target in paths if mixed else [directory]:
   run('corpus-'+str(target.relative_to(R/'tests/fuzz_corpus')).replace('/','_'),['--replay',str(target)]+list(f))
(E/(mode+'-commands.json')).write_text(json.dumps(commands,indent=2)+'\n')
