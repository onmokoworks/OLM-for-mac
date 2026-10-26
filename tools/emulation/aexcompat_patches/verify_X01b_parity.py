#!/usr/bin/env python3
"""Replay the frozen U03 UI inputs against a new worker without rebinding evidence.

The recorded worker hash remains unchanged. Report the candidate hash separately;
use U03's explicit active-arbitrary-payload comparator and retain raw differences.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--main', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    source = ROOT / 'tests/ui_oracle'
    verify = module('x01_ui_verify', source / 'verify.py')
    capture = module('x01_ui_capture', source / 'capture.py')
    plugins = {name: plugin for name, plugin, _ in capture.sessions()}
    manifest = json.loads((source / 'manifest.json').read_text())
    summary = {'candidate_worker_sha256': sha(args.worker),
               'recorded_worker_sha256': manifest['worker_sha256'],
               'sessions': [], 'semantic_mismatches': 0, 'raw_different_sessions': []}
    for entry in manifest['sessions']:
        name = entry['name']
        request = source / 'witnesses' / (name + '.request.json')
        expected_path = source / 'witnesses' / (name + '.jsonl.gz')
        assert sha(request) == entry['request_sha256'], name
        assert sha(expected_path) == entry['compressed_sha256'], name
        output = args.output / (name + '.jsonl')
        with output.open('w') as out, (args.output / (name + '.log')).open('w') as err:
            process = subprocess.run([str(args.worker.resolve()), 'ui-session',
                                      str(args.main / 'plugins_2025' / (plugins[name] + '.aex')),
                                      str(request.resolve())], stdout=out, stderr=err,
                                     env={**os.environ, 'TMPDIR': str(args.output.resolve())},
                                     timeout=180)
        row = {'name': name, 'returncode': process.returncode}
        if process.returncode == 0:
            expected, actual = verify.rows(expected_path), verify.rows(output)
            verify.invariants(name, actual)
            row['events'] = len(actual)
            row['semantic_equal'] = verify.semantic(expected) == verify.semantic(actual)
            if expected != actual:
                summary['raw_different_sessions'].append(name)
        else:
            row['semantic_equal'] = False
        summary['semantic_mismatches'] += int(not row['semantic_equal'])
        summary['sessions'].append(row)
        (args.output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
        print(json.dumps(row), flush=True)
        if not row['semantic_equal']:
            return 1
    print(json.dumps({'sessions': len(summary['sessions']),
                      'events': sum(row['events'] for row in summary['sessions']),
                      'semantic_mismatches': summary['semantic_mismatches'],
                      'raw_different_sessions': summary['raw_different_sessions']}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
