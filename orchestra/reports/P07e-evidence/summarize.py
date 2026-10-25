"""Compact measured evidence; never classify unavailable oracle output as exact."""
import gzip,json
from pathlib import Path
root=Path(__file__).resolve().parents[3];s=root/'orchestra/state/P07e-radialblur-rotation-parallel'
result={'oracle':{},'matrix':{},'default_baselines':{}}
for p in sorted((s/'oracle').glob('*.json')):
 if p.name=='commands.json':continue
 v=json.loads(p.read_text());result['oracle'][p.stem]={k:v.get(k) for k in ('completed','requested','summary','status','replay_matches_saved')}
 if v.get('replays'):
  result['oracle'][p.stem]['matches']=sum(r['matches_saved'] for r in v['replays'])
  result['oracle'][p.stem]['unmatched_paths']=[r['path'] for r in v['replays'] if not r['matches_saved']]
current=s/'oracle/default.json'
if current.exists():
 now={c['index']:c['result']['routes']['smart'] for c in json.loads(current.read_text())['cases']}
 for name in ['P05b-evidence/default.json.gz','R10-evidence/fast-oracle-radial.json.gz']:
  previous=json.loads(gzip.decompress((root/'orchestra/reports'/name).read_bytes()))
  exact=[c for c in previous['cases'] if c['result']['routes']['smart']['status']=='exact']
  regressions=[c['index'] for c in exact if now[c['index']]['status']!='exact']
  changes=[c['index'] for c in exact if now[c['index']].get('raw_sha256')!=c['result']['routes']['smart'].get('raw_sha256')]
  result['default_baselines'][name]=dict(previous_exact=len(exact),exact_to_nonexact=regressions,changed_hashes=changes)
for label in ['before-matrix','after-matrix']:
 p=s/label/'matrix.jsonl'
 if p.exists():result['matrix'][label]=[{k:r.get(k) for k in ('case','situation','depth','status','result')} for r in map(json.loads,p.read_text().splitlines())]
(s/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='matrix'},indent=2))
