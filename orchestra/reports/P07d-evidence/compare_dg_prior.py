"""Compare all default candidate route bytes/errors with the retained P04a run."""
import gzip,json
from pathlib import Path
r=Path(__file__).resolve().parents[3];s=r/'orchestra/state/P07d-distancegradation-blur-colorkey-threading'
prior='orchestra/reports/P04a-evidence/default-after.json.gz'
a=json.load(gzip.open(r/prior,'rt'));b=json.loads((s/'dg-default.json').read_text());diff=[]
assert len(a['cases'])==len(b['cases'])==300
for x,y in zip(a['cases'],b['cases']):
 if x['input_sha256']!=y['input_sha256']:diff.append([x['index'],'input'])
 for route in ('smart','classic'):
  p=x['result']['routes'][route];q=y['result']['routes'][route]
  if (p.get('raw_sha256'),p.get('error'))!=(q.get('raw_sha256'),q.get('error')):diff.append([x['index'],route])
result=dict(cases=300,route_pairs=600,differences=diff,prior=prior)
(s/'dg-default-prior-comparison.json').write_text(json.dumps(result,indent=2)+'\n')
print(result)
assert not diff
