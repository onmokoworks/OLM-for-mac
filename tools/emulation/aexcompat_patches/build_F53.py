#!/usr/bin/env python3
"""Build isolated F53 cropped checkout geometry worker; never change default worker."""
import argparse, fcntl, hashlib, json, os, re, shutil, subprocess, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
CACHE=Path.home()/'.cache/olm-emu'
S=ROOT/'orchestra/state/F53-oracle-cropped-checkout'
def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def tree(p): return {str(f.relative_to(p)):sha(f) for f in sorted(p.rglob('*')) if f.is_file()}
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--register',action='store_true')
    ap.add_argument('--verify-source',action='store_true')
    args=ap.parse_args(); S.mkdir(parents=True,exist_ok=True)
    parent=CACHE/'src-F52c/reference-guest'; source=CACHE/'src-F53/reference-guest'
    build=CACHE/'build-F53'; out=CACHE/'worker-F53-geom'; binary=out/'aex-guest-worker'
    if args.verify_source:
        expected=json.loads((out/'build.json').read_text())
        with tempfile.TemporaryDirectory(prefix='source-check-',dir=S) as name:
            clean=Path(name)/'source';shutil.copytree(parent,clean)
            subprocess.run(['patch','-p1','-i',str(HERE/'F53-checkout.patch')],cwd=clean,check=True,stdout=subprocess.DEVNULL)
            assert tree(clean)==tree(source)==expected['source_manifest'], 'source / patch / build manifest mismatch'
        assert sha(binary)==expected['worker_sha256']
        assert sha(HERE/'F53-checkout.patch')==expected['patch_sha256']
        print('PASS source/patch/build binding',sha(binary));return
    if args.register:
        manifest=json.loads((out/'build.json').read_text()); assert sha(binary)==manifest['worker_sha256']
        with (CACHE/'.index.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            path=CACHE/'INDEX.json'; data=json.loads(path.read_text())
            assert not any(x['name']=='worker-F53-geom' for x in data['links'])
            data['links'].append(dict(name='worker-F53-geom',parent='worker-F52c-geom',worker_path=str(binary),worker_sha256=sha(binary),build_json=str(out/'build.json'),recipe='python3 tools/emulation/aexcompat_patches/build_F53.py',matches_recorded=True))
            staged=CACHE/'INDEX.F53.json'; staged.write_text(json.dumps(data,indent=2)+'\n'); staged.replace(path)
        print('Registered',sha(binary)); return
    assert not binary.exists() and not build.exists()
    expected=json.loads((CACHE/'worker-F52c-geom/build.json').read_text())['source_manifest']
    assert tree(parent)==expected, 'F52 source drift'
    with tempfile.TemporaryDirectory(prefix='source-check-',dir=S) as name:
        clean=Path(name)/'source';shutil.copytree(parent,clean)
        subprocess.run(['patch','-p1','-i',str(HERE/'F53-checkout.patch')],cwd=clean,check=True)
        if source.exists():
            assert tree(source)==tree(clean), 'F53 source drift'
        else:
            shutil.copytree(clean,source)
    pressure=subprocess.check_output(['memory_pressure'],text=True)
    (S/'memory-pressure.txt').write_text(pressure)
    free=int(re.search(r'System-wide memory free percentage: (\d+)%',pressure)[1])
    assert free>=30, f'Build blocked: {free}% free'
    out.mkdir(parents=True,exist_ok=True)
    env=dict(os.environ,TMPDIR=str(S),TMP=str(S),TEMP=str(S),CARGO_BUILD_JOBS='1',CMAKE_BUILD_PARALLEL_LEVEL='1',CARGO_TARGET_DIR=str(build),AEXCOMPAT_BUILD_REVISION='F53-geometry')
    cmd=['cargo','build','--manifest-path',str(source/'Cargo.toml'),'--release','--offline','--locked','-j','1','-p','aex-guest-worker','--bin','aex-guest-worker']
    try:
        with (S/'rebuild.log').open('w') as log: subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
        shutil.copy2(build/'release/aex-guest-worker',binary)
        manifest=dict(worker_sha256=sha(binary),parent_worker_sha256=sha(CACHE/'worker-F52c-geom/aex-guest-worker'),patch_sha256=sha(HERE/'F53-checkout.patch'),source_manifest=tree(source),memory_free_percent=free,command=cmd)
        (out/'build.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
        print('Built',sha(binary))
    finally:
        if build.exists(): shutil.rmtree(build)
if __name__=='__main__': main()
