"""Replay all retained corpora for one reference plugin, one process at a time."""
import argparse,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser();p.add_argument('--plugin',required=True);a=p.parse_args()
S=ROOT/'orchestra/state/R10-reference-fast-split'/('replay-'+a.plugin);S.mkdir(parents=True,exist_ok=True)
env=dict(os.environ,TMPDIR=str(S),TMP=str(S),TEMP=str(S),OLM_TEST_JOBS='1',PYTHONDONTWRITEBYTECODE='1')
groups={}
for path in (ROOT/'tests/fuzz_corpus').rglob('*.json'):
 if not path.relative_to(ROOT/'tests/fuzz_corpus').parts[0].startswith(a.plugin):continue
 data=json.loads(path.read_text())
 if data.get('plugin')!=a.plugin:continue
 groups.setdefault((path.parent,data['max_size'],data.get('size_sampler','default')),[]).append(path)
rows=[]
for (directory,maximum,sampler),paths in sorted(groups.items()):
 mixed=len([k for k in groups if k[0]==directory])>1
 for target in paths if mixed else [directory]:
  label=str(target.relative_to(ROOT/'tests/fuzz_corpus')).replace('/','_').replace('.json','')
  cmd=[sys.executable,'tools/fuzz/run.py','--plugin',a.plugin,'--reference-build','--jobs','1','--shrink-attempts','0','--scratch',str(S/'build'),'--corpus',str(S/'failures'),'--replay',str(target),'--max-size',str(maximum),'--size-sampler',sampler,'--report',str(S/(label+'.json'))]
  with (S/(label+'.log')).open('w') as log:r=subprocess.run(cmd,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
  data=json.loads((S/(label+'.json')).read_text())
  rows.append(dict(command=cmd,returncode=r.returncode,status=data.get('status'),summary=data.get('summary'),replay_matches=[x.get('replay_matches') for x in data.get('replays',[])]))
  (S/'commands.json').write_text(json.dumps(rows,indent=2)+'\n')
  print(label,r.returncode,data.get('status'),flush=True)
