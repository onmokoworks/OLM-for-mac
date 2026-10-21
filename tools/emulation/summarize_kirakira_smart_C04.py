#!/usr/bin/env python3
"""Compact measured C04 evidence without changing results or corpus baselines."""
import argparse
import json
from pathlib import Path
import hashlib
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--scratch',type=Path,required=True)
p.add_argument('--report',type=Path,required=True)
p.add_argument('--phase',choices=('tiny','pf8','gaussian'),default='tiny')
a=p.parse_args(); root=Path(__file__).resolve().parents[2]
def read(name): return json.loads((a.scratch/(name+'.json')).read_text())
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
if a.phase != 'tiny':
    prefix=a.phase
    report=dict(schema='olm-kira-smart-C04-cluster/1',phase=prefix,campaigns={},checks={},sources={})
    for seed in (1,4):
        mapped={}
        for kind in ('before','after'):
            r=read(f'{prefix}-campaigns/{kind}-seed{seed}')
            assert r['status']=='complete' and r['completed']==300
            report['campaigns'][f'{kind}-seed{seed}']={k:r[k] for k in ('summary','provenance','status','completed')}
            mapped[kind]={c['index']:c for c in r['cases']}
        changes=[]
        for i,old in mapped['before'].items():
            new=mapped['after'][i]
            x,y=(c['result']['routes']['smart'] for c in (old,new))
            assert old['result']['oracle']==new['result']['oracle']
            assert x['status']==y['status'] or x['status']=='refusal' and y['status']=='exact'
            if x['status']=='exact': assert x==y
            if x!=y: changes.append(dict(index=i,input_sha256=old['input_sha256'],before=x,after=y))
        report['campaigns'][f'transitions-seed{seed}']=changes
        r=read(f'{prefix}-off-seed{seed}')
        report['campaigns'][f'gateoff-seed{seed}']={k:r[k] for k in ('summary','provenance','status','completed')}
    names=(('pf8-before-trace','pf8-after-trace','pf8-production-trace','pf8-corpus-audit',
            'pf8-normalize-probe','pf8-flat-normalize-probe','pf8-verify','pf8-flat-verify',
            'pf8-boundary','pf8-campaign-verify','pf8-replay','pf8-rebased') if prefix=='pf8' else
           ('gaussian-final-probe','gaussian-final-boundary','gaussian-verify','gaussian-campaign-verify',
            'gaussian-corpus-audit','gaussian-boundary','gaussian-negatives','gaussian-replay','gaussian-rebased',
            'gaussian-production-trace','gaussian-before-trace','gaussian-length1-evidence','gaussian-length1-refusal'))
    for name in names:
        r=read(name)
        if name.endswith(('replay','rebased')): r={k:r[k] for k in ('status','completed','replay_matches_saved','replays')}
        elif 'rows' in r and r['rows'] and 'parameters' in r['rows'][0]:
            r['rows']=[{k:v for k,v in row.items() if k!='parameters' or row.get('result',{}).get('status')!='exact'} for row in r['rows']]
        report['checks'][name]=r
    for path in [root/'mac/OLMKiraKira/OLMKiraKira.cpp',*sorted((root/'core').glob('kirakira*.h')),
                 *sorted((root/'tools/emulation').glob('*kirakira*C04*'))]:
        report['sources'][str(path.relative_to(root))]=digest(path)
    if prefix=='gaussian':
        report['remaining_refusals']={}
        for seed in (1,4):
            current=read(f'gaussian-campaigns/after-seed{seed}')
            off={c['index']:c for c in read(f'gaussian-off-seed{seed}')['cases']}
            remaining=[]
            for case in current['cases']:
                if case['result']['routes']['smart']['status']!='refusal': continue
                params={v['slot']:v['value'] for v in case['parameters']}
                remaining.append(dict(index=case['index'],input_sha256=case['input_sha256'],
                    geometry=case['geometry'],depth=case['depth'],profile=case['profile'],
                    channel=params[1],mode=params[2],oracle=case['result']['oracle'],
                    diagnostic=off[case['index']]['result']['routes']['smart']))
            report['remaining_refusals'][str(seed)]=remaining
    report['fast_tests']=(a.scratch/f'{prefix}-fast-tests.log').read_text().strip()
    sanitizer=a.scratch/f'{prefix}-sanitizer-tests.log'
    if sanitizer.exists(): report['sanitizer_tests']=sanitizer.read_text().strip()
    if prefix=='gaussian':
        report['frozen_headers']={n:digest(a.scratch/n) for n in ('gaussian_before.h','gaussian_C04_final.h','gaussian_C04.h')}
        assert report['frozen_headers']['gaussian_C04_final.h']==report['sources']['core/kirakira_gaussian.h']
    a.report.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('wrote',a.report,'bytes',a.report.stat().st_size)
    raise SystemExit(0)
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
