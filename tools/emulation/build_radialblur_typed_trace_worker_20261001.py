#!/usr/bin/env python3
"""Add typed Angle trace CLI to a disposable, hash-bound controlled reference.

The source copy and parent worker are kept immutable. This changes CLI input
representation only; all original typed materialization and AEX instructions
remain in the same path. Targets MPL-2.0 AEXCompat sources.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

PATCH = Path(__file__).with_name('aexcompat_radial_typed_angle_trace_20261001.patch')
MAIN = 'crates/aex-guest-worker/src/main.rs'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--controlled-source', type=Path, required=True)
    parser.add_argument('--base-build', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source, output = args.controlled_source.resolve(), args.output.resolve()
    assert not output.exists()
    assert source != output and source not in output.parents and output not in source.parents
    base = json.loads(args.base_build.read_text())
    assert sha(source/'target/release/aex-guest-worker') == base['controlled_worker_sha256']
    assert sha(source/MAIN) == base['base_source_files_sha256'][MAIN]
    for name, digest in base['patched_source_files_sha256'].items():
        assert sha(source/name) == digest
    manifest = {str(p.relative_to(source)): sha(p) for p in source.rglob('*')
                if p.is_file() and p.relative_to(source).parts[0] != 'target'
                and not set(p.relative_to(source).parts) & {'.git', '__pycache__'}}
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
    assert sha(source/'target/release/aex-guest-worker') == base['controlled_worker_sha256']
    report = {'schema': 'radialblur.typed-trace-worker-build/1',
              'base_build_sha256': sha(args.base_build),
              'parent_worker_sha256': base['controlled_worker_sha256'],
              'worker_sha256': sha(output/'target/release/aex-guest-worker'),
              'parent_source_and_worker_unchanged': True,
              'main_base_sha256': manifest[MAIN], 'main_patched_sha256': sha(output/MAIN),
              'patch_sha256': sha(PATCH), 'builder_sha256': sha(Path(__file__)),
              'parent_source_files_sha256': manifest,
              'cargo_command': 'cargo build --release --offline --locked -p aex-guest-worker',
              'claims_not_made': ['No native Windows UCRT equivalence',
                                 'No original frozen worker rebuilt or modified',
                                 'No production plugin or AEX instructions modified']}
    (output/'typed-trace-build.json').write_text(json.dumps(report, sort_keys=True, indent=2)+'\n')
    print('TYPED_TRACE_WORKER_BUILD', report['worker_sha256'], flush=True)


if __name__ == '__main__':
    main()
