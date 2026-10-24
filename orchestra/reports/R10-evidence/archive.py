"""Keep compact, reproducible R10 evidence before deleting regenerable builds."""
import gzip,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
S=ROOT/'orchestra/state/R10-reference-fast-split';E=Path(__file__).resolve().parent
for path in S.rglob('*'):
 if path.suffix not in ('.json','.jsonl','.log') or any(part in ('xcode','build','ucrtmath') for part in path.relative_to(S).parts):continue
 if 'corpus' in str(path.relative_to(S)) or 'failures' in path.parts:continue
 # Complete runner reports retain hashes, command provenance and first mismatches.
 name='__'.join(path.relative_to(S).parts)+'.gz'
 with path.open('rb') as source,gzip.open(E/name,'wb') as target:
  while chunk:=source.read(1048576):target.write(chunk)
comparisons=[]
a=S/'fast-oracle-directional.json';b=S/'oracle-directional.json'
if a.exists() and b.exists():
 fast=json.loads(a.read_text())
 for label,path in [('P05a-fast',ROOT/'orchestra/reports/P05a-evidence/default-1.json'),('reference-fast',b)]:
  prior=json.loads(path.read_text());diff=[]
  for x,y in zip(prior['cases'],fast['cases']):
   assert x['index']==y['index'] and x['input_sha256']==y['input_sha256']
   for route in ('classic','smart'):
    old=x['result']['routes'][route].get('raw_sha256');new=y['result']['routes'][route].get('raw_sha256')
    if old!=new:diff.append(dict(index=x['index'],route=route,old=old,new=new))
  comparisons.append(dict(label=label,cases=len(prior['cases']),different_hashes=diff))
(E/'hash-comparisons.json').write_text(json.dumps(comparisons,indent=2)+'\n')
