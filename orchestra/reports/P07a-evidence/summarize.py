"""Retain compact evidence; source reports remain in ticket scratch."""
import hashlib,json,re,shutil
from pathlib import Path
r=Path(__file__).resolve().parents[3];s=r/'orchestra/state/P07a-parallel-helper-kirakira';e=Path(__file__).resolve().parent
summary={}
for name in ['default','realistic-1','realistic-20261025','realistic-v2-1','realistic-v2-20261025','odd','odd-wide','replay-default','replay-gate-off','replay-gate-reductions','replay-realistic','replay-odd']:
 p=s/(name+'.json')
 if not p.exists():continue
 d=json.loads(p.read_text());out={k:d[k] for k in ['status','requested','completed','summary','replay_matches_saved','seed','provenance','replay_groups'] if k in d}
 out['report_sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
 if 'replays' in d:
  out['replays']=[dict(path=v['path'],matches_saved=v['matches_saved']) for v in d['replays']]
 else:
  out['smart_rows']=[]
  for v in d['cases']:
   result=v['result'];smart=result['routes']['smart'];oracle=result.get('oracles',{}).get('smart',result['oracle'])
   out['smart_rows'].append(dict(index=v['index'],input_sha256=v['input_sha256'],candidate_status=smart['status'],oracle_status=oracle['status'],candidate_sha256=smart.get('raw_sha256'),oracle_sha256=oracle.get('raw_sha256')))
  out['mac_only_refusals']=sum(v['candidate_status']=='refusal' and v['oracle_status']=='ok' for v in out['smart_rows'])
 summary[name]=out
units={}
for label in ['before','before-sdk','after','original-clean']:
 p=s/('units-'+label+'.log')
 if p.exists():
  t=p.read_text();units[label]=dict(tests=re.findall(r'Ran .* tests in .*',t),result=re.findall(r'FAILED .*|^OK.*',t,re.M),failures=re.findall(r'^(?:FAIL|ERROR): (.*)$',t,re.M),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
summary['units']=units
(e/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
for source,target in [('before.sample.txt','before.sample.txt'),('before/matrix.jsonl','before-matrix.jsonl'),('after/matrix.jsonl','after-matrix.jsonl'),('before/matrix-manifest.json','before-manifest.json'),('after/matrix-manifest.json','after-manifest.json'),('threads/results.json','thread-hashes.json'),('original/results.json','original-hashes.json'),('warp-bench.log','warp-bench.txt'),('concurrent.log','concurrent.txt'),('verify-commands.json','verify-commands.json'),('replay-commands.json','replay-commands.json'),('correction-commands.json','correction-commands.json'),('frame-hashes/results.json','frame-hashes.json'),('source-after/matrix.jsonl','source-after-matrix.jsonl'),('source-after/matrix-manifest.json','source-after-manifest.json'),('source-before/matrix.jsonl','source-before-matrix.jsonl'),('source-before/matrix-manifest.json','source-before-manifest.json')]:
 if (s/source).exists():shutil.copy2(s/source,e/target)
print({k:{f:v.get(f) for f in ('completed','summary','replay_matches_saved','mac_only_refusals')} for k,v in summary.items() if k!='units'})
