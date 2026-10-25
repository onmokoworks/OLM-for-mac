"""Retain reproducible Blur evidence and register the completed candidate bundle."""
import gzip,hashlib,json,shutil,fcntl
from pathlib import Path
r=Path(__file__).resolve().parents[3];s=r/'orchestra/state/P07d-distancegradation-blur-colorkey-threading';e=Path(__file__).parent
cache=Path.home()/'.cache/olm-emu/P07d-key'
shutil.copytree(s/'key-bundle-after/xcode',cache/'xcode',dirs_exist_ok=True)
link=cache/'plugin-host'
if not link.exists():link.symlink_to(Path.home()/'.cache/olm-emu/P00b/plugin-host')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
record=dict(name=cache.name,worker_path=str(link),worker_sha256=sha(link),bundles_path=str(cache),bundle_sha256={'OLMColorKey':sha(cache/'xcode/OLMColorKey/products/OLMColorKey.plugin/Contents/MacOS/OLMColorKey')},source_sha256={str(p.relative_to(r)):sha(p) for p in [r/'mac/OLMColorKey/OLMColorKey.cpp',r/'core/olm_parallel.h',r/'tools/perf/ref_vs_fast.py'] if p.is_file()},capability='P07d eight-task ColorKey candidate; P00b host reused; not an AEX oracle',recipe='python3 orchestra/reports/P07d-evidence/build_key.py && python3 orchestra/reports/P07d-evidence/retain_key.py')
(cache/'build.json').write_text(json.dumps(record,indent=2)+'\n')
with (cache.parent/'INDEX.json').open('r+') as f:
 fcntl.flock(f,fcntl.LOCK_EX);data=json.load(f);data['links']=[v for v in data['links'] if v['name']!=cache.name]+[record];f.seek(0);json.dump(data,f,indent=2);f.write('\n');f.truncate()
(e/'key-cache.json').write_text(json.dumps(record,indent=2)+'\n')
paths=[*s.glob('key-*.json'),*s.glob('key-*.log'),s/'key-threads/results.json',s/'key-profile-before.txt']
for folder in ('key-before','key-after','key-ref-before/olmcolorkey','key-ref-after/olmcolorkey','key-units-before','key-units-after','key-functions-before','key-functions-after'):
 paths.extend((s/folder).glob('*.json'));paths.extend((s/folder).glob('*.jsonl'));paths.extend((s/folder).glob('*.log'))
for p in paths:
 if p.exists():
  name=str(p.relative_to(s)).replace('/','-')+'.gz'
  with p.open('rb') as i,gzip.open(e/name,'wb') as o:shutil.copyfileobj(i,o)
print('retained',record['bundle_sha256'])
