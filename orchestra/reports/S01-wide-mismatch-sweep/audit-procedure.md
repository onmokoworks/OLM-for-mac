# Evidence integrity audit

Run from the worktree root. Expected: `PASS: 50 campaigns, 15000 cases; E/M/R/U 14126/2/791/81; 5875 witnesses; 2 matching replays`. This reads the committed archives and corpus, reconstructs procedural inputs with the unchanged adapters, and validates hashes and counts without rendering.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
from pathlib import Path
import json,gzip,hashlib,sys,argparse,importlib
root=Path.cwd();base=root/'orchestra/reports/S01-wide-mismatch-sweep'
sys.dont_write_bytecode=True;sys.path.insert(0,str(root/'tools/fuzz'))
from core import load_corpus
from run import summarize
sha=lambda b:hashlib.sha256(b).hexdigest()
m=json.loads((base/'manifest.json').read_text());assert len(m['campaigns'])==50
seen=set();total=[0,0,0,0];adapters={};expected_witnesses=set()
for c in m['campaigns']:
 raw=gzip.decompress((root/c['report']).read_bytes());assert sha(raw)==c['report_sha256'];d=json.loads(raw)
 assert d['status']=='complete' and [r['index'] for r in d['cases']]==list(range(300))
 for name,h in c['framework_sha256'].items():assert sha((root/name).read_bytes())==h
 if c['plugin']=='olmdistancegradation' and c['seed']==105:
  retry=json.loads((base/'olmdistancegradation_seed105_retry.json').read_text());rs={r['index']:r for r in retry['cases']}
  assert sorted(r['index'] for r in d['cases'] if 'worker_error' in r)==[50,123]
  d['cases']=[rs.get(r['index'],r) for r in d['cases']]
 assert summarize(d['cases'])[0]==c['summary']
 for r in d['cases']:
  key=(c['plugin'],c['seed'],r['index']);assert key not in seen;seen.add(key)
  if any(v['status']=='mismatch' for v in r['result']['routes'].values()):expected_witnesses.add(key)
 route='classic' if c['plugin']=='olmsmoother' else 'smart';s=c['summary']
 v=[s.get(route+'_'+k,0) for k in ['exact','mismatch','refusal']];v+=[300-sum(v)];total=[a+b for a,b in zip(total,v)]
 if c['plugin'] not in adapters:
  opts=argparse.Namespace(max_size=256,case_timeout=10,main=root.parent.parent,worker=Path(c['provenance']['worker_path']))
  adapters[c['plugin']]=importlib.import_module('adapters.'+c['plugin']).Adapter(opts)
assert len(seen)==15000 and total==[14126,2,791,81]
assert len(m['witnesses'])==5875
assert expected_witnesses=={(w['plugin'],w['seed'],w['index']) for w in m['witnesses']}
for w in m['witnesses']:
 p=root/w['path'];assert sha(p.read_bytes())==w['sha256'];case,saved=load_corpus(p,adapters[w['plugin']])
 assert len(case['pixels'])==case['geometry'][0]*case['geometry'][1]*case['depth']//8*4
 assert all(saved['result']['routes'][r]['status']=='mismatch' for r in w['routes'])
for name in ['dg','radial']:
 d=json.loads((base/f'replay_{name}.json').read_text());assert d['replay_matches_saved'] and d['completed']==1
 assert d['replays'][0]['result']['routes']['smart']['status']=='mismatch'
print('PASS: 50 campaigns, 15000 cases; E/M/R/U 14126/2/791/81; 5875 witnesses; 2 matching replays')
PY
```
