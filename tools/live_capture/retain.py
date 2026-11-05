#!/usr/bin/env python3
"""Retain the tested bundles in the shared cache; never install into AE."""
import fcntl,hashlib,json,os,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
STATE=ROOT/'orchestra/state/T22-live-world-capture-dg-kirakira'
CACHE=Path.home()/'.cache/olm-emu'
commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
name='T22-live-world-capture-'+commit[:8]
dest=CACHE/name
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
if dest.exists():raise SystemExit('Refusing to overwrite retained artifacts: '+str(dest))
dest.mkdir()
manifest={'name':name,'kind':'live-capture-bundles','source_commit':commit,'bundles_path':str(dest),
          'recipe':'python3 tools/live_capture/build.py && python3 tools/live_capture/self_test.py && python3 tools/live_capture/retain.py',
          'bundle_sha256':{}}
for plugin in ('OLMDistanceGradation','OLMKiraKira'):
    source=STATE/'build'/(plugin+'.plugin');target=dest/source.name
    shutil.copytree(source,target,symlinks=True)
    binary=Path('Contents/MacOS')/plugin
    expected=sha(source/binary)
    if sha(target/binary)!=expected:raise RuntimeError('retention hash mismatch')
    manifest['bundle_sha256'][plugin]=expected
(dest/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
with (CACHE/'INDEX.lock').open('a') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX)
    index=CACHE/'INDEX.json';data=json.loads(index.read_text())
    # Retained INDEX uses a top-level artifacts array on this machine.
    arrays=[key for key,value in data.items() if isinstance(value,list) and any(isinstance(x,dict) and 'name' in x for x in value)]
    if len(arrays)!=1:raise RuntimeError('ambiguous worker index schema')
    data[arrays[0]].append(manifest)
    temporary=CACHE/('INDEX.T22-'+str(os.getpid())+'.json')
    with temporary.open('x') as out:
        json.dump(data,out,indent=2);out.write('\n');out.flush();os.fsync(out.fileno())
    os.replace(temporary,index)
(STATE/'retained.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(dest)
