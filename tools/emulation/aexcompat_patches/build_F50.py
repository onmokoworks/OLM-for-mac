#!/usr/bin/env python3
"""Build the F46 source plus deterministic F50 execution limits; no default change."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
CACHE = Path.home()/'.cache/olm-emu'
S = ROOT/'orchestra/state/F50b-oracle-budget-build'
E = ROOT/'orchestra/reports/F50b-evidence'

def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def tree(path):
    return {str(p.relative_to(path)): sha(p) for p in sorted(path.rglob('*')) if p.is_file()}

def main():
    S.mkdir(parents=True, exist_ok=True)
    E.mkdir(parents=True, exist_ok=True)
    parent = CACHE/'src-F46/reference-guest'
    source = CACHE/'src-F50-budget/reference-guest'
    out = CACHE/'worker-F50-budget'
    binary = out/'aex-guest-worker'
    expected = json.loads((ROOT/'orchestra/reports/F46-evidence/build-manifest.json').read_text())['source_manifest']
    assert tree(parent) == expected, 'F46 source manifest changed'
    assert not source.parent.exists() and not out.exists(), 'Never overwrite retained workers'
    pressure = subprocess.check_output(['memory_pressure'], text=True)
    (S/'memory-pressure.log').write_text(pressure)
    free = int(re.search(r'System-wide memory free percentage: (\d+)%', pressure)[1])
    assert free >= 30, f'Build blocked at {free}% free'
    shutil.copytree(parent, source)
    subprocess.run(['patch', '-p1', '-i', str(HERE/'F50-budget.patch')], cwd=source, check=True)
    out.mkdir()
    build = CACHE/'build-F50'
    assert not build.exists(), 'Never overwrite an existing build directory'
    build.mkdir()
    env = dict(os.environ, TMPDIR=str(S), TMP=str(S), TEMP=str(S),
               CARGO_BUILD_JOBS='1', CMAKE_BUILD_PARALLEL_LEVEL='1',
               CARGO_TARGET_DIR=str(build), AEXCOMPAT_BUILD_REVISION='F50-budget')
    cmd = ['cargo', 'build', '--manifest-path', str(source/'Cargo.toml'), '--release',
           '--offline', '--locked', '-j', '1', '-p', 'aex-guest-worker', '--bin', 'aex-guest-worker']
    try:
        with (S/'rebuild.log').open('w') as log:
            subprocess.run(cmd, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
        shutil.copy2(build/'release/aex-guest-worker', binary)
        manifest = dict(worker_sha256=sha(binary), parent_worker_sha256=sha(CACHE/'worker-F46-pow/aex-guest-worker'),
                        patch_sha256=sha(HERE/'F50-budget.patch'), source_manifest=tree(source),
                        memory_free_percent=free, command=cmd, instructions_per_slice=2000000000,
                        max_scheduler_slices=257, production_timeout_microseconds=0)
        durable = CACHE/'F50-budget-build.json'
        durable.write_text(json.dumps(manifest, indent=2, sort_keys=True)+'\n')
        (E/'build-manifest.json').write_text(durable.read_text())
        with (CACHE/'.index.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            index = CACHE/'INDEX.json'
            data = json.loads(index.read_text())
            assert not any(x['name'] == 'worker-F50-budget' for x in data['links'])
            data['links'].append(dict(name='worker-F50-budget', parent='worker-F46-pow',
                worker_path=str(binary), worker_sha256=sha(binary), build_json=str(durable),
                recipe='tools/emulation/aexcompat_patches/build_F50.py', matches_recorded=True))
            staged = CACHE/'INDEX.F50.json'
            staged.write_text(json.dumps(data, indent=2)+'\n')
            staged.replace(index)
        print('Built and registered', sha(binary), flush=True)
    finally:
        if build.exists():
            shutil.rmtree(build)

if __name__ == '__main__':
    main()
