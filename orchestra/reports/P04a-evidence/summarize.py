"""Check exact regressions, Mac-only refusals, saved replay, and unit outcomes."""
import json,re,gzip
from pathlib import Path
R=Path(__file__).resolve().parents[3];S=R/'orchestra/state/P04a-distancegradation-default-pf32'
def read(n):
 p=S/n
 return json.loads(p.read_text() if p.exists() else gzip.decompress((Path(__file__).parent/(n+'.gz')).read_bytes()))
b=read('default-before.json');a=read('default-after.json');changes=[];regress=[]
for x,y in zip(b['cases'],a['cases']):
 for route in ('classic','smart'):
  old=x['result']['routes'][route];new=y['result']['routes'][route]
  if (old.get('raw_sha256'),old.get('error'))!=(new.get('raw_sha256'),new.get('error')):changes.append([x['index'],route])
  if old['status']=='exact' and new['status']!='exact':regress.append([x['index'],route])
rows=[]
for name in ('default-after','realistic-1','realistic-10424','odd-even-2026','odd-even-2027'):
 d=read(name+'.json');bad=[];counts={}
 for c in d['cases']:
  r=c['result'];oracle=r.get('oracles',{}).get('smart',r['oracle']);status=r['routes']['smart']['status']
  key=status if oracle['status']=='ok' else 'oracle_unavailable';counts[key]=counts.get(key,0)+1
  if status=='mismatch' or (status=='refusal' and oracle['status']=='ok'):bad.append(c['index'])
 rows.append(dict(campaign=name,completed=d['completed'],counts=counts,smart_bad_indices=bad))
replays=[]
for p in sorted(S.glob('replay-*.json')):
 d=json.loads(p.read_text())
 if 'replay_matches_saved' in d:replays.append(dict(name=p.stem,completed=d['completed'],matches=d['replay_matches_saved']))
def failures(p):
 text=p.read_text() if p.exists() else gzip.decompress((Path(__file__).parent/(p.name+'.gz')).read_bytes()).decode()
 return sorted(re.findall(r'^(?:FAIL|ERROR): (.*)$',text,re.M))
before=failures(S/'units-before.log');after=failures(S/'units-after.log')
out=dict(default_route_changes=changes,exact_regressions=regress,campaigns=rows,replays=replays,unit_failure_sets_equal=before==after,unit_failure_count_before=len(before),unit_failure_count_after=len(after))
(S/'summary.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
assert not changes and not regress and all(not r['smart_bad_indices'] for r in rows)
assert all(r['matches'] for r in replays) and before==after
