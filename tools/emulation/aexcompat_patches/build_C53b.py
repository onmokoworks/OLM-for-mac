#!/usr/bin/env python3
"""Build configurable read-only resident watches from the retained F49-v2 source."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[3]
CACHE = Path.home()/'.cache/olm-emu'
SCRATCH = ROOT/'orchestra/state/C53b-radial-trace-worker'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--rebuild', action='store_true', help='Replace this ticket’s own registered build')
    args = ap.parse_args()
    SCRATCH.mkdir(parents=True, exist_ok=True)
    parent = CACHE/'src-F49-v2/reference-guest'
    src = CACHE/'src-C53b/reference-guest'
    build = CACHE/'build-C53b'
    out = CACHE/'worker-C53b-trace'
    expected = json.loads((CACHE/'worker-F49-trace-v2/build.json').read_text())['source_manifest']
    assert {str(p.relative_to(parent)):sha(p) for p in parent.rglob('*') if p.is_file()} == expected
    if args.rebuild:
        previous = json.loads((out/'build.json').read_text())
        assert sha(out/'aex-guest-worker') == previous['worker_sha256']
        assert {str(p.relative_to(src)):sha(p) for p in src.rglob('*') if p.is_file()} == previous['source_manifest']
        shutil.rmtree(src.parent)
    assert not any(p.exists() for p in (src.parent, build))
    assert args.rebuild or not out.exists()
    shutil.copytree(parent.parent, src.parent)
    patch = Path(__file__).with_name('C53b-resident-watches.patch')
    subprocess.run(['patch', '-p1', '-i', str(patch)], cwd=src, check=True)
    pressure = subprocess.check_output(['memory_pressure'], text=True)
    (SCRATCH/'memory-pressure.txt').write_text(pressure)
    free = int(re.search(r'System-wide memory free percentage: (\d+)%', pressure)[1])
    assert free >= 30, free
    env = dict(os.environ, TMPDIR=str(SCRATCH), TMP=str(SCRATCH), TEMP=str(SCRATCH),
               CARGO_BUILD_JOBS='1', CMAKE_BUILD_PARALLEL_LEVEL='1',
               CARGO_TARGET_DIR=str(build), AEXCOMPAT_BUILD_REVISION='C53b-trace')
    cmd = ['cargo','build','--manifest-path',str(src/'Cargo.toml'),'--release','--offline','--locked',
           '-j','1','-p','aex-guest-worker','--bin','aex-guest-worker']
    try:
        with (SCRATCH/'build.log').open('w') as log:
            subprocess.run(cmd, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
        out.mkdir(exist_ok=True)
        shutil.copy2(build/'release/aex-guest-worker', out/'aex-guest-worker.next')
        (out/'aex-guest-worker.next').replace(out/'aex-guest-worker')
    finally:
        shutil.rmtree(build, ignore_errors=True)
    manifest = dict(worker_sha256=sha(out/'aex-guest-worker'),
                    parent_worker_sha256=sha(CACHE/'worker-F49-trace-v2/aex-guest-worker'),
                    patch_sha256=sha(patch), memory_free_percent=free, command=cmd,
                    source_manifest={str(p.relative_to(src)):sha(p) for p in src.rglob('*') if p.is_file()})
    (out/'build.json').write_text(json.dumps(manifest, indent=2)+'\n')
    with (CACHE/'.index.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        path = CACHE/'INDEX.json'
        data = json.loads(path.read_text())
        if args.rebuild:
            data['links'] = [e for e in data['links'] if e['name'] != out.name]
        assert not any(e['name']==out.name for e in data['links'])
        data['links'].append(dict(name=out.name, parent='worker-F49-trace-v2',
            worker_path=str(out/'aex-guest-worker'), worker_sha256=manifest['worker_sha256'],
            build_json=str(out/'build.json'), recipe='tools/emulation/aexcompat_patches/build_C53b.py',
            matches_recorded=True))
        staged = CACHE/'INDEX.C53b.json'
        staged.write_text(json.dumps(data, indent=2)+'\n')
        staged.replace(path)
    print(json.dumps({k:v for k,v in manifest.items() if k!='source_manifest'}))

if __name__ == '__main__':
    main()
