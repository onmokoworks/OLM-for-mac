#!/usr/bin/env python3
"""Bounded Round-5 dispatch regression: same AEX, base, promotion and repair.

No corpus or expected output is rewritten. Uses the existing public compiler
helper and OLM_REFUSAL_TRACE via Adapter.candidate; all builds are disposable.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

from adapters.radialblur import Adapter, ROOT, public
from core import load_corpus, sha
import probe_radialblur_offset_promote_20261002 as promote


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', type=Path, required=True)
    parser.add_argument('--scratch', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--main', type=Path, default=promote.MAIN_ROOT)
    parser.add_argument('--base', default='95b185eb')
    parser.add_argument('--before', default='ee80fabc')
    parser.add_argument('--case-timeout', type=float, default=20)
    parser.add_argument('--max-size', type=int, default=256)
    args = parser.parse_args()
    args.scratch = args.scratch.resolve()
    assert args.scratch.is_relative_to(ROOT/'orchestra/state/T01-radial-offset-promote')
    assert not os.environ.get('OLM_RADIAL_CANDIDATE_BYPASS')
    assert not os.environ.get('OLM_RADIAL_CANDIDATE_SANITIZE')
    args.scratch.mkdir(parents=True, exist_ok=False)
    os.environ['TMPDIR'] = str(args.scratch)
    source_path = public.SOURCE
    report = {'schema': 'radialblur.offset-round5/1', 'rows': [], 'provenance': {}}
    try:
        promote.resolve_aex()
        report['calibration'] = promote.worker_calibration(args.worker, args.scratch/'calibration')
        adapters = {}
        deadline = time.monotonic() + 1200
        for label, revision in [('base', args.base), ('before', args.before), ('after', None)]:
            directory = args.scratch/label
            directory.mkdir()
            source = source_path.read_bytes() if revision is None else subprocess.check_output(
                ['git', 'show', revision+':mac/OLMRadialBlur/OLMRadialBlur.cpp'], cwd=ROOT)
            path = directory/'OLMRadialBlur.cpp'
            path.write_bytes(source)
            path.with_suffix('.h').symlink_to(source_path.with_suffix('.h'))
            public.SOURCE = path
            adapter = Adapter(args)
            report['provenance'][label] = adapter.prepare(directory, deadline)
            report['provenance'][label]['revision'] = revision
            adapters[label] = adapter
        paths = sorted((ROOT/'orchestra/reports/T01-round4-witnesses').glob('*.json'))
        paths += sorted((ROOT/'tests/fuzz_corpus/radialblur').glob('*.json'))
        for index, path in enumerate(paths):
            directory = args.scratch/f'case_{index}'
            directory.mkdir()
            case, saved = load_corpus(path, adapters['after'])
            start = time.monotonic()
            oracle, expected = adapters['after'].oracle(case, directory, deadline)
            row = {'witness': str(path.relative_to(ROOT)), 'input_sha256': sha(case['pixels']),
                   'oracle': oracle, 'oracle_seconds': time.monotonic()-start,
                   'oracle_sha256': sha(expected), 'results': {}}
            assert oracle['status'] == 'ok', row
            for label, adapter in adapters.items():
                row['results'][label] = {}
                for route in adapter.routes:
                    start = time.monotonic()
                    result, raw, guards = adapter.candidate(case, directory, route, deadline)
                    state = ('exact' if raw == expected else 'mismatch') if result['status'] == 'ok' else result['status']
                    row['results'][label][route] = {'result': result, 'state': state,
                        'raw_sha256': sha(raw) if raw else None, 'refusal_guards': guards,
                        'seconds': time.monotonic()-start,
                        'different_bytes': sum(a != b for a, b in zip(raw, expected)) if raw else None,
                        'first_byte': next((i for i, (a, b) in enumerate(zip(raw, expected)) if a != b), None)}
            report['rows'].append(row)
            args.report.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
            for route in adapters['after'].routes:
                base = row['results']['base'][route]
                after = row['results']['after'][route]
                if base['state'] == 'exact':
                    assert after['state'] == 'exact' and base['raw_sha256'] == after['raw_sha256'], row
                before = row['results']['before'][route]
                if before['state'] == 'exact':
                    assert after['state'] == 'exact' and before['raw_sha256'] == after['raw_sha256'], row
            # The unreduced witnesses must recover every original route byte,
            # including the known Classic mismatch of case 425.
            if index < 2:
                assert row['oracle_sha256'] == saved['result']['oracle']['raw_sha256'], row
                for route in adapters['after'].routes:
                    assert row['results']['before'][route]['refusal_guards'] == [
                        'RenderWorld:generic-world-not-admitted@5362'], row
                    assert row['results']['after'][route]['raw_sha256'] == row['results']['base'][route]['raw_sha256'], row
            print('ROUND5', index+1, path.name,
                  {label: {route: value['state'] for route, value in routes.items()}
                   for label, routes in row['results'].items()}, flush=True)
            shutil.rmtree(directory)
        report['complete'] = True
        args.report.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    finally:
        public.SOURCE = source_path
        shutil.rmtree(args.scratch)


if __name__ == '__main__':
    main()
