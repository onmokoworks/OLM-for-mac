"""Archive reproducible measurements and assert acceptance without reclassification."""
import gzip,hashlib,json,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[3];E=Path(__file__).resolve().parent
S=R/'orchestra/state/N02-olmdirectionalblur-nightly-20261025'
summary={'campaigns':{},'corpora':{},'source_sha256':{f:hashlib.sha256((R/f).read_bytes()).hexdigest() for f in ['core/dblur_frontonly.cpp','core/dblur_rowdriver.cpp']}}
def archive(p):
 with p.open('rb') as i,gzip.open(E/(p.name+'.gz'),'wb') as o:shutil.copyfileobj(i,o)
labels=[f'{sampler}-{seed}' for sampler in ['realistic','realistic-v2','odd-even-v1'] for seed in [2026102601,2026102602,2026102603]]+['default-1']
for label in labels:
 p=S/(label+'.json');d=json.loads(p.read_text())
 assert d['completed']==d['requested']
 for f,h in summary['source_sha256'].items():assert d['provenance']['dependencies_sha256'][f]==h,(label,f)
 assert d['summary'].get('smart_mismatch',0)==0,(label,d['summary'])
 mac_only=[c['index'] for c in d['cases'] if c['result']['oracle']['status']=='ok' and c['result']['routes']['smart']['status']=='refusal']
 assert not mac_only,(label,mac_only)
 summary['campaigns'][label]={'completed':d['completed'],'summary':d['summary'],'mac_only_refusals':mac_only}
 archive(p)
for p in sorted(S.glob('corpus-*.json')):
 d=json.loads(p.read_text());assert d['replay_matches_saved'],p
 summary['corpora'][p.stem]=dict(completed=d['completed'],matches=True)
 archive(p)
for p in sorted(S.glob('reference-*.json')):
 d=json.loads(p.read_text());assert d['replay_matches_saved'],p
 archive(p)
old=json.loads((R/'orchestra/reports/P05a-evidence/default-1.json').read_text())
new=json.loads((S/'default-1.json').read_text())
regressions=[];changed=[]
for a,b in zip(old['cases'],new['cases']):
 assert a['index']==b['index'] and a['input_sha256']==b['input_sha256']
 for route,prev in a['result']['routes'].items():
  cur=b['result']['routes'][route]
  if prev['status']=='exact' and cur['status']!='exact':regressions.append([a['index'],route])
  if (prev.get('raw_sha256'),prev.get('error'))!=(cur.get('raw_sha256'),cur.get('error')):changed.append([a['index'],route])
summary['default_regression']={'baseline':'orchestra/reports/P05a-evidence/default-1.json','exact_to_nonexact':regressions,'candidate_hash_or_error_changes':changed}
assert not regressions
perf=S/'perf/olmdirectionalblur'
summary['perf']=json.loads((perf/'summary.json').read_text())
assert summary['perf']['counts']['mismatch']==0
for n in ['summary.json','builds.json','results.jsonl']:
 with (perf/n).open('rb') as i,gzip.open(E/('perf-'+n+'.gz'),'wb') as o:shutil.copyfileobj(i,o)
(E/'summary.json').write_text(json.dumps(summary,indent=2,default=str)+'\n')
print(json.dumps({'campaigns':len(labels),'corpus_cases':sum(r['completed'] for r in summary['corpora'].values()),'default':summary['default_regression'],'perf':summary['perf']['counts']},indent=2))
