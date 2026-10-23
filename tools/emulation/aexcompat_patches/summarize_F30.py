#!/usr/bin/env python3
"""Bind before/after measurements; preserve every changed oracle/status boundary."""
import collections, hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
S=ROOT/'orchestra/state/F30-oracle-worker-ucrtmath'
OUT=Path(__file__).with_name('F30-evidence')
VARIANTS=['default','f29','f30']
WORKERS={'default':Path('/Users/onmk/Documents/Codex/2026-10-05/task-3/AEXCompat-containment/guest/target/release/aex-guest-worker'),'f29':Path.home()/'.cache/olm-emu/worker-F29-ssenan/aex-guest-worker','f30':Path.home()/'.cache/olm-emu/worker-F30-ucrtmath/aex-guest-worker'}
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def compact(r):
 return {'oracles':{k:{a:v[a] for a in ('status','raw_sha256') if a in v} for k,v in r.get('oracles',{'smart':r['oracle']}).items()},'routes':{k:{a:v[a] for a in ('status','raw_sha256','diff','error') if a in v} for k,v in r['routes'].items()}}
def main():
 result={'reports':{},'campaigns':[],'corpora':[],'changes':[],'findings':[]}
 labels=sorted(p.name.removeprefix('default-').removesuffix('.json') for p in S.glob('default-*.json') if p.name.endswith(('-seed1.json','-replay.json')))
 assert len(labels)==21,len(labels)
 for label in labels:
  docs=[];entries=[]
  for variant in VARIANTS:
   p=S/f'{variant}-{label}.json';doc=json.loads(p.read_text());docs.append(doc)
   expected='replay_complete' if label.endswith('-replay') else 'complete'
   assert doc['status']==expected,(p,doc['status'])
   assert doc['completed']==doc.get('requested',300),(p,doc['completed'])
   provenances=[g['provenance'] for g in doc['replay_groups']] if label.endswith('-replay') else [doc['provenance']]
   assert all(pr['worker_sha256']==sha(WORKERS[variant]) for pr in provenances),(p,'worker hash')
   result['reports'][p.name]={'sha256':sha(p),'completed':doc['completed'],'provenance':doc.get('provenance'),'replay_groups':doc.get('replay_groups')}
   rows=doc['replays'] if label.endswith('-replay') else doc['cases']
   entries.append({r.get('path',r.get('index')):r for r in rows})
  assert entries[0].keys()==entries[1].keys()==entries[2].keys()
  if label.endswith('-seed1'):
   for d in docs[1:]:
    for key,value in docs[0]['provenance'].items():
     if key.endswith('_sha256') and key not in ('worker_sha256','candidate_sha256'):
      assert d['provenance'][key]==value,(label,key,'source/input provenance changed')
  summary={'label':label,'plugin':docs[0]['plugin'],'cases':docs[0]['completed'],'variants':{},'changed_results':{},'changed_smart_oracle':{}}
  for v,d,rows in zip(VARIANTS,docs,entries):
   counts=collections.Counter(r['result']['routes']['smart']['status'] for r in rows.values())
   summary['variants'][v]={'smart':dict(counts),'matches_saved':sum(r.get('matches_saved',False) for r in rows.values()) if label.endswith('-replay') else None}
  for ai,bi,cause in [(0,1,'F29 SSE NaN propagation'),(1,2,'F30 UCRT expf/atan2f/powf imports'),(0,2,'combined')]:
   pair=f'{VARIANTS[ai]}->{VARIANTS[bi]}';changed=0;smart=0
   for key in entries[ai]:
    x,y=entries[ai][key],entries[bi][key]
    if 'input_sha256' in x:assert x['input_sha256']==y['input_sha256']
    a,b=compact(x['result']),compact(y['result'])
    if a==b:continue
    changed+=1;smart+=a['oracles']['smart']!=b['oracles']['smart']
    transitions={r:[a['routes'][r]['status'],b['routes'][r]['status']] for r in a['routes'] if a['routes'][r]['status']!=b['routes'][r]['status']}
    candidate_changes=[r for r in a['routes'] if a['routes'][r].get('raw_sha256')!=b['routes'][r].get('raw_sha256')]
    execution_changes=[r for r in a['oracles'] if a['oracles'][r]['status']!=b['oracles'][r]['status']]
    finding=bool(candidate_changes or execution_changes)
    entry={'label':label,'case':key,'pair':pair,'cause':cause if not finding else 'finding: execution/candidate boundary requires review','transitions':transitions,'before':a,'after':b}
    result['changes'].append(entry)
    if finding:result['findings'].append({'label':label,'case':key,'pair':pair,'candidate_changes':candidate_changes,'oracle_status_changes':execution_changes})
   summary['changed_results'][pair]=changed;summary['changed_smart_oracle'][pair]=smart
  result['corpora' if label.endswith('-replay') else 'campaigns'].append(summary)
 result['worker_sha256']={v:sha(p) for v,p in WORKERS.items()}
 (OUT/'measurements.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
 for group in ['campaigns','corpora']:
  for row in result[group]:print(row['label'],row['variants'],row['changed_smart_oracle'])
 print('changes',len(result['changes']),'findings',len(result['findings']))
if __name__=='__main__':main()
