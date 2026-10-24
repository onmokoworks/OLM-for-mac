#!/usr/bin/env python3
"""Compact the retained acceptance observations without changing classifications."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];E=ROOT/'orchestra/reports/P04b2-evidence'
result={'campaigns':{},'replays':{},'unit_changes':[]}
for p in sorted(E.glob('*.json')):
 d=json.loads(p.read_text())
 if not isinstance(d,dict):continue
 if 'summary' in d:
  result['campaigns'][p.stem]={'completed':d['completed'],'summary':d['summary'],'smart_non_exact':[
   {'index':r['index'],'seed':r['seed'],'geometry':r['geometry'],'result':r['result']['routes']['smart'],'oracle':r['result'].get('oracles',{}).get('smart',r['result']['oracle'])}
   for r in d['cases'] if r['result']['routes']['smart']['status']!='exact']}
 if isinstance(d.get('replays'),list):
  result['replays'][p.stem]={'completed':d['completed'],'requested':d['requested'],'matches':d['replay_matches_saved'],'different':[r['path'] for r in d['replays'] if not r['matches_saved']]}
a=json.loads((E/'units-before.json').read_text());b=json.loads((E/'units-after.json').read_text())
result['units']={'files':len(b),'before_pass':sum(r['returncode']==0 for r in a),'after_pass':sum(r['returncode']==0 for r in b)}
result['unit_changes']=[x['file'] for x,y in zip(a,b) if x['returncode']!=y['returncode']]
old=[json.loads(l) for l in (ROOT/'orchestra/reports/F53-evidence/survey-auto-olmdirectionalblur.jsonl').read_text().splitlines()]
new=json.loads((E/'realistic-v2-1.json').read_text())['cases']
result['F53_refusals_now_exact']=[x['index'] for x,y in zip(old,new) if x['result']['routes']['smart']['status']=='refusal' and y['result']['routes']['smart']['status']=='exact']
(E/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
for label,d in result['campaigns'].items():print(label,d['completed'],{k:v for k,v in d['summary'].items() if k.startswith('smart_')})
for label,d in result['replays'].items():print(label,d['completed'],d['requested'],d['matches'],len(d['different']))
print('units',result['units'],'changes',result['unit_changes']);print('F53 refusals resolved',len(result['F53_refusals_now_exact']))
