#!/usr/bin/env python3
"""Rebuild the isolated F32 worker from the pinned F30 source (one build job)."""
import argparse, fcntl, hashlib, json, os, re, shutil, subprocess
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CACHE = Path.home()/'.cache/olm-emu'
SCRATCH = ROOT/'orchestra/state/F32-smoother-oracle-deep-pixels'
def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--register', action='store_true', help='Register the verified build in INDEX')
    args = parser.parse_args()
    SCRATCH.mkdir(parents=True, exist_ok=True)
    source = CACHE/'src-F32/reference-guest'
    parent = CACHE/'src-F30/reference-guest'
    out = CACHE/'worker-F32-deep'
    if args.register:
        manifest = json.loads((SCRATCH/'build-manifest.json').read_text())
        binary = out/'aex-guest-worker'
        assert sha(binary) == manifest['worker_sha256']
        results = json.loads((SCRATCH/'corpus-differential.json').read_text())
        assert results['total'] == 679 and results['changed'] == 0
        campaign = json.loads((SCRATCH/'fixed-seed1.json').read_text())
        assert campaign['completed'] == 300
        assert campaign['summary']['classic_exact'] == 205
        assert campaign['summary']['classic_refusal'] == 95
        with (CACHE/'.index.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            path = CACHE/'INDEX.json'
            data = json.loads(path.read_text())
            assert not any(x['name']=='worker-F32-deep' for x in data['links'])
            durable = CACHE/'F32-deep-build.json'
            assert not durable.exists()
            durable.write_text(json.dumps(manifest, indent=2)+'\n')
            data['links'].append(dict(name='worker-F32-deep', parent='worker-F30-ucrtmath', worker_path=str(binary), worker_sha256=sha(binary), build_json=str(durable), recipe='tools/emulation/aexcompat_patches/build_F32.py; F30 plus legacy DEEP_PIXELS allocator', matches_recorded=True))
            staged = CACHE/'INDEX.F32.json'
            staged.write_text(json.dumps(data, indent=2)+'\n')
            staged.replace(path)
        print('Registered', sha(binary))
        return
    assert not out.exists(), 'Existing workers must not be overwritten'
    expected_parent = json.loads((HERE/'F30-evidence/build-manifest.json').read_text())['source_manifest']
    assert {str(p.relative_to(parent)):sha(p) for p in parent.rglob('*') if p.is_file()} == expected_parent, 'F30 source changed' 
    if not source.exists():
        shutil.copytree(parent, source)
        subprocess.run(['patch', '-p1', '-i', str(HERE/'F32-deep-pixels.patch')], cwd=source, check=True)
    expected = json.loads((HERE/'F32-evidence/build-manifest.json').read_text())['source_manifest']
    assert {str(p.relative_to(source)):sha(p) for p in source.rglob('*') if p.is_file()} == expected, 'F32 source differs from reviewed patch'
    pressure = subprocess.check_output(['memory_pressure'], text=True)
    (SCRATCH/'memory-pressure.txt').write_text(pressure)
    free = int(re.search(r'System-wide memory free percentage: (\d+)%', pressure)[1])
    assert free >= 30, f'Build blocked at {free}% free'
    out.mkdir()
    env = dict(os.environ, TMPDIR=str(SCRATCH), TMP=str(SCRATCH), TEMP=str(SCRATCH), CARGO_BUILD_JOBS='1', CMAKE_BUILD_PARALLEL_LEVEL='1', CARGO_TARGET_DIR=str(out/'build'), AEXCOMPAT_BUILD_REVISION='F32-deep')
    cmd = ['cargo', 'build', '--manifest-path', str(source/'Cargo.toml'), '--release', '--offline', '--locked', '-j', '1', '-p', 'aex-guest-worker', '--bin', 'aex-guest-worker']
    with (SCRATCH/'build.log').open('w') as log:
        subprocess.run(cmd, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
    binary = out/'aex-guest-worker'
    shutil.copy2(out/'build/release/aex-guest-worker', binary)
    manifest = dict(worker_sha256=sha(binary), parent_worker_sha256=sha(CACHE/'worker-F30-ucrtmath/aex-guest-worker'), patch_sha256=sha(HERE/'F32-deep-pixels.patch'), memory_free_percent=free, command=cmd, source_manifest={str(p.relative_to(source)):sha(p) for p in sorted(source.rglob('*')) if p.is_file()})
    (SCRATCH/'build-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print('Built', sha(binary), flush=True)
if __name__ == '__main__':
    main()
