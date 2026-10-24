import json,gzip,re,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[3];S=R/'orchestra/state/P03a-distancegradation-pf32-downsample-ulp';E=Path(__file__).parent
def data(n):
 if (S/n).exists():return (S/n).read_bytes()
 if (E/n).exists():return (E/n).read_bytes()
 return gzip.decompress((E/(n+'.gz')).read_bytes())
load=lambda n:json.loads(data(n))
b,c=load('baseline.json'),load('candidate.json');reg=[];changed=[]
for x,y in zip(b['cases'],c['cases']):
 assert x['index']==y['index']
 for route,old in x['result']['routes'].items():
  new=y['result']['routes'][route]
  if old['status']=='exact' and new['status']!='exact':reg.append([x['index'],route,old,new])
  if old.get('raw_sha256')!=new.get('raw_sha256'):changed.append([x['index'],route,old.get('raw_sha256'),new.get('raw_sha256')])
oldrows=[json.loads(x) for x in (R/'orchestra/reports/T15b-evidence/olmdistancegradation-cases.jsonl').read_text().splitlines()]
newrows=[json.loads(x) for x in (S/'sweep.jsonl').read_text().splitlines()]
input_diffs=[i for i,(a,z) in enumerate(zip(oldrows,newrows)) if a['input_sha256']!=z['input_sha256']]
units={}
for which in ('before','after'):
 t=data(f'plugin-units-{which}.log').decode()
 units[which]=dict(summary=re.findall(r'Ran \d+ tests.*|FAILED \(.*\)|^OK.*',t,re.M),failures=re.findall(r'^(?:ERROR|FAIL): (.*)$',t,re.M))
replays={n:{k:load(n)[k] for k in ('completed','requested','replay_matches_saved')} for n in ('replay-default.json','replay-P02b.json','replay-T15b.json')}
summary=dict(baseline=b['summary'],candidate=c['summary'],regressions=reg,changed_raw_hashes=changed,sweep=load('sweep-summary.json')['counts'],sweep_input_differences=input_diffs,units=units,unit_failures_unchanged=units['before']['failures']==units['after']['failures'],replays=replays)
(E/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
for name in ('baseline.json','candidate.json','sweep.jsonl','sweep-summary.json','witness.json','replay-default.json','replay-P02b.json','replay-T15b.json'):
 (E/(name+'.gz')).write_bytes(gzip.compress(data(name),mtime=0))
for name in ('core-before-comparison.json','stage-matrix.json','stages.json','sqrt-trace.json','compare.log','units-before.log','units-after.log','plugin-units-before.log','plugin-units-after.log'):
 (E/name).write_bytes(data(name))
print(json.dumps({k:v for k,v in summary.items() if k!='units'},indent=2))
assert not reg and not input_diffs and summary['unit_failures_unchanged']
assert all(r['replay_matches_saved'] for r in replays.values())
assert summary['sweep'].get('mismatch',0)==0
