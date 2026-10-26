"""Replay every retained DistanceGradation corpus with its original sampler."""
import json,os,subprocess,sys
from collections import defaultdict
from pathlib import Path
R=Path(__file__).resolve().parents[3];S=R/'orchestra/state/N03-distancegradation-bilateral-refusals';groups=defaultdict(list)
for root in sorted((R/'tests/fuzz_corpus').glob('*distancegradation*')):
 for p in sorted(root.rglob('*.json')):
  d=json.loads(p.read_text())
  key=(d['max_size'],d.get('geometry_sampler','default'),d.get('size_sampler','default'),d.get('size_max_height'))
  groups[key].append(p)
rows=[]
for i,(key,paths) in enumerate(groups.items()):
 mx,geometry,size,height=key;dest=S/f'replay-input-{i}';dest.mkdir(exist_ok=True)
 for n,p in enumerate(paths):
  link=dest/f'{n:04d}-{p.name}'
  if not link.exists():link.symlink_to(p)
 args=['python3',str(R/'tools/fuzz/run.py'),'--plugin','olmdistancegradation','--worker',str(Path.home()/'.cache/olm-emu/worker-F54b/aex-guest-worker'),'--jobs','1','--replay',str(dest),'--max-size',str(mx),'--geometry',{'realistic-v1':'realistic'}.get(geometry,geometry),'--size-sampler',size,'--budget-minutes','90','--scratch',str(S/f'replay-{i}'),'--report',str(S/f'replay-{i}.json')]
 if height is not None:args+=['--size-max-height',str(height)]
 with (S/f'replay-{i}.log').open('w') as log:r=subprocess.run(args,cwd=R,stdout=log,stderr=subprocess.STDOUT)
 rows.append(dict(group=i,inputs=[str(p.relative_to(R)) for p in paths],command=args,returncode=r.returncode))
 print('group',i,'cases',len(paths),'returncode',r.returncode,flush=True)
(S/'replay-index.json').write_text(json.dumps(rows,indent=2)+'\n')
