#!/usr/bin/env python3
"""Build isolated F46 + F52 geometry worker; never change default worker."""
import argparse, fcntl, hashlib, json, os, re, shutil, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
CACHE=Path.home()/'.cache/olm-emu'
S=ROOT/'orchestra/state/F52-oracle-downsample-geometry'
def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def tree(p): return {str(f.relative_to(p)):sha(f) for f in sorted(p.rglob('*')) if f.is_file()}
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--register',action='store_true')
    args=ap.parse_args(); S.mkdir(parents=True,exist_ok=True)
    parent=CACHE/'src-F46/reference-guest'; source=CACHE/'src-F52/reference-guest'
    build=CACHE/'build-F52'; out=CACHE/'worker-F52-geom'; binary=out/'aex-guest-worker'
    if args.register:
        manifest=json.loads((out/'build.json').read_text()); assert sha(binary)==manifest['worker_sha256']
        with (CACHE/'.index.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            path=CACHE/'INDEX.json'; data=json.loads(path.read_text())
            assert not any(x['name']=='worker-F52-geom' for x in data['links'])
            data['links'].append(dict(name='worker-F52-geom',parent='worker-F46-pow',worker_path=str(binary),worker_sha256=sha(binary),build_json=str(out/'build.json'),recipe='python3 tools/emulation/aexcompat_patches/build_F52.py',matches_recorded=True))
            staged=CACHE/'INDEX.F52.json'; staged.write_text(json.dumps(data,indent=2)+'\n'); staged.replace(path)
        print('Registered',sha(binary)); return
    assert not binary.exists() and not build.exists()
    expected=json.loads((CACHE/'F46-pow-build.json').read_text())['source_manifest']
    assert tree(parent)==expected, 'F46 source drift'
    if not source.exists():
        shutil.copytree(parent,source)
        subprocess.run(['patch','-p1','-i',str(HERE/'F52-geometry.patch')],cwd=source,check=True)
    pressure=subprocess.check_output(['memory_pressure'],text=True)
    (S/'memory-pressure.txt').write_text(pressure)
    free=int(re.search(r'System-wide memory free percentage: (\d+)%',pressure)[1])
    assert free>=30, f'Build blocked: {free}% free'
    out.mkdir(parents=True,exist_ok=True)
    env=dict(os.environ,TMPDIR=str(S),TMP=str(S),TEMP=str(S),CARGO_BUILD_JOBS='1',CMAKE_BUILD_PARALLEL_LEVEL='1',CARGO_TARGET_DIR=str(build),AEXCOMPAT_BUILD_REVISION='F52-geometry')
    cmd=['cargo','build','--manifest-path',str(source/'Cargo.toml'),'--release','--offline','--locked','-j','1','-p','aex-guest-worker','--bin','aex-guest-worker']
    try:
        with (S/'rebuild.log').open('w') as log: subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
        shutil.copy2(build/'release/aex-guest-worker',binary)
        manifest=dict(worker_sha256=sha(binary),parent_worker_sha256=sha(CACHE/'worker-F46-pow/aex-guest-worker'),patch_sha256=sha(HERE/'F52-geometry.patch'),source_manifest=tree(source),memory_free_percent=free,command=cmd)
        (out/'build.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
        print('Built',sha(binary))
    finally:
        if build.exists(): shutil.rmtree(build)
if __name__=='__main__': main()
