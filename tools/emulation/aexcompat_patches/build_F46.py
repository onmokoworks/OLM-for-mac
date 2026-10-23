#!/usr/bin/env python3
"""Build F45 + UCRT pow imports in an isolated cache. No default/corpus edits."""
import argparse, fcntl, hashlib, json, os, re, shutil, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
CACHE=Path.home()/'.cache/olm-emu'
S=ROOT/'orchestra/state/F46-integrate-ucrt-pow'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def tree(p):
 return {str(f.relative_to(p)):sha(f) for f in sorted(p.rglob('*')) if f.is_file()}
def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--cache-root',type=Path,default=CACHE)
 ap.add_argument('--register',action='store_true')
 args=ap.parse_args(); cache=args.cache_root.resolve(); S.mkdir(parents=True,exist_ok=True)
 assert ' ' not in str(cache)
 parent=CACHE/'src-F45/reference-guest'; source=cache/'src-F46/reference-guest'
 out=cache/'worker-F46-pow'; binary=out/'aex-guest-worker'
 if args.register:
  assert cache==CACHE
  manifest=json.loads((S/'build-manifest.json').read_text())
  assert sha(binary)==manifest['worker_sha256']
  results=json.loads((S/'shim-results.json').read_text())
  assert len(results)==4 and all(r['count']==1000000 and r['mismatches']==0 for r in results)
  with (CACHE/'.index.lock').open('a') as lock:
   fcntl.flock(lock,fcntl.LOCK_EX)
   path=CACHE/'INDEX.json'; data=json.loads(path.read_text())
   assert not any(x['name']=='worker-F46-pow' for x in data['links'])
   durable=CACHE/'F46-pow-build.json';assert not durable.exists()
   durable.write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
   data['links'].append(dict(name='worker-F46-pow',parent='worker-F45-msdouble',worker_path=str(binary),worker_sha256=sha(binary),build_json=str(durable),recipe='tools/emulation/aexcompat_patches/build_F46.py; F45 + UCRT pow; OLM_UCRT_FMA defaults to 1',matches_recorded=True))
   staged=CACHE/'INDEX.F46.json';staged.write_text(json.dumps(data,indent=2)+'\n');staged.replace(path)
  print('Registered',sha(binary));return
 assert not source.parent.exists() and not out.exists(), 'Use a fresh cache root; existing workers are never replaced'
 expected=json.loads((ROOT/'orchestra/reports/F45-evidence/build-manifest.json').read_text())['source_manifest']
 assert tree(parent)==expected, 'F45 parent source changed'
 for path in (ROOT/'ucrtmath/src').iterdir():
  if path.is_file():
   assert sha(path)==sha(parent/'crates/olm-ucrtmath/ucrtmath/src'/path.name), 'Existing math implementation changed'
 for name in ('float.c', 'tables.h', 'double.c', 'pow.c'):
  assert sha(ROOT/'ucrtmath/ms'/name)==sha(parent/'crates/olm-ucrtmath/ucrtmath/ms'/name), 'Existing MS float math changed'
 pressure=subprocess.check_output(['memory_pressure'],text=True)
 free=int(re.search(r'System-wide memory free percentage: (\d+)%',pressure)[1])
 assert free>=30, f'Build blocked at {free}% free'
 shutil.copytree(parent,source)
 subprocess.run(['patch','-p1','-i',str(HERE/'F46-pow.patch')],cwd=source,check=True)
 shutil.rmtree(source/'crates/olm-ucrtmath/ucrtmath')
 shutil.copytree(ROOT/'ucrtmath',source/'crates/olm-ucrtmath/ucrtmath')
 out.mkdir(parents=True)
 env=dict(os.environ,TMPDIR=str(S),TMP=str(S),TEMP=str(S),CARGO_BUILD_JOBS='1',CMAKE_BUILD_PARALLEL_LEVEL='1',CARGO_TARGET_DIR=str(out/'build'),AEXCOMPAT_BUILD_REVISION='F46-pow')
 cmd=['cargo','build','--manifest-path',str(source/'Cargo.toml'),'--release','--offline','--locked','-j','1','-p','aex-guest-worker','--bin','aex-guest-worker','--example','f30_import_probe']
 with (S/'rebuild.log').open('w') as log:subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
 shutil.copy2(out/'build/release/aex-guest-worker',binary)
 shutil.copy2(out/'build/release/examples/f30_import_probe',out/'f30_import_probe')
 manifest=dict(worker_sha256=sha(binary),probe_sha256=sha(out/'f30_import_probe'),parent_worker_sha256=sha(CACHE/'worker-F45-msdouble/aex-guest-worker'),patch_sha256=sha(HERE/'F46-pow.patch'),source_manifest=tree(source),memory_free_percent=free,command=cmd)
 (S/'build-manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
 shutil.rmtree(out/'build')
 print('Built',sha(binary),'; regenerable build tree removed')
if __name__=='__main__':main()
