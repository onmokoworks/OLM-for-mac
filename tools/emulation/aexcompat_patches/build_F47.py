#!/usr/bin/env python3
"""Build the F47 load-only probe; never register it as a render candidate."""
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
CACHE = Path.home() / '.cache/olm-emu'
S = ROOT / 'orchestra/state/F47-aexcompat-native-plugin-host'

def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def main():
    S.mkdir(parents=True, exist_ok=True)
    source = CACHE / 'src-F47'
    parent = CACHE / 'src-F46/reference-guest'
    patch = HERE / 'F47-native-plugin.patch'
    if not source.exists():
        shutil.copytree(parent, source)
        subprocess.run(['patch', '-p1', '-i', str(patch)], cwd=source, check=True)
    # Verify the existing copy against the committed patch without altering it.
    subprocess.run(['patch', '--dry-run', '-R', '-p1', '-i', str(patch)], cwd=source, check=True)
    pressure = subprocess.check_output(['memory_pressure'], text=True)
    (S / 'memory-pressure.log').write_text(pressure)
    free = int(re.search(r'System-wide memory free percentage: (\d+)%', pressure)[1])
    if free < 30:
        raise RuntimeError(f'Build blocked: {free}% free, need 30%')
    out = CACHE / 'worker-F47-nativeplugin'
    out.mkdir(exist_ok=True)
    if (out / 'aex-guest-worker').exists():
        raise RuntimeError('Worker already exists; refusing to replace it')
    env = dict(os.environ, TMPDIR=str(S), TMP=str(S), TEMP=str(S),
               CARGO_BUILD_JOBS='1', CMAKE_BUILD_PARALLEL_LEVEL='1',
               CARGO_TARGET_DIR=str(out / 'build'), AEXCOMPAT_BUILD_REVISION='F47-load-only')
    cmd = ['cargo', 'build', '--manifest-path', str(source / 'Cargo.toml'),
           '--release', '--offline', '--locked', '-j', '1', '-p', 'aex-guest-worker',
           '--bin', 'aex-guest-worker']
    with (S / 'rust-build.log').open('w') as log:
        subprocess.run(cmd, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
    binary = out / 'aex-guest-worker'
    shutil.copy2(out / 'build/release/aex-guest-worker', binary)
    manifest = dict(worker_sha256=sha(binary), patch_sha256=sha(patch),
                    parent_worker_sha256=sha(CACHE / 'worker-F46-pow/aex-guest-worker'),
                    memory_free_percent=free, command=cmd, capability='native-plugin-load-only',
                    source_manifest={str(p.relative_to(source)): sha(p)
                                     for p in sorted(source.rglob('*')) if p.is_file()})
    record = CACHE / 'F47-nativeplugin-build.json'
    record.write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
    shutil.copy2(record, S / 'worker-build.json')
    shutil.rmtree(out / 'build')
    with (CACHE / '.index.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        path = CACHE / 'INDEX.json'
        data = json.loads(path.read_text())
        if any(x['name'] == out.name for x in data['links']):
            raise RuntimeError('INDEX entry already exists')
        data['links'].append(dict(name=out.name, parent='worker-F46-pow',
            worker_path=str(binary), worker_sha256=sha(binary), build_json=str(record),
            capability='native-plugin-load-only', matches_recorded=True,
            recipe='tools/emulation/aexcompat_patches/build_F47.py; load probe, no Mac render'))
        staged = CACHE / 'INDEX.F47.json'
        staged.write_text(json.dumps(data, indent=2) + '\n')
        staged.replace(path)
    print(sha(binary))

if __name__ == '__main__':
    main()
