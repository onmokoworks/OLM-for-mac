#!/usr/bin/env python3
"""Correct a witnessed axis in a disposable controlled reference, not the port.

The parent source/worker and frozen AEX remain immutable. All other atan2f
inputs still use host FLOAT32 math; this is not a general Windows UCRT port.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

PATCH = Path(__file__).with_name('aexcompat_radial_atan2_axis_20261001.patch')
CALLBACK = 'crates/aex-guest-worker/src/x64/callbacks.rs'
MAIN = 'crates/aex-guest-worker/src/main.rs'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--typed-source', type=Path, required=True)
    parser.add_argument('--parent-build', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source, output = args.typed_source.resolve(), args.output.resolve()
    assert not output.exists()
    assert source != output and source not in output.parents and output not in source.parents
    parent = json.loads(args.parent_build.read_text())
    assert sha(source/'target/release/aex-guest-worker') == parent['worker_sha256']
    assert sha(source/MAIN) == parent['main_patched_sha256']
    manifest = {str(p.relative_to(source)): sha(p) for p in source.rglob('*')
                if p.is_file() and p.relative_to(source).parts[0] != 'target'
                and not set(p.relative_to(source).parts) & {'.git', '__pycache__'}}
    for name, digest in parent['parent_source_files_sha256'].items():
        assert manifest[name] == (parent['main_patched_sha256'] if name == MAIN else digest), name
    def ignore(directory, names):
        return [n for n in names if n in ('.git', '__pycache__')
                or (Path(directory) == source and n == 'target')]
    shutil.copytree(source, output, ignore=ignore)
    subprocess.run(['cp', '-cR', str(source/'target'), str(output/'target')], check=True)
    subprocess.run(['git', 'apply', '--check', str(PATCH)], cwd=output, check=True)
    subprocess.run(['git', 'apply', str(PATCH)], cwd=output, check=True)
    subprocess.run(['cargo', 'build', '--release', '--offline', '--locked', '-p', 'aex-guest-worker'],
                   cwd=output, check=True)
    for name, digest in manifest.items():
        assert sha(source/name) == digest, name
        if name != CALLBACK:
            assert sha(output/name) == digest, name
    assert sha(source/'target/release/aex-guest-worker') == parent['worker_sha256']
    report = {'schema': 'radialblur.axis-reference-build/1',
              'parent_build_sha256': sha(args.parent_build),
              'parent_worker_sha256': parent['worker_sha256'],
              'worker_sha256': sha(output/'target/release/aex-guest-worker'),
              'parent_source_and_worker_unchanged': True,
              'callback_base_sha256': manifest[CALLBACK],
              'callback_patched_sha256': sha(output/CALLBACK),
              'patch_sha256': sha(PATCH), 'builder_sha256': sha(Path(__file__)),
              'parent_source_files_sha256': manifest,
              'cargo_command': 'cargo build --release --offline --locked -p aex-guest-worker',
              'corrected_domain': 'y bits 00000000 and finite x < 0: nearest FLOAT32 pi',
              'claims_not_made': ['Other atan2f inputs retain unverified host math',
                                 'No general native Windows UCRT equivalence',
                                 'No production plugin, original worker, or AEX modified']}
    (output/'axis-reference-build.json').write_text(json.dumps(report, sort_keys=True, indent=2)+'\n')
    print('AXIS_REFERENCE_BUILD', report['worker_sha256'], flush=True)


if __name__ == '__main__':
    main()
