#!/usr/bin/env python3
"""Retain verified Universal bundles in the shared artifact cache, never install in AE."""
import hashlib, json, os, shutil, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];S=ROOT/'orchestra/state/I03-integration-check'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
builds=json.loads((S/'bundles/bundle-builds.json').read_text())
hashes={r['plugin']:sha(S/'bundles/xcode'/r['plugin']/'products'/(r['plugin']+'.plugin')/'Contents/MacOS'/r['plugin']) for r in builds}
fingerprint=hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest()[:16]
cache=Path.home()/'.cache/olm-emu'/('I03-bundles-'+fingerprint)
for name,digest in hashes.items():
    src=S/'bundles/xcode'/name/'products'/(name+'.plugin')
    dst=cache/'bundles/xcode'/name/'products'/(name+'.plugin')
    if not dst.exists():dst.parent.mkdir(parents=True,exist_ok=True);shutil.copytree(src,dst)
    assert sha(dst/'Contents/MacOS'/name)==digest
host=Path.home()/'.cache/olm-emu/worker-F51-x86host/plugin-host'
record=dict(name=cache.name,worker_path=str(host),worker_sha256=sha(host),capability='existing F51 plugin-only host plus I03 verified Universal bundles; no new AEX worker',build_json=str(cache/'build.json'),bundles_path=str(cache/'bundles'),bundle_sha256=hashes)
if not (cache/'build.json').exists():
    metadata=dict(record,source_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),build_commands=builds,slice_report_sha256=sha(S/'F51/summary.json'),arm64_reports_sha256={p.name:sha(p) for p in S.glob('*-plugin-bundle.json')})
    (cache/'build.json').write_text(json.dumps(metadata,indent=2)+'\n')
index=cache.parent/'INDEX.json';data=json.loads(index.read_text())
if not any(r.get('name')==record['name'] for r in data['links']):
    shutil.copy2(index,S/'worker-index-before-I03.json')
    data['links'].append(record)
    temporary=S/'worker-index-after-I03.json';temporary.write_text(json.dumps(data,indent=2)+'\n');os.replace(temporary,index)
(S/'cached-bundles.json').write_text(json.dumps(record,indent=2)+'\n')
print(cache)
