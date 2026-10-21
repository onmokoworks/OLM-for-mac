#!/usr/bin/env python3
"""Compact measured C04 evidence without changing results or corpus baselines."""
import argparse
import json
from pathlib import Path
import hashlib
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--scratch',type=Path,required=True)
p.add_argument('--report',type=Path,required=True)
a=p.parse_args(); root=Path(__file__).resolve().parents[2]
def read(name): return json.loads((a.scratch/(name+'.json')).read_text())
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
report=dict(schema='olm-kira-smart-C04-evidence/1',scope='CPU original AEX Smart versus Mac Smart; native AE/UCRT and other host routes unverified',campaigns={},checks={},sources={})
for name in ('before-seed1','before-seed4','after-seed1','after-seed4','owner-seed1','owner-seed4'):
 r=read(name)
 report['campaigns'][name]=dict(status=r['status'],completed=r['completed'],summary=r['summary'],provenance=r['provenance'])
for seed in (1,4):
 before,after=(read(f'{k}-seed{seed}') for k in ('before','after'))
 old={r['index']:r for r in before['cases']};new={r['index']:r for r in after['cases']}
 transitions=[]
 for i in old:
  x,y=(r[i]['result']['routes']['smart'] for r in (old,new))
  assert old[i]['result']['oracle']==new[i]['result']['oracle']
  assert old[i]['result']['routes']['classic']==new[i]['result']['routes']['classic']
  assert x['status']==y['status'] or x['status']=='refusal' and y['status']=='exact'
  if x['status']=='exact': assert x==y
  if x!=y: transitions.append(dict(index=i,input_sha256=old[i]['input_sha256'],before=x,after=y))
 report['campaigns'][f'seed{seed}-transitions']=transitions
names=('alpha-probe','alpha-candidate','zero-probe','tiny-verify','tiny-campaign-verify',
       'tiny-negatives-final','tiny-replay','tiny-rebased','pre-geometry','tiny-trace',
       'pf8-probe','pf8-flat-probe','pf8-before-trace','gaussian-probe','gaussian-trace')
for name in names:
 r=read(name)
 if name in ('tiny-replay','tiny-rebased'):
  r={k:r[k] for k in ('status','completed','replay_matches_saved','replays')}
 elif 'rows' in r and r['rows'] and 'parameters' in r['rows'][0]:
  r['rows']=[{k:v for k,v in row.items() if k not in ('parameters',)} for row in r['rows']]
 report['checks'][name]=r
initial=read('before-default-shrink')
report['initial_shrink_errors']=[r for r in initial['cases'] if 'worker_error' in r]
report['initial_shrink_summary']=initial['summary']
for path in [root/'mac/OLMKiraKira/OLMKiraKira.cpp',*sorted((root/'core').glob('kirakira*.h')),
             *sorted((root/'tools/emulation').glob('*kirakira*C04*'))]:
 report['sources'][str(path.relative_to(root))]=digest(path)
report['tests']={n:(a.scratch/n).read_text().strip() for n in ('fast-tests.log','sanitizer-tests.log')}
a.report.parent.mkdir(parents=True,exist_ok=True)
a.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print('wrote',a.report,'bytes',a.report.stat().st_size)
