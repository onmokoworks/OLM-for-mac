#!/usr/bin/env python3
"""Extend only the disposable host deadline for legal Offset measurements.

The original AEX, parent source/worker, ABI, dimensions, arena and callbacks
remain unchanged. Calibrate the resulting binary with original output hashes;
a longer deadline does not establish native Windows/AE equivalence.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

CHANGED = 'crates/aex-guest-worker/src/x64.rs'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--parent-source', type=Path, required=True)
    ap.add_argument('--parent-build', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    source, output = args.parent_source.resolve(), args.output.resolve()
    assert not output.exists() and source != output
    assert source not in output.parents and output not in source.parents
    parent = json.loads(args.parent_build.read_text())
    worker_sha = sha(source/'target/release/aex-guest-worker')
    assert worker_sha == parent['worker_sha256']
    manifest = {}
    for directory, dirs, files in os.walk(source):
        # Nested qemu/target is source; only root target is build output.
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__']
                   and not (Path(directory) == source and d == 'target')]
        for name in files:
            path = Path(directory)/name
            manifest[str(path.relative_to(source))] = sha(path)
    def ignore(directory, names):
        return [n for n in names if n in ['.git', '__pycache__']
                or (Path(directory) == source and n == 'target')]
    shutil.copytree(source, output, ignore=ignore)
    subprocess.run(['cp', '-cR', str(source/'target'), str(output/'target')], check=True)
    path = output/CHANGED
    text = path.read_text()
    before = 'const TIMEOUT_MICROSECONDS: u64 = 20_000_000;'
    after = 'const TIMEOUT_MICROSECONDS: u64 = 120_000_000;'
    assert text.count(before) == 1
    path.write_text(text.replace(before, after))
    subprocess.run(['cargo', 'build', '--release', '--offline', '--locked', '-p', 'aex-guest-worker'],
                   cwd=output, check=True)
    for rel, expected in manifest.items():
        assert sha(source/rel) == expected, rel
        if rel != CHANGED: assert sha(output/rel) == expected, rel
    assert sha(source/'target/release/aex-guest-worker') == worker_sha
    result = dict(schema='radialblur.offset-timeout-reference-build/1',
        parent_worker_sha256=worker_sha, worker_sha256=sha(output/'target/release/aex-guest-worker'),
        parent_build_sha256=sha(args.parent_build), parent_source_and_worker_unchanged=True,
        original_aex_changed=False, source_files_sha256=manifest,
        changed={CHANGED: dict(before=manifest[CHANGED], after=sha(path))},
        builder_sha256=sha(Path(__file__)), timeout_microseconds_before=20_000_000,
        timeout_microseconds_after=120_000_000,
        dimensions_memory_abi_math_and_copy_callbacks_unchanged=True,
        claims_not_made=['No native Windows/AE behavior or general reference-worker equivalence.',
                        'Earlier failed batches lack retained stderr; their cause remains unclassified.'])
    (output/'offset-timeout-reference-build.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print('OFFSET_TIMEOUT_REFERENCE_BUILD', result['worker_sha256'], flush=True)


if __name__ == '__main__': main()
