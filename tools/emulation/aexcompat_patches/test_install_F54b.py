#!/usr/bin/env python3
"""Filesystem regression for immutable installation; no real cache/git changes."""
import argparse
import contextlib
import io
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
import install_F54b as installer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--scratch', type=Path, required=True)
    args = parser.parse_args()
    args.scratch.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=args.scratch, prefix='install-test-') as name:
        root = Path(name)
        cache = root / '.cache/olm-emu'
        cache.mkdir(parents=True)
        index = cache / 'INDEX.json'
        index.write_text(json.dumps({'links': []}))
        source = root / 'source'
        source.mkdir()
        (source / 'file').write_bytes(b'source')
        binary = root / 'binary'
        binary.write_bytes(b'worker')
        head = ['head-1']

        def git(command, **kwargs):
            argv = command[3:]
            if argv == ['status', '--porcelain']:
                return ''
            if argv == ['branch', '--show-current']:
                return 'branch'
            if argv == ['rev-parse', 'HEAD']:
                return head[0]
            if argv == ['diff', '--name-only', '5a9bd8f7', 'HEAD']:
                return 'file'
            raise AssertionError(argv)

        def archive(command, stdout, **kwargs):
            assert command[3:] == ['archive', head[0]]
            stdout.write(b'source archive ' + head[0].encode())

        def snapshot():
            return {str(p.relative_to(cache)): (p.read_bytes(), p.stat().st_mtime_ns)
                    for p in cache.rglob('*') if p.is_file() and p.name != '.index.lock'}

        with patch.object(installer.Path, 'home', return_value=root), \
                patch.object(installer.subprocess, 'check_output', side_effect=git), \
                patch.object(installer.subprocess, 'run', side_effect=archive), \
                patch.object(sys, 'argv', ['install', '--source', str(source), '--binary', str(binary)]), \
                contextlib.redirect_stdout(io.StringIO()):
            installer.main()
            retained = snapshot()
            installer.main()
            assert snapshot() == retained, 'identical rerun modified files'
            head[0] = 'head-2'
            try:
                installer.main()
            except SystemExit:
                pass
            else:
                raise AssertionError('changed provenance accepted')
            assert snapshot() == retained, 'rejected provenance changed files'
            head[0] = 'head-1'
            data = json.loads(index.read_text())
            data['links'][0]['worker_sha256'] = 'conflict'
            index.write_text(json.dumps(data))
            conflict = snapshot()
            try:
                installer.main()
            except SystemExit:
                pass
            else:
                raise AssertionError('conflicting INDEX accepted')
            assert snapshot() == conflict, 'rejected INDEX changed files'
        print('PASS: fresh install, immutable rerun, changed-HEAD rejection, INDEX-conflict rejection')


if __name__ == '__main__':
    main()
