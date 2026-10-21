#!/usr/bin/env python3
"""Package completed T01 Round 4 measurements; does not render or rebaseline.

Run from the worktree root after the recorded Round 4 commands, before cleaning
scratch. Kept to make the counts and artifact provenance reproducible.
"""
import collections
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from types import SimpleNamespace

root=Path.cwd(); scratch=root/'orchestra/state/T01-radial-offset-promote/round4'; reports=root/'orchestra/reports'
sys.path[:0]=[str(root/'tools/fuzz'),str(root/'tools/emulation')]
from adapters.radialblur import Adapter
from core import save_corpus,sha
import probe_radialblur_offset_promote_20261002 as promote

def load(name):return json.loads((scratch/name).read_text())
def dump(path,obj):path.write_text(json.dumps(obj,sort_keys=True,indent=2)+'\n');assert path.stat().st_size<2_000_000

files={name: 'T01-round4-'+name for name in ['fuzz-base.json','fuzz-after.json','corpus-base.json','corpus-after.json','tests.json']}
for src,dst in files.items():shutil.copyfile(scratch/src,reports/dst)
for src,dst in [('gates.log','T01-round4-gates-initial.log'),('gates-complete.log','T01-round4-gates-stopped.log'),('tests.log','T01-round4-tests.log')]:
 shutil.copyfile(scratch/src,reports/dst)
base=load('fuzz-base.json');after=load('fuzz-after.json');cb=load('corpus-base.json');ca=load('corpus-after.json')
rows=[json.loads(line) for line in (scratch/'gates/independent.jsonl').read_text().splitlines()]
source=promote.public.SOURCE.read_text()
assert (scratch/'gates/candidate.cpp').read_text()==source
compiled_source=re.sub(r'^#include "([^"]+)"',lambda m:'#include "'+str((promote.public.SOURCE.parent/m.group(1)).resolve())+'"',source,flags=re.M)
for mode in ['o2','san','default']:
 assert (scratch/'gates'/mode/'production_under_test.cpp').read_text()==compiled_source
calibration=[]
for name in promote.CALIBRATION_REPORTS:
 old=json.loads((root/'reports'/name).read_text())
 cases=[next(r for r in old['rows'] if r['family']==f and r['depth']==d) for f in [1,2] for d in [8,16,32]]
 for i,case in enumerate(cases):
  paths=list((scratch/'gates/calibration_replay'/(name[:16]+'_'+str(i))).glob('native_*/output.raw'))
  assert len(paths)==1
  actual=sha(paths[0].read_bytes());assert actual==case['reference_raw_sha256']
  calibration.append(dict(report=name,family=case['family'],depth=case['depth'],expected=case['reference_raw_sha256'],actual=actual))
dump(reports/'T01-round4-offset390.json',dict(schema='radialblur.offset-promote-partial/1',status='independent_complete_retained_incomplete',
 production_source_sha256=sha(source.encode()),worker_sha256=after['provenance']['worker_sha256'],
 aex_sha256=after['provenance']['aex_sha256'],core_sha256=after['provenance']['core_sha256'],
 header_sha256=after['provenance']['header_sha256'],calibration=calibration,
 builds={mode:dict(binary_sha256=sha((scratch/'gates'/mode/'mac').read_bytes()),compiled_source_sha256=sha(compiled_source.encode())) for mode in ['o2','san','default']},
 case_count=len(rows),public_replays=len(rows)*6,before_revision=promote.offset.BEFORE_REVISION,
 before_summary=dict(collections.Counter('refusal' if r['before_error'] else 'exact' if r['before_raw_exact'] else 'mismatch' for r in rows)),rows=rows))

adapter=Adapter(SimpleNamespace(max_size=256,case_timeout=10,main=Path('/Users/onmk/Documents/Projects/Personal/OLM as'),
 worker=Path(after['provenance']['worker_path'])))
wd=reports/'T01-round4-witnesses';wd.mkdir(exist_ok=True)
for index in [193,425]:
 row=next(c for c in base['cases'] if c['index']==index);case=adapter.generate(1,index)
 assert sha(case['pixels'])==row['input_sha256'] and case['parameters']==row['parameters']
 save_corpus(wd/f'seed1_case{index:06d}.json',adapter,case,case,row['result'],dict(accepted=[],attempted=0,reason='unreduced recorded exact-to-refusal witness'),base['provenance'])

