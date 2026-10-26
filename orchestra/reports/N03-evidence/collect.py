"""Compress completed reports and summarize both routes without hiding exclusions."""
import gzip,hashlib,json,shutil
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parents[3];S=R/'orchestra/state/N03-distancegradation-bilateral-refusals';E=R/'orchestra/reports/N03-evidence'
summary={'source_sha256':hashlib.sha256((R/'mac/OLMDistanceGradation/OLMDistanceGradation.cpp').read_bytes()).hexdigest(),'campaigns':[],'replay':[]}
for p in sorted(S.glob('final-*.json')):
 if p.stem.endswith('-revalidated'):continue
 d=json.loads(p.read_text());summary['campaigns'].append(dict(name=p.stem,completed=d['completed'],summary=d['summary'],depths=dict(Counter(str(c['depth']) for c in d['cases'])),mac_only_refusals=sum(c['result']['oracles']['smart']['status']=='ok' and c['result']['routes']['smart']['status']=='refusal' for c in d['cases'])))
for p in sorted(S.glob('replay-[0-9]*.json')):
 d=json.loads(p.read_text());counts=Counter();transitions=Counter();regressions=[]
 for row in d.get('replays',[]):
  saved=json.loads(Path(row['path']).read_text())['result']['routes']
  for route,current in row['result']['routes'].items():
   counts[route+'_'+current['status']]+=1
   if route in saved:
    old=saved[route];transitions[route+':'+old['status']+'->'+current['status']]+=1
    if old['status']=='exact' and current['status']!='exact':
     regressions.append(dict(path=row['path'],route=route,status=current['status'],same_candidate_hash=old.get('raw_sha256')==current.get('raw_sha256')))
 summary['replay'].append(dict(name=p.stem,completed=d['completed'],counts=dict(counts),transitions=dict(transitions),exact_to_nonexact=regressions))
for name in ('default','default-baseline','refusal38'):
 p=S/(name+'.json')
 if p.exists():
  d=json.loads(p.read_text())
  summary[name]=dict(routes=len(d),exact_to_nonexact=sum(x['regression'] for x in d)) if isinstance(d,list) else d.get('summary',{'status':d['status']})
p=S/'ref-vs-fast/olmdistancegradation/summary.json'
if p.exists():summary['ref_vs_fast']=json.loads(p.read_text())['counts']
if (E/'revalidated-summary.json').exists():summary['final_campaign_validation']=json.loads((E/'revalidated-summary.json').read_text())
if (S/'replay-final.json').exists():
 d=json.loads((S/'replay-final.json').read_text());summary['final_replay']={k:d[k] for k in ('completed','counts','transitions')}
if (S/'default-baseline.json').exists() and (S/'default-revalidated.json').exists():
 baseline=json.loads((S/'default-baseline.json').read_text());final={r['index']:r for r in json.loads((S/'default-revalidated.json').read_text())['cases']}
 summary['default_final_regressions']=sum(r['baseline_exact'] and final[r['index']]['routes'][r['route']]['status']!='exact' for r in baseline)
(E/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
paths=list(S.glob('final-*.json'))+list(S.glob('replay-*.json'))+[S/n for n in ('default.json','default-baseline.json','refusal38.json','focused-v1-26031.json','default-revalidated.json')]+list((S/'bilateral').glob('*.json'))+list((S/'ref-vs-fast/olmdistancegradation').glob('*.json*'))
for p in paths:
 if p.is_file():
  name=('ref-vs-fast-' if 'ref-vs-fast' in p.parts else 'bilateral-' if p.parent.name=='bilateral' else '')+p.name+'.gz'
  with p.open('rb') as src,gzip.open(E/name,'wb') as dest:shutil.copyfileobj(src,dest)
print(json.dumps(summary,indent=2))
