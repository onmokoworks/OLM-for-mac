#!/usr/bin/env python3
"""Build an isolated SSE NaN reference variant; never changes fuzzer defaults.

Copies the requested current AEXCompat snapshot for provenance, and builds the
existing default worker's source lineage in reference-guest. That distinction
avoids introducing unrelated upstream/host/math changes into the comparison.
Build output is outside the repository (spaces break Unicorn's CMake build).
Use --register only after validation. Existing cache entries are preserved.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[3]
CACHE=Path.home()/'.cache/olm-emu'
PARENT=Path('/Users/onmk/Documents/Codex/2026-10-05/task-3/AEXCompat-containment/guest')
ORIGINAL=Path('/Users/onmk/Documents/Projects/Personal/04_Tools/AEXCompat')
PATCH=Path(__file__).with_name('F29-sse-nan-order.patch')

def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()

def copy_source(source,destination):
    def ignore(directory,names):
        d=Path(directory)
        return [n for n in names if n in ('.git','__pycache__','.venv') or n.endswith('.zip')
                or (n=='target' and d in (source,source/'guest'))]
    shutil.copytree(source,destination,ignore=ignore)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--scratch',type=Path,default=ROOT/'orchestra/state/F29-unicorn-sse-nan-propagation')
    ap.add_argument('--cache-root',type=Path,default=CACHE,help='fresh space-free cache for independent rebuilds')
    ap.add_argument('--register',action='store_true',help='register already validated final binary; no build')
    args=ap.parse_args(); scratch=args.scratch.resolve()
    assert scratch.is_relative_to(ROOT/'orchestra/state')
    scratch.mkdir(parents=True,exist_ok=True)
    cache=args.cache_root.resolve(); assert ' ' not in str(cache)
    cache.mkdir(parents=True,exist_ok=True)
    src=cache/'src-F29'; output=cache/'worker-F29-ssenan'; worker=output/'aex-guest-worker'
    if args.register:
        assert cache==CACHE, 'Only register the designated final worker'
        manifest=json.loads((scratch/'build-manifest.json').read_text())
        assert sha(worker)==manifest['worker_sha256']
        index=CACHE/'INDEX.json'
        # Lock a separate file: don't replace a locked inode during atomic write.
        import fcntl
        with (CACHE/'.F29-index.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            data=json.loads(index.read_text())
            assert not any(e['name']=='worker-F29-ssenan' for e in data['links'])
            durable=CACHE/'F29-ssenan-build.json'
            assert not durable.exists()
            durable.write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
            data['links'].append(dict(name='worker-F29-ssenan',parent='fuzzer_default_3cb4855b7b3f',parent_worker_path=str(PARENT/'target/release/aex-guest-worker'),
                worker_path=str(worker),worker_sha256=sha(worker),
                recipe='tools/emulation/aexcompat_patches/build_F29.py; F29 SSE-only NaN order',
                build_json=str(durable),matches_recorded=True))
            staged=CACHE/'INDEX.F29.json'; staged.write_text(json.dumps(data,indent=2)+'\n'); staged.replace(index)
        print('Registered',sha(worker)); return
    assert not src.exists() and not output.exists(), 'Use fresh F29 destinations; never overwrite existing evidence.'
    pressure=subprocess.check_output(['memory_pressure'],text=True)
    free=int(re.search(r'System-wide memory free percentage: (\d+)%',pressure)[1])
    assert free>=30, f'Build blocked: {free}% free (<30%)'
    copy_source(ORIGINAL,src)
    guest=src/'reference-guest'; copy_source(PARENT,guest)
    subprocess.run(['patch','-p1','-i',str(PATCH)],cwd=guest/'vendor/unicorn-engine-sys',check=True)
    output.mkdir()
    env=dict(os.environ,TMPDIR=str(scratch),TMP=str(scratch),TEMP=str(scratch),
        CARGO_BUILD_JOBS='1',CMAKE_BUILD_PARALLEL_LEVEL='1',
        CARGO_TARGET_DIR=str(output/'build'),AEXCOMPAT_BUILD_REVISION='F29-ssenan')
    cmd=['cargo','build','--manifest-path',str(guest/'Cargo.toml'),'--release','--offline','--locked','-j','1','-p','aex-guest-worker']
    with (scratch/'build.log').open('w') as log:
        subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    shutil.copy2(output/'build/release/aex-guest-worker',worker)
    manifest=dict(worker_sha256=sha(worker),parent_worker_sha256=sha(PARENT/'target/release/aex-guest-worker'),
        parent_source_revision=subprocess.check_output(['git','-C',str(PARENT),'rev-parse','HEAD'],text=True).strip(),
        patch_sha256=sha(PATCH),original_snapshot_revision=subprocess.check_output(['git','-C',str(ORIGINAL),'rev-parse','HEAD'],text=True).strip(),
        build_source=str(guest),command=cmd,memory_free_percent=free,
        source_manifest={str(p.relative_to(guest)):sha(p) for p in sorted(guest.rglob('*')) if p.is_file()})
    (scratch/'build-manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    print('Built',sha(worker),'Keep build tree only until instruction tests finish, then remove output/build.')

if __name__=='__main__': main()
