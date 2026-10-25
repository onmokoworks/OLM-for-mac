"""Retain this candidate bundle for reproducible measurements, not as an oracle."""
import fcntl, hashlib, json, shutil
from pathlib import Path
root=Path(__file__).resolve().parents[3]
s=root/'orchestra/state/P07e-radialblur-rotation-parallel/bundle'
cache=Path.home()/'.cache/olm-emu/P07e-radialblur-rotation-parallel'
cache.mkdir(exist_ok=True)
rel=Path('xcode/OLMRadialBlur/products/OLMRadialBlur.plugin')
shutil.copytree(s/rel,cache/rel,dirs_exist_ok=True)
shutil.copy2(s/'bundle-builds.json',cache/'bundle-builds.json')
host=cache/'plugin-host'
if not host.exists():host.symlink_to(Path.home()/'.cache/olm-emu/P05b-radialblur-simd/plugin-host')
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
record=dict(name=cache.name,worker_path=str(host),worker_sha256=digest(host),bundles_path=str(cache),build_json=str(cache/'bundle-builds.json'),capability='P07e candidate measurement bundle; not an oracle',bundle_sha256={'OLMRadialBlur':digest(cache/rel/'Contents/MacOS/OLMRadialBlur')},source_sha256={str(p.relative_to(root)):digest(p) for p in [root/'mac/OLMRadialBlur/OLMRadialBlur.cpp',root/'mac/OLMRadialBlur/RadialRotationRows.h',root/'core/olm_parallel.h']})
(cache/'build.json').write_text(json.dumps(record,indent=2)+'\n')
with (cache.parent/'INDEX.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX)
 index=cache.parent/'INDEX.json';data=json.loads(index.read_text())
 data['links']=[r for r in data['links'] if r['name']!=cache.name]+[record]
 index.write_text(json.dumps(data,indent=2)+'\n')
print(record['bundle_sha256'])
