#!/usr/bin/env python3
"""Add passive read windows in a disposable copy; preserve reference math."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

PATCH = Path(__file__).with_name('aexcompat_radial_readonly_windows_20261001.patch')
CHANGED = ['crates/aex-guest-worker/src/main.rs', 'crates/aex-guest-worker/src/classic.rs',
           'crates/aex-guest-worker/src/x64/types.rs', 'crates/aex-guest-worker/src/x64/trace.rs',
           'crates/aex-guest-worker/src/x64/tests_cases.rs']
CALLBACK = 'crates/aex-guest-worker/src/x64/callbacks.rs'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--parent-source', type=Path, required=True)
    ap.add_argument('--parent-build', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    source, output = args.parent_source.resolve(), args.output.resolve()
    assert not output.exists()
    assert source != output and source not in output.parents and output not in source.parents
    parent = json.loads(args.parent_build.read_text())
    assert sha(source/'target/release/aex-guest-worker') == parent['worker_sha256']
    assert sha(source/CALLBACK) == parent['callback_patched_sha256']
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
    for name, expected in manifest.items():
        assert sha(source/name) == expected, name
        if name not in CHANGED: assert sha(output/name) == expected, name
    assert sha(source/'target/release/aex-guest-worker') == parent['worker_sha256']
    report = {'schema': 'radialblur.readonly-windows-reference-build/1',
              'parent_build_sha256': sha(args.parent_build), 'parent_worker_sha256': parent['worker_sha256'],
              'worker_sha256': sha(output/'target/release/aex-guest-worker'),
              'parent_source_and_worker_unchanged': True, 'parent_source_files_sha256': manifest,
              'modified_source_files': {name: {'before': manifest[name], 'after': sha(output/name)} for name in CHANGED},
              'math_callbacks_unchanged': True, 'callback_sha256': sha(output/CALLBACK),
              'patch_sha256': sha(PATCH), 'builder_sha256': sha(Path(__file__)),
              'read_window_size_limit': 4096, 'pointer_and_window_offset_limit': 16777216,
              'offset_zero_preserves_existing_watches': True,
              'guest_memory_writes_added': False,
              'claims_not_made': ['Diagnostic read windows do not change controlled math provenance.',
                                 'No production plugin, original AEX or parent worker changes.']}
    (output/'window-reference-build.json').write_text(json.dumps(report, sort_keys=True, indent=2)+'\n')
    print('READONLY_WINDOWS_BUILD', report['worker_sha256'], flush=True)


if __name__ == '__main__':
    main()
