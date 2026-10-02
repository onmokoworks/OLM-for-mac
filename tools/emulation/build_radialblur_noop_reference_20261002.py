#!/usr/bin/env python3
"""Widen only disposable fixture dimensions and data arena for copy witnesses.

Preserve nested qemu/target sources and the parent source/worker. Original AEX,
ABI, math callbacks and copy callbacks are unchanged. This is a local host
measurement envelope, not proof of native Windows AE hosting.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

CHANGED = ['crates/aex-guest-worker/src/classic.rs', 'crates/aex-guest-worker/src/x64.rs']
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
    assert not output.exists() and source != output
    assert source not in output.parents and output not in source.parents
    parent = json.loads(args.parent_build.read_text())
    worker_sha = sha(source/'target/release/aex-guest-worker')
    assert worker_sha == parent['worker_sha256']
    manifest = {}
    for directory, dirs, files in os.walk(source):
        # Only the top-level target is build output; qemu/target is source.
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
    replacements = {
        CHANGED[0]: [('pub const MAX_RENDER_WIDTH: u32 = 1920;', 'pub const MAX_RENDER_WIDTH: u32 = 8192;'),
                     ('pub const MAX_RENDER_HEIGHT: u32 = 1080;', 'pub const MAX_RENDER_HEIGHT: u32 = 4096;')],
        CHANGED[1]: [('const DATA_SIZE: u64 = 0x1000_0000;', 'const DATA_SIZE: u64 = 0x2000_0000;'),
                     ('const HANDLE_DATA_BASE: u64 = DATA_BASE + 0x400_0000;', 'const HANDLE_DATA_BASE: u64 = DATA_BASE + 0x1200_0000;')],
    }
    for rel, pairs in replacements.items():
        path = output/rel; text = path.read_text()
        for old, new in pairs:
            assert text.count(old) == 1, (rel, old)
            text = text.replace(old, new)
        path.write_text(text)
    text = (output/CHANGED[1]).read_text()
    assert 'const DATA_BASE: u64 = 0x0000_0000_4000_0000;' in text
    assert 'const STUB_BASE: u64 = 0x0000_0000_6000_0000;' in text
    assert 0x40000000 + 0x20000000 == 0x60000000
    subprocess.run(['cargo', 'build', '--release', '--offline', '--locked', '-p', 'aex-guest-worker'], cwd=output, check=True)
    for rel, expected in manifest.items():
        assert sha(source/rel) == expected, rel
        if rel not in CHANGED: assert sha(output/rel) == expected, rel
    assert sha(source/'target/release/aex-guest-worker') == worker_sha
    result = dict(schema='radialblur.noop-reference-build/1',
        parent_worker_sha256=worker_sha, worker_sha256=sha(output/'target/release/aex-guest-worker'),
        parent_build_sha256=sha(args.parent_build), parent_source_and_worker_unchanged=True,
        original_aex_changed=False, source_files_sha256=manifest,
        changed={rel: dict(before=manifest[rel], after=sha(output/rel)) for rel in CHANGED},
        builder_sha256=sha(Path(__file__)), callback_sha256=sha(output/CALLBACK),
        copy_and_math_callbacks_unchanged=True, fixture_dimensions=[8192,4096],
        data_arena_bytes=288*1024*1024, data_mapping_bytes=512*1024*1024,
        handle_arena_bytes=224*1024*1024, data_mapping_ends_at_stub_base_without_overlap=True,
        claims_not_made=['No new native Windows execution or AE/ROI/downsample/Type3 restoration.'])
    (output/'noop-reference-build.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print('NOOP_REFERENCE_BUILD', result['worker_sha256'], flush=True)


if __name__ == '__main__': main()