transitions=collections.Counter();forbidden=[];policy=[];oracle_status_changes=[]
for x,y in zip(base['cases'],after['cases']):
 assert x['index']==y['index'] and x['input_sha256']==y['input_sha256']
 assert all(x[k]==y[k] for k in ['parameters','depth','geometry','input_padding','output_padding'])
 for route,before in x['result']['routes'].items():
  result=y['result']['routes'][route];t=(route,before['status'],result['status']);transitions[t]+=1
  detail=dict(index=x['index'],route=route,before=before,after=result,refusal_guards=y.get('refusal_guards',{}))
  if before['status']=='exact' and (result['status']!='exact' or before['raw_sha256']!=result.get('raw_sha256')):forbidden.append(detail)
  if before['status']=='mismatch' and result['status']=='refusal':policy.append(detail)
 if x['result']['oracle']['status']!=y['result']['oracle']['status']:oracle_status_changes.append(dict(index=x['index'],before=x['result']['oracle'],after=y['result']['oracle']))
 if x['result']['oracle']['status']==y['result']['oracle']['status']=='ok':assert x['result']['oracle']['raw_sha256']==y['result']['oracle']['raw_sha256']
reported_replays=max(map(int,re.findall(r'OFFSET_PROMOTE_RETAINED (\d+)',(scratch/'gates.log').read_text())))
assert reported_replays % 6 == 0
retained=promote.offset.retained_cases();case_counts=collections.Counter(r.get('matrix','rotation_size_noise_independent') for r in retained)
verified=collections.Counter(r.get('matrix','rotation_size_noise_independent') for r in retained[:reported_replays//6])
summary=dict(schema='radialblur.T01-round4/1',status='blocked',base_revision=subprocess.check_output(['git','rev-parse','95b185eb'],text=True).strip(),
 production_source_sha256=sha(source.encode()),base_source_sha256=base['provenance']['source_sha256'],
 offset=dict(conditions=390,exact_public_replays=2340,before=dict(collections.Counter('refusal' if r['before_error'] else 'exact' if r['before_raw_exact'] else 'mismatch' for r in rows))),
 retained=dict(requested_conditions=9645,requested_public_replays=57870,reported_exact_replays=reported_replays,
  suites=[dict(suite=k,total_conditions=n,reported_exact_conditions=verified[k],reported_exact_replays=verified[k]*6) for k,n in case_counts.items()],
  interruption='First run passed 390 but aggregation KeyError matrix stopped retained reporting at 6336; repaired run stopped on fuzz exact-to-refusal regression after 84 independent cases.'),
 fuzz=dict(base=base['summary'],after=after['summary'],transitions=[dict(route=r,before=b,after=a,count=n) for (r,b,a),n in sorted(transitions.items())],forbidden=forbidden,policy=policy,oracle_status_changes=oracle_status_changes),
 artifacts={dst:dict(sha256=sha((reports/dst).read_bytes()),bytes=(reports/dst).stat().st_size) for dst in files.values()})
ct=collections.Counter();st=collections.Counter()
for x,y in zip(cb['replays'],ca['replays']):
 assert x['path']==y['path']
 old=json.loads(Path(x['path']).read_text())['result']
 for route,v in x['result']['routes'].items():
  actual=y['result']['routes'][route]
  if v['status']=='exact':assert actual['status']=='exact' and actual['raw_sha256']==v['raw_sha256']
  ct[(route,v['status'],actual['status'])]+=1
  st[(route,old['routes'][route]['status'],actual['status'])]+=1
summary['corpus']=dict(cases=35,base_to_candidate=[dict(route=r,before=b,after=a,count=n) for (r,b,a),n in sorted(ct.items())],saved_to_candidate=[dict(route=r,before=b,after=a,count=n) for (r,b,a),n in sorted(st.items())],rebaselined=False)
for label,data in [('base',base),('after',after)]:
 selected=[r for r in data['cases'] if r['depth']==8 and any(p['slot']==6 and p['value']!=0 for p in r['parameters'])]
 summary['fuzz'][label+'_pf8_outer_offset']=dict(cases=len(selected),routes={route:dict(collections.Counter(r['result']['routes'][route]['status'] for r in selected)) for route in ['classic','smart']})
dump(reports/'T01-round4-summary.json',summary)
print('evidence packaged; forbidden routes',len(forbidden),'offset',len(rows),'retained reported',reported_replays)
print('retained suites',summary['retained']['suites'])
