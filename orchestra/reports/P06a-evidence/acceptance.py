#!/usr/bin/env python3
"""Serial standard-CLI acceptance and all retained corpus replays."""
import json, os, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
S=ROOT/'orchestra/state/P06a-directionalblur-pf32-cropped-mismatch'
E=ROOT/'orchestra/reports/P06a-evidence'
os.environ.update(TMPDIR=str(S),TMP=str(S),TEMP=str(S),OLM_TEST_JOBS='1',PYTHONDONTWRITEBYTECODE='1')
base=[sys.executable,'tools/fuzz/run.py','--plugin','olmdirectionalblur','--jobs','1','--budget-minutes','30','--shrink-attempts','0','--scratch',str(S/'fuzz'),'--corpus',str(S/'failures')]
runs=[]
for geometry,seeds,n in [('default',[1],300),('realistic',[1,2053,2069],100),('realistic-v2',[1,2053,2069],100)]:
 for seed in seeds:runs.append((f'{geometry}-{seed}', ['--geometry',geometry,'--seed',str(seed),'--n',str(n)]))
for seed in [2026,2027]:runs.append((f'odd-even-{seed}',['--geometry','realistic','--size-sampler','odd-even-v1','--max-size','1920','--size-max-height','1080','--seed',str(seed),'--n','150']))
corpora={}
if '--replay-only' in sys.argv:runs=[]
for p in (ROOT/'tests/fuzz_corpus').rglob('*.json'):
 if not p.relative_to(ROOT/'tests/fuzz_corpus').parts[0].startswith('olmdirectionalblur'):continue
 d=json.loads(p.read_text());corpora.setdefault((p.parent,d['max_size'],d.get('size_sampler','default')),[]).append(p)
for (directory,maximum,sampler),paths in sorted(corpora.items()):
 # Standard replay enumerates one directory; mixed bounds require one file each.
 mixed=len({k for k in corpora if k[0]==directory})>1
 for target in paths if mixed else [directory]:
  runs.append(('replay-'+str(target.relative_to(ROOT/'tests/fuzz_corpus')).replace('/','_').replace('.json',''),['--replay',str(target),'--max-size',str(maximum),'--size-sampler',sampler]))
rows=[]
for label,args in runs:
 cmd=base+args+['--report',str(E/(label+'.json'))]
 with (S/(label+'.log')).open('w') as log:r=subprocess.run(cmd,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
 rows.append(dict(label=label,command=cmd,returncode=r.returncode))
 (E/('replay-commands.json' if '--replay-only' in sys.argv else 'acceptance-commands.json')).write_text(json.dumps(rows,indent=2)+'\n')
 print(label,r.returncode,flush=True)
