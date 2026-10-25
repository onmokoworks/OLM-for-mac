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
 with path.open('rb') as source,(E/name).open('wb') as output,gzip.GzipFile(fileobj=output,mode='wb',mtime=0) as target:
  while chunk:=source.read(1048576):target.write(chunk)
comparisons=[]
for plugin, baseline in [('directional','P05a-evidence/default-1.json'),('radial','P05b-evidence/default.json.gz'),('blur','P05c-evidence/blur-parallel-default-final.json.gz'),('key','P05c-evidence/key-final-default.json.gz'),('smooth','P05c-evidence/smooth-final-default.json.gz')]:
 a=S/f'fast-oracle-{plugin}.json';b=S/f'oracle-{plugin}.json'
 if not a.exists() or not b.exists():continue
 fast=json.loads(a.read_text())
 for label,path in [(plugin+'-baseline-fast',ROOT/'orchestra/reports'/baseline),(plugin+'-reference-fast',b)]:
  prior=json.load(gzip.open(path) if path.suffix=='.gz' else path.open());diff=[]
  for x,y in zip(prior['cases'],fast['cases']):
   assert x['index']==y['index'] and x['input_sha256']==y['input_sha256']
   for route in ('classic','smart'):
    old=x['result']['routes'][route].get('raw_sha256');new=y['result']['routes'][route].get('raw_sha256')
    if old!=new:diff.append(dict(index=x['index'],route=route,old=old,new=new))
  comparisons.append(dict(label=label,cases=len(prior['cases']),different_hashes=diff))
p=S/'fast-oracle-kira.json'
if p.exists():
 fast=json.loads(p.read_text());prior=json.loads((ROOT/'orchestra/reports/P07a-evidence/summary.json').read_text())['default']['smart_rows'];diff=[]
 for x,y in zip(prior,fast['cases']):
  assert x['index']==y['index'] and x['input_sha256']==y['input_sha256']
  if x['candidate_sha256']!=y['result']['routes']['smart'].get('raw_sha256'):diff.append(x['index'])
 comparisons.append(dict(label='kira-baseline-fast-Smart',cases=len(prior),different_hashes=diff))
 ref=json.loads((S/'oracle-kira.json').read_text());diff=[]
 for x,y in zip(ref['cases'],fast['cases']):
  assert x['index']==y['index'] and x['input_sha256']==y['input_sha256']
  for route in ('classic','smart'):
   if x['result']['routes'][route].get('raw_sha256')!=y['result']['routes'][route].get('raw_sha256'):diff.append(dict(index=x['index'],route=route))
 comparisons.append(dict(label='kira-reference-fast',cases=len(ref['cases']),different_hashes=diff))
(E/'hash-comparisons.json').write_text(json.dumps(comparisons,indent=2)+'\n')
