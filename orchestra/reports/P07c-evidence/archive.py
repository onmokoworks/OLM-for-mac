"""Retain evidence and register the initial experimental bundle (not an oracle).
Run under lockf -k ~/.cache/olm-emu/index.lock.
"""
import gzip,hashlib,json,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[3];S=R/'orchestra/state/P07c-smoother-threading';E=R/'orchestra/reports/P07c-evidence'
for p in sorted(S.rglob('*')):
    if not p.is_file() or p.suffix not in ('.json','.jsonl','.log','.txt'):continue
    if any(part in ('ucrtmath','xcode','geometry-shim') for part in p.relative_to(S).parts):continue
    if p.name in ('params.txt','parameters.txt'):continue
    name='__'.join(p.relative_to(S).parts)+'.gz'
    with p.open('rb') as src,(E/name).open('wb') as out,gzip.GzipFile(filename='',mode='wb',fileobj=out,mtime=0) as dst:shutil.copyfileobj(src,dst)
cache=Path.home()/'.cache/olm-emu';identity='P07c-smooth-initial-experimental';target=cache/identity;target.mkdir(exist_ok=True)
relative=Path('xcode/OLMSmoother/products/OLMSmoother.plugin')
shutil.copytree(S/'candidate'/relative,target/relative,dirs_exist_ok=True)
host=target/'plugin-host'
if not host.exists():host.symlink_to(cache/'P00b/plugin-host')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
record=dict(name=identity,bundles_path=str(target),worker_path=str(host),worker_sha256=sha(host),
 bundle_sha256={'OLMSmoother':sha(target/relative/'Contents/MacOS/OLMSmoother')},
 source_path='mac/OLMSmoother/Mac/OLMSmoother_port.cpp',
 source_sha256=json.loads((E/'candidate-source.json').read_text())['initial_source_sha256'],
 patch_path='orchestra/reports/P07c-evidence/candidate-initial.patch',patch_sha256=sha(E/'candidate-initial.patch'),
 capability='Experimental 32-row classifier threading; NOT accepted, NOT an AEX oracle; MFR throughput regression',
 recipe='Apply candidate-initial.patch, then tools/fuzz/build_F47_bundles.py --plugins OLMSmoother --scratch orchestra/state/P07c-smoother-threading/candidate')
(target/'build.json').write_text(json.dumps(record,indent=2)+'\n');(E/'cache.json').write_text(json.dumps(record,indent=2)+'\n')
p=cache/'INDEX.json';index=json.loads(p.read_text());index['links']=[r for r in index['links'] if r['name']!=identity]+[record]
q=cache/'INDEX.P07c.pending.json';q.write_text(json.dumps(index,indent=2)+'\n');q.replace(p)
print('Archived evidence and registered',identity)
