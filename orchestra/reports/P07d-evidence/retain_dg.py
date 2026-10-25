"""Register both DistanceGradation bundles and retain compact, deterministic evidence."""
import fcntl,gzip,hashlib,json,shutil,subprocess
from pathlib import Path
r=Path(__file__).resolve().parents[3];s=r/'orchestra/state/P07d-distancegradation-blur-colorkey-threading';e=Path(__file__).parent
source='mac/OLMDistanceGradation/OLMDistanceGradation.cpp'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
records=[]
for before in (True,False):
 cache=Path.home()/'.cache/olm-emu'/('P07d-dg-before' if before else 'P07d-dg')
 shutil.copytree(s/('dg-bundle-before' if before else 'dg-bundle-after')/'xcode',cache/'xcode',dirs_exist_ok=True)
 link=cache/'plugin-host'
 if not link.exists():link.symlink_to(Path.home()/'.cache/olm-emu/P00b/plugin-host')
 source_bytes=subprocess.check_output(['git','show','12b78241:'+source],cwd=r) if before else (r/source).read_bytes()
 record=dict(name=cache.name,worker_path=str(link),worker_sha256=sha(link),bundles_path=str(cache),bundle_sha256={'OLMDistanceGradation':sha(cache/'xcode/OLMDistanceGradation/products/OLMDistanceGradation.plugin/Contents/MacOS/OLMDistanceGradation')},source_sha256={source:hashlib.sha256(source_bytes).hexdigest(),'core/olm_parallel.h':sha(r/'core/olm_parallel.h'),'core/olmdistancegradation_fieldgen.cpp':sha(r/'core/olmdistancegradation_fieldgen.cpp')},capability='P07d '+('pre-threading baseline' if before else 'threaded Smart row candidate')+'; P00b host reused; not an AEX oracle',recipe='python3 orchestra/reports/P07d-evidence/build_dg.py'+(' --before' if before else ''))
 (cache/'build.json').write_text(json.dumps(record,indent=2)+'\n');records.append(record)
with (Path.home()/'.cache/olm-emu/INDEX.json').open('r+') as f:
 fcntl.flock(f,fcntl.LOCK_EX);data=json.load(f);names={v['name'] for v in records};data['links']=[v for v in data['links'] if v['name'] not in names]+records;f.seek(0);json.dump(data,f,indent=2);f.write('\n');f.truncate()
(e/'dg-cache.json').write_text(json.dumps(records,indent=2)+'\n')
paths=[*s.glob('dg-*.json'),*s.glob('dg-*.log'),s/'dg-threads/results.json',s/'dg-profile-before.txt']
for folder in ('dg-before','dg-after','dg-ref-before/olmdistancegradation','dg-ref-after/olmdistancegradation','dg-units-before','dg-units-after','dg-functions-before','dg-functions-after'):
 paths.extend((s/folder).glob('*.json'));paths.extend((s/folder).glob('*.jsonl'));paths.extend((s/folder).glob('*.log'))
for p in paths:
 if p.exists():
  name=str(p.relative_to(s)).replace('/','-')+'.gz'
  with p.open('rb') as i,(e/name).open('wb') as f,gzip.GzipFile(fileobj=f,mode='wb',mtime=0) as o:shutil.copyfileobj(i,o)
print({v['name']:v['bundle_sha256'] for v in records})
