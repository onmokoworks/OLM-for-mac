#!/usr/bin/env python3
"""Validate retained P00b evidence (not a numerical conformance gate)."""
import collections,gzip,json
from pathlib import Path
import ae_realism_audit as audit
root=audit.ROOT/'orchestra/reports/P00b-evidence'
bindings=[]
for phase in ('baseline','matrix'):
 with gzip.open(root/(phase+'.jsonl.gz'),'rt') as f:rows=[json.loads(line) for line in f]
 manifest=json.loads((root/(phase+'-manifest.json')).read_text())
 identities=[(r['plugin'],r['case'],r['situation'],r['depth']) for r in rows]
 assert len(identities)==len(set(identities)), 'duplicate case identities'
 bindings.append((manifest['host_sha256'],manifest['bundles']))
 names=['full','half','quarter','4k','4k-half','4k-quarter'] if phase=='baseline' else [n for n,g in audit.situations()]
 expected_ids={(p,c,n,d) for p in audit.PLUGINS for c in (['default'] if phase=='baseline' else ['default']+[f'corpus{i:02d}' for i in range(len(manifest['samples'][p]['paths']))]) for n in names for d in ((8,) if phase=='baseline' else (8,16,32))}
 assert set(identities)==expected_ids, 'missing or extra matrix cells'
 expected=60 if phase=='baseline' else sum(len(audit.situations())*3*(1+len(manifest['samples'][p]['paths'])) for p in audit.PLUGINS)
 assert len(rows)==expected,(phase,len(rows),expected)
 counts=dict(collections.Counter(r['status'] for r in rows));assert counts==manifest['counts']
 assert len(manifest['bundles'])==10
 assert manifest['timeout']==60
 assert all(x['free_percent']>=30 for x in manifest['memory'])
 if phase=='baseline':assert counts=={'ok':60}
 for r in rows:
  assert r['status'] in ('ok','refusal','pf_error','crash','host_error','timeout')
  if r['status']=='ok':assert r['result']['error']==0
  if r['status']=='timeout':assert r['wall_seconds']>=60
 print(phase,len(rows),counts)
assert bindings[0]==bindings[1], 'baseline/matrix binary identity drift'
selected=[];profiles=[]
for group in ('main','heavy'):
 selected+=json.loads((root/'profiles'/('selected-'+group+'.json')).read_text())
 profiles += [json.loads(x) for x in (root/'profiles'/('results-'+group+'.jsonl')).open()]
slow={f"{r['plugin']}-{r['selection']}-{r['situation']}-{r['depth']}" for r in selected if r['status']=='timeout' or (r['status']=='ok' and r['result']['render_seconds']>2)}
assert slow=={r['identity'] for r in profiles}
assert len(profiles)==len(slow)
for r in profiles:
 assert r['sample_returncode']==0 and r['memory_free']>=30
 assert r['status'] in ('completed','sampled_then_stopped')
 with gzip.open(root/'profiles'/(Path(r['profile']).name+'.gz'),'rt') as f:
  assert 'Sort by top of stack' in f.read()
print('All',len(profiles),'slow performance cells have successful stack samples.')
cache=Path.home()/'.cache/olm-emu/P00b'
assert audit.sha(cache/'plugin-host')==manifest['host_sha256']
for plugin,expected_hash in manifest['bundles'].items():
 name=audit.PLUGINS[plugin]
 assert audit.sha(cache/'xcode'/name/'products'/(name+'.plugin')/'Contents/MacOS'/name)==expected_hash,plugin
print('Cached host and all ten bundle hashes match.')
print('Evidence integrity OK; this does not assert pixel-exactness or native AE compatibility.')
