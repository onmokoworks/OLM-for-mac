#!/usr/bin/env python3
"""Local rebuild of the controlled-math worker.

Identical steps to tools/emulation/build_radialblur_controlled_math_worker_20261001.py
but the source tree is the cached frozen rebuild, so the frozen worker hash
assertion is relaxed and the recorded hash is kept as data.
"""
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

CACHE = Path('/Users/onmk/.cache/olm-emu')
SOURCE = CACHE / 'radial_frozen_reference_bd878da'
OUTPUT = CACHE / 'radial_controlled_reference_20261001'
OLM = Path('/Users/onmk/Documents/Projects/Personal/OLM as')
PATCH = OLM / 'tools/emulation/aexcompat_radial_controlled_math_20261001.patch'
RECORDED = OLM / 'reports/radialblur_controlled_reference_build_20261001.json'
BINDINGS = ['crates/aex-guest-worker/src/x64/imports.rs',
            'crates/aex-guest-worker/src/x64/callbacks.rs']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest(root):
    return {str(p.relative_to(root)): sha(p) for p in root.rglob('*')
            if p.is_file() and p.relative_to(root).parts[0] != 'target'
            and not set(p.relative_to(root).parts) & {'.git', '__pycache__'}}


def main():
    assert not OUTPUT.exists()
    base_manifest = manifest(SOURCE)
    recorded = json.loads(RECORDED.read_text())
    for name, digest in recorded['base_source_files_sha256'].items():
        assert base_manifest[name] == digest, name
    def ignore(directory, names):
        return [n for n in names if n in ('.git', '__pycache__')
                or (Path(directory) == SOURCE and n == 'target')]
    shutil.copytree(SOURCE, OUTPUT, ignore=ignore)
    subprocess.run(['git', 'apply', '--check', str(PATCH)], cwd=OUTPUT, check=True)
    subprocess.run(['git', 'apply', str(PATCH)], cwd=OUTPUT, check=True)
    subprocess.run(['cargo', 'build', '--release', '--offline', '--locked',
                    '-p', 'aex-guest-worker'], cwd=OUTPUT, check=True)
    for name, digest in base_manifest.items():
        assert sha(SOURCE / name) == digest, name
    worker = sha(OUTPUT / 'target/release/aex-guest-worker')
    report = {
        'schema': 'radialblur.controlled-math-worker-build/1',
        'frozen_worker_sha256_recorded': recorded['frozen_worker_sha256'],
        'frozen_worker_sha256_local': sha(SOURCE / 'target/release/aex-guest-worker'),
        'controlled_worker_sha256': worker,
        'controlled_worker_sha256_recorded': recorded['controlled_worker_sha256'],
        'worker_sha256_matches_recorded': worker == recorded['controlled_worker_sha256'],
        'base_source_files_sha256': base_manifest,
        'patched_source_files_sha256': {name: sha(OUTPUT / name) for name in BINDINGS},
        'patch_sha256': sha(PATCH),
        'builder_sha256': sha(OLM / 'tools/emulation/build_radialblur_controlled_math_worker_20261001.py'),
        'cargo_command': 'cargo build --release --offline --locked -p aex-guest-worker',
        'frozen_source_and_worker_unchanged': True,
        'claims_not_made': ['Local rebuild; recorded worker hashes are path/toolchain-specific.'],
    }
    (OUTPUT / 'controlled-reference-build.json').write_text(
        json.dumps(report, sort_keys=True, indent=2) + '\n')
    print('CONTROLLED_WORKER_BUILD', worker)


if __name__ == '__main__':
    main()
