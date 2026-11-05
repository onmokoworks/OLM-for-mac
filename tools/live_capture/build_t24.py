#!/usr/bin/env python3
"""Reproduce the isolated T24 worker from the retained, hash-bound F53 source."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
CACHE = Path.home()/'.cache/olm-emu'
STATE = ROOT/'orchestra/state/T24-aexcompat-worker-32bpc-arena'
SOURCE = CACHE/'src-T24/reference-guest'
OUT = CACHE/'worker-T24-arena'
PATCH = HERE/'T24-arena.patch'
TRANSPORT = HERE/'T24-S02-transport.patch'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def tree(path):
    return {str(p.relative_to(path)): sha(p) for p in sorted(path.rglob('*')) if p.is_file()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--register', action='store_true')
    parser.add_argument('--verify', action='store_true')
    parser.add_argument('--replace-existing', action='store_true', help='Replace this ticket\'s initial INDEX entry')
    args = parser.parse_args()
    STATE.mkdir(parents=True, exist_ok=True)
    binary = OUT/'aex-guest-worker'
    if args.register or args.verify:
        manifest = json.loads((OUT/'build.json').read_text())
        assert sha(binary) == manifest['worker_sha256']
        assert sha(PATCH) == manifest['patch_sha256']
        assert sha(TRANSPORT) == manifest['transport_patch_sha256']
        assert tree(SOURCE) == manifest['source_manifest']
        if args.register:
            # Reuse the cache's existing lock without creating files elsewhere.
            with (CACHE/'.index.lock').open('rb') as lock:
                fcntl.flock(lock, fcntl.LOCK_EX)
                index = CACHE/'INDEX.json'
                data = json.loads(index.read_text())
                entry = dict(name=OUT.name, parent='worker-F53-geom',
                             worker_path=str(binary), worker_sha256=sha(binary),
                             build_json=str(OUT/'build.json'),
                             recipe='python3 tools/live_capture/build_t24.py',
                             matches_recorded=False)
                existing = next((x for x in data['links'] if x['name'] == OUT.name), None)
                if existing is None:
                    data['links'].append(entry)
                else:
                    if existing['worker_sha256'] != entry['worker_sha256']:
                        assert args.replace_existing, 'Use --replace-existing for a revised T24 build'
                        (OUT/'previous-index-entry.json').write_text(json.dumps(existing, indent=2)+'\n')
                        existing.clear()
                        existing.update(entry)
                staged = OUT/'INDEX.staged.json'
                staged.write_text(json.dumps(data, indent=2)+'\n')
                staged.replace(index)
        print('PASS source/patch/build binding', sha(binary))
        return
    parent = CACHE/'src-F53/reference-guest'
    expected = json.loads((CACHE/'worker-F53-geom/build.json').read_text())
    assert tree(parent) == expected['source_manifest'], 'F53 source drift'
    clean = CACHE/'src-T24/expected'
    assert not clean.exists()
    clean.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copytree(parent, clean)
        subprocess.run(['patch', '-p1', '-i', str(PATCH)], cwd=clean, check=True)
        subprocess.run(['patch', '-p1', '-i', str(TRANSPORT)], cwd=clean, check=True)
        # Preserve the already validated independent AE float-colour transport.
        callback = 'crates/aex-guest-worker/src/x64/iterate_and_suites.rs'
        s02 = json.loads((CACHE/'worker-S02-F53/build.json').read_text())
        assert sha(clean/callback) == s02['callback_sha256']
        if SOURCE.exists():
            assert tree(SOURCE) == tree(clean), 'T24 source differs from patch'
        else:
            shutil.copytree(clean, SOURCE)
    finally:
        if clean.exists():
            shutil.rmtree(clean)
    pressure = subprocess.check_output(['memory_pressure'], text=True)
    (STATE/'memory-pressure-build.txt').write_text(pressure)
    free = int(re.search(r'System-wide memory free percentage: (\d+)%', pressure)[1])
    assert free >= 30, f'Build blocked: {free}% free'
    target = CACHE/'src-T24/target'
    temporary = CACHE/'src-T24/tmp'
    temporary.mkdir(exist_ok=True)
    env = dict(os.environ, TMPDIR=str(temporary), TMP=str(temporary), TEMP=str(temporary),
               CARGO_TARGET_DIR=str(target), CARGO_BUILD_JOBS='1',
               CMAKE_BUILD_PARALLEL_LEVEL='1', AEXCOMPAT_BUILD_REVISION='T24-arena')
    command = ['cargo', 'build', '--release', '--offline', '--locked', '-j', '1',
               '-p', 'aex-guest-worker', '--bin', 'aex-guest-worker']
    test = ['cargo', 'test', '--release', '--offline', '--locked', '-j', '1',
            '-p', 'aex-guest-worker', 't24_data_arena', '--', '--test-threads=1']
    with (STATE/'build.log').open('w') as log:
        subprocess.run(command, cwd=SOURCE, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
    with (STATE/'worker-tests.log').open('w') as log:
        subprocess.run(test, cwd=SOURCE, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
    OUT.mkdir(exist_ok=True)
    shutil.copy2(target/'release/aex-guest-worker', binary)
    manifest = dict(worker_sha256=sha(binary), parent_worker_sha256=sha(CACHE/'worker-F53-geom/aex-guest-worker'),
                    patch_sha256=sha(PATCH), source_manifest=tree(SOURCE),
                    transport_patch_sha256=sha(TRANSPORT), capability='S02-float-colors-v1',
                    transport_callback_sha256=s02['callback_sha256'],
                    memory_free_percent=free, command=command, tests=test, cwd=str(SOURCE),
                    environment={k: env[k] for k in ('TMPDIR', 'CARGO_TARGET_DIR', 'CARGO_BUILD_JOBS',
                                                    'CMAKE_BUILD_PARALLEL_LEVEL', 'AEXCOMPAT_BUILD_REVISION')})
    (OUT/'build.json').write_text(json.dumps(manifest, indent=2, sort_keys=True)+'\n')
    shutil.rmtree(target)
    print('Built and tested', sha(binary))


if __name__ == '__main__':
    main()
