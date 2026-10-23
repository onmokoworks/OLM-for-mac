#!/usr/bin/env python3
"""Replay seed-1 candidate alignment coverage; no gates or math seams enabled."""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
from types import SimpleNamespace

from adapters import radialblur
from core import sha
from run import ROOT, default_worker, main_checkout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compare', type=Path, help='Require byte/status identity to this baseline and no sanitizer reports')
    parser.add_argument('--revision', help='Read production source/header from this git revision')
    parser.add_argument('--scratch', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    scratch = args.scratch.resolve()
    if not scratch.is_relative_to(ROOT / 'orchestra/state'):
        parser.error('scratch must be under orchestra/state')
    scratch.mkdir(parents=True, exist_ok=True)
    os.environ['OLM_RADIAL_CANDIDATE_SANITIZE'] = '1'
    os.environ.pop('OLM_RADIAL_CANDIDATE_BYPASS', None)
    deadline = time.monotonic() + 1200
    report = {'revision': args.revision, 'rows': []}
    with tempfile.TemporaryDirectory(dir=scratch, prefix='alignment_') as name:
        work = Path(name)
        if args.revision:
            for suffix in ('.cpp', '.h'):
                source = f'mac/OLMRadialBlur/OLMRadialBlur{suffix}'
                (work / ('source' + suffix)).write_bytes(subprocess.check_output(
                    ['git', 'show', f'{args.revision}:{source}'], cwd=ROOT))
            radialblur.public.SOURCE = work / 'source.cpp'
        adapter = radialblur.Adapter(SimpleNamespace(
            max_size=256, case_timeout=10, main=main_checkout(), worker=default_worker()))
        report['provenance'] = adapter.prepare(work, deadline)
        for index in range(500):
            case = adapter.generate(1, index)
            with tempfile.TemporaryDirectory(dir=work, prefix='case_') as case_name:
                directory = Path(case_name)
                for route in adapter.routes:
                    trace = directory / f'{route}.trace'
                    if index in (193, 425):
                        adapter.env['OLMRADIALBLUR_DEBUG_DUMP_PATH'] = str(trace)
                        adapter.env['OLMRADIALBLUR_DEBUG_POINTS'] = '0,0;0,1'
                    else:
                        adapter.env.pop('OLMRADIALBLUR_DEBUG_DUMP_PATH', None)
                        adapter.env.pop('OLMRADIALBLUR_DEBUG_POINTS', None)
                    status, raw, guards = adapter.candidate(case, directory, route, deadline)
                    row = {'index': index, 'route': route, 'status': status['status'],
                           'sha256': sha(raw), 'guards': guards,
                           'sanitizer': status.get('sanitizer', [])}
                    # Historical admitted UBSan witnesses: compare to the original
                    # route owner, retaining first-byte evidence for existing reds.
                    if trace.exists():
                        row['intermediate_trace'] = trace.read_text()
                        row['intermediate_trace_sha256'] = sha(trace.read_bytes())
                    if index in (193, 425):
                        oracle, expected = adapter.oracle(case, directory, deadline, route)
                        row['oracle_status'] = oracle['status']
                        row['oracle_sha256'] = sha(expected)
                        if status['status'] == oracle['status'] == 'ok':
                            row['exact'] = raw == expected
                            row['first_mismatch'] = next(({'byte': i, 'candidate': a, 'aex': b}
                                for i, (a, b) in enumerate(zip(raw, expected)) if a != b), None)
                    report['rows'].append(row)
            if index % 100 == 99:
                print('completed', index + 1, flush=True)
        report['summary'] = dict(Counter(row['status'] for row in report['rows']))
        report['sanitizer_rows'] = sum(bool(row['sanitizer']) for row in report['rows'])
    if args.compare:
        before = json.loads(args.compare.read_text())
        fields = ('index', 'route', 'status', 'sha256', 'intermediate_trace_sha256')
        # Refusal traces append source line numbers; edits move those numbers.
        def guard_tags(row):
            return [guard.rsplit('@', 1)[0] for guard in row['guards']]
        report['changed_rows'] = [
            {'index': row['index'], 'route': row['route']}
            for old, row in zip(before['rows'], report['rows'])
            if any(old.get(key) != row.get(key) for key in fields)
            or guard_tags(old) != guard_tags(row)]
        report['baseline_rows'] = len(before['rows'])
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    print(report['summary'], 'sanitizer_rows', report['sanitizer_rows'])
    if args.compare:
        assert report['baseline_rows'] == len(report['rows'])
        assert not report['changed_rows'], report['changed_rows'][:10]
        assert report['sanitizer_rows'] == 0


if __name__ == '__main__':
    main()
