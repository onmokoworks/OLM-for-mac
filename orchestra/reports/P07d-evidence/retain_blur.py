"""Retain reproducible Blur evidence and register the completed candidate bundle."""
import gzip,hashlib,json,shutil,fcntl
from pathlib import Path
r=Path(__file__).resolve().parents[3];s=r/'orchestra/state/P07d-distancegradation-blur-colorkey-threading';e=Path(__file__).parent
cache=Path.home()/'.cache/olm-emu/P07d-blur'
shutil.copytree(s/'bundle-after/xcode',cache/'xcode',dirs_exist_ok=True)
link=cache/'plugin-host'
if not link.exists():link.symlink_to(Path.home()/'.cache/olm-emu/P00b/plugin-host')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
record=dict(name=cache.name,worker_path=str(link),worker_sha256=sha(link),bundles_path=str(cache),bundle_sha256={'OLMBlur':sha(cache/'xcode/OLMBlur/products/OLMBlur.plugin/Contents/MacOS/OLMBlur')},source_sha256={str(p.relative_to(r)):sha(p) for p in sorted((r/'core').glob('olmblur*')) if p.is_file()},capability='P07d six-task Blur candidate; P00b host reused; not an AEX oracle',recipe='python3 orchestra/reports/P07d-evidence/build_blur.py && python3 orchestra/reports/P07d-evidence/retain_blur.py')
(cache/'build.json').write_text(json.dumps(record,indent=2)+'\n')
with (cache.parent/'INDEX.json').open('r+') as f:
 fcntl.flock(f,fcntl.LOCK_EX);data=json.load(f);data['links']=[v for v in data['links'] if v['name']!=cache.name]+[record];f.seek(0);json.dump(data,f,indent=2);f.write('\n');f.truncate()
(e/'blur-cache.json').write_text(json.dumps(record,indent=2)+'\n')
paths=[*s.glob('blur-*.json'),*s.glob('blur-*.log'),s/'concurrent.log',s/'threads.log',s/'threads/results.json',s/'blur-profile-before.txt',s/'verify.log']
for folder in ('blur-before','blur-after','ref-before/olmblur','ref-after/olmblur','blur-units-before','blur-units-after'):
 paths.extend((s/folder).glob('*.json'));paths.extend((s/folder).glob('*.jsonl'));paths.extend((s/folder).glob('*.log'))
for p in paths:
 if p.exists():
  name='blur-'+str(p.relative_to(s)).replace('/','-')+'.gz'
  with p.open('rb') as i,gzip.open(e/name,'wb') as o:shutil.copyfileobj(i,o)
print('retained',record['bundle_sha256'])
