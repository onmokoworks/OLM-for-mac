#!/usr/bin/env python3
"""Validate retained P00b evidence (not a numerical conformance gate)."""
import collections,gzip,json
from pathlib import Path
import ae_realism_audit as audit
root=audit.ROOT/'orchestra/reports/P00b-evidence'
for phase in ('baseline','matrix'):
 with gzip.open(root/(phase+'.jsonl.gz'),'rt') as f:rows=[json.loads(line) for line in f]
 manifest=json.loads((root/(phase+'-manifest.json')).read_text())
 identities=[(r['plugin'],r['case'],r['situation'],r['depth']) for r in rows]
 assert len(identities)==len(set(identities)), 'duplicate case identities'
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
cache=Path.home()/'.cache/olm-emu/P00b'
assert audit.sha(cache/'plugin-host')==manifest['host_sha256']
for plugin,expected_hash in manifest['bundles'].items():
 name=audit.PLUGINS[plugin]
 assert audit.sha(cache/'xcode'/name/'products'/(name+'.plugin')/'Contents/MacOS'/name)==expected_hash,plugin
print('Cached host and all ten bundle hashes match.')
print('Evidence integrity OK; this does not assert pixel-exactness or native AE compatibility.')
