#!/usr/bin/env python3
"""Install a tested X01b worker under a new name; never replace an oracle."""
import argparse
import fcntl
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--worker', type=Path, required=True)
    parser.add_argument('--ui-summary', type=Path, required=True)
    args = parser.parse_args()
    subprocess.run(['git', 'diff', 'HEAD', '--exit-code', '--', 'guest', 'rust-toolchain.toml'], cwd=args.source, check=True)
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=args.source, text=True).strip()
    summary = json.loads(args.ui_summary.read_text())
    digest = sha(args.worker)
    assert digest == summary['candidate_worker_sha256']
    assert len(summary['sessions']) == 17 and summary['semantic_mismatches'] == 0
    assert all(row['returncode'] == 0 and row['semantic_equal'] for row in summary['sessions'])
    cache = Path.home() / '.cache/olm-emu'
    name = 'worker-X01b-parity'
    output = cache / name
    with (cache / '.index.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        index_path = cache / 'INDEX.json'
        index = json.loads(index_path.read_text())
        assert not any(row['name'] == name for row in index['links']), 'already registered'
        output.mkdir(exist_ok=False)
        shutil.copy2(args.worker, output / 'aex-guest-worker')
        with (output / 'source.tar.gz').open('wb') as stream, gzip.GzipFile(fileobj=stream, mode='wb', mtime=0) as archive:
            proc = subprocess.Popen(['git', 'archive', revision, 'guest', 'rust-toolchain.toml', 'AGENTS.md', 'CLAUDE.md'], cwd=args.source, stdout=subprocess.PIPE)
            shutil.copyfileobj(proc.stdout, archive)
            assert proc.wait() == 0
        manifest = {'worker_sha256': digest, 'source_revision': revision,
                    'source_branch': 'olm/X01-platform-parity',
                    'source_archive_sha256': sha(output / 'source.tar.gz'),
                    'ui_replay': summary,
                    'build_command': 'TMPDIR=$HOME/.cache/olm-emu/build-X01b/tmp CARGO_TARGET_DIR=$HOME/.cache/olm-emu/build-X01b/target CARGO_PROFILE_RELEASE_DEBUG=0 CARGO_INCREMENTAL=0 CMAKE_BUILD_PARALLEL_LEVEL=1 cargo build --release --manifest-path guest/Cargo.toml -p aex-guest-worker --locked --jobs 1'}
        (output / 'build.json').write_text(json.dumps(manifest, indent=2) + '\n')
        index['links'].append({'name': name, 'parent': 'worker-F54c', 'worker_path': str(output / 'aex-guest-worker'),
                               'worker_sha256': digest, 'build_json': str(output / 'build.json'),
                               'recipe': 'tools/emulation/aexcompat_patches/install_X01b_worker.py; build.json and source.tar.gz',
                               'matches_recorded': True})
        staged = cache / 'INDEX.X01b.json'
        with staged.open('x') as stream:
            stream.write(json.dumps(index, indent=2) + '\n')
        staged.replace(index_path)
    print(json.dumps({'name': name, 'worker_sha256': digest, 'source_revision': revision}))


if __name__ == '__main__':
    main()
