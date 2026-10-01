#!/usr/bin/env python3
"""Build a calibrated, explicitly controlled reference in a disposable copy.

DOUBLE atan2 -> FLOAT32 matches the retained Windows scalar census. This is
not an implementation or proof of the Windows UCRT for arbitrary arguments.
The enlarged trace limit is diagnostic only; original AEX/parent stay frozen.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

PATCH = Path(__file__).with_name('aexcompat_radial_doublecast_reference_20261001.patch')
CALLBACK = 'crates/aex-guest-worker/src/x64/callbacks.rs'
TRACE = 'crates/aex-guest-worker/src/x64.rs'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--axis-source', type=Path, required=True)
    ap.add_argument('--parent-build', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    source, output = args.axis_source.resolve(), args.output.resolve()
    assert not output.exists()
    assert source != output and source not in output.parents and output not in source.parents
    parent = json.loads(args.parent_build.read_text())
    assert sha(source/'target/release/aex-guest-worker') == parent['worker_sha256']
    assert sha(source/CALLBACK) == parent['callback_patched_sha256']
    manifest = {str(p.relative_to(source)): sha(p) for p in source.rglob('*')
                if p.is_file() and p.relative_to(source).parts[0] != 'target'
                and not set(p.relative_to(source).parts) & {'.git', '__pycache__'}}
    for name, expected in parent['parent_source_files_sha256'].items():
        assert manifest[name] == (parent['callback_patched_sha256'] if name == CALLBACK else expected), name
    def ignore(directory, names):
        return [n for n in names if n in ('.git', '__pycache__')
                or (Path(directory) == source and n == 'target')]
    shutil.copytree(source, output, ignore=ignore)
    subprocess.run(['cp', '-cR', str(source/'target'), str(output/'target')], check=True)
    subprocess.run(['git', 'apply', '--check', str(PATCH)], cwd=output, check=True)
    subprocess.run(['git', 'apply', str(PATCH)], cwd=output, check=True)
    subprocess.run(['cargo', 'build', '--release', '--offline', '--locked', '-p', 'aex-guest-worker'],
                   cwd=output, check=True)
    for name, expected in manifest.items():
        assert sha(source/name) == expected, name
        if name not in (CALLBACK, TRACE): assert sha(output/name) == expected, name
    assert sha(source/'target/release/aex-guest-worker') == parent['worker_sha256']
    report = {'schema': 'radialblur.doublecast-reference-build/1',
              'parent_build_sha256': sha(args.parent_build), 'parent_worker_sha256': parent['worker_sha256'],
              'worker_sha256': sha(output/'target/release/aex-guest-worker'),
              'parent_source_and_worker_unchanged': True,
              'callback_base_sha256': manifest[CALLBACK], 'callback_patched_sha256': sha(output/CALLBACK),
              'trace_base_sha256': manifest[TRACE], 'trace_patched_sha256': sha(output/TRACE),
              'patch_sha256': sha(PATCH), 'builder_sha256': sha(Path(__file__)),
              'parent_source_files_sha256': manifest, 'trace_witness_limit': 1024,
              'reference_math': 'host DOUBLE atan2 of exact FLOAT32 arguments, rounded to FLOAT32',
              'cargo_command': 'cargo build --release --offline --locked -p aex-guest-worker',
              'claims_not_made': ['Finite retained Windows vectors do not prove arbitrary UCRT arguments',
                                 'No production plugin, frozen worker, parent, or AEX modified']}
    (output/'doublecast-reference-build.json').write_text(json.dumps(report, sort_keys=True, indent=2)+'\n')
    print('DOUBLECAST_REFERENCE_BUILD', report['worker_sha256'], flush=True)


if __name__ == '__main__':
    main()
