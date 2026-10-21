#!/usr/bin/env python3
"""Remeasure unreduced Round-6 fuzz witnesses with one shared AEX result.

Production/base source, inputs and raw hashes are retained in the report.
The longer subprocess deadline resolves oracle timeouts without changing any
production admission guard, corpus expectation, or emulation math.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

from adapters.radialblur import Adapter, ROOT, public
from core import sha, raw_diff


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', type=Path, required=True)
    parser.add_argument('--scratch', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--main', type=Path, default=ROOT.parent.parent)
    parser.add_argument('--base', default='95b185eb')
    parser.add_argument('--case-timeout', type=float, default=120)
    parser.add_argument('--max-size', type=int, default=256)
    parser.add_argument('--seed', type=int, default=1)
    parser.add_argument('--indices', type=int, nargs='+', default=[89, 193, 363, 421, 425, 459])
    args = parser.parse_args()
    args.scratch = args.scratch.resolve()
    assert args.scratch.is_relative_to(ROOT/'orchestra/state/T01-radial-offset-promote')
    assert not os.environ.get('OLM_RADIAL_CANDIDATE_BYPASS')
    assert not os.environ.get('OLM_RADIAL_CANDIDATE_SANITIZE')
    args.scratch.mkdir(parents=True, exist_ok=False)
    os.environ['TMPDIR'] = str(args.scratch)
    source_path = public.SOURCE
    report = dict(seed=args.seed, case_timeout=args.case_timeout, provenance={}, rows=[])
    try:
        adapters = {}
        deadline = time.monotonic() + 3600
        for label, revision in [('base', args.base), ('after', None)]:
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
            adapters[label] = adapter
        for index in args.indices:
            directory = args.scratch/f'case_{index}'
            directory.mkdir()
            case = adapters['after'].generate(args.seed, index)
            start = time.monotonic()
            oracle, expected = adapters['after'].oracle(case, directory, deadline)
            row = {k: v for k, v in case.items() if k != 'pixels'}
            row.update(input_sha256=sha(case['pixels']), oracle=oracle,
                       oracle_seconds=time.monotonic()-start, results={})
            if oracle['status'] == 'ok':
                row['oracle']['raw_sha256'] = sha(expected)
            for label, adapter in adapters.items():
                row['results'][label] = {}
                for route in adapter.routes:
                    start = time.monotonic()
                    result, raw, guards = adapter.candidate(case, directory, route, deadline)
                    result.update(seconds=time.monotonic()-start, refusal_guards=guards)
                    if result['status'] == 'ok':
                        result['raw_sha256'] = sha(raw)
                        result['status'] = ('exact' if raw == expected else 'mismatch') if oracle['status'] == 'ok' else 'uncompared'
                        if result['status'] == 'mismatch':
                            result['diff'] = raw_diff(expected, raw, case['depth'])
                    row['results'][label][route] = result
            report['rows'].append(row)
            args.report.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
            print('ROUND6_WITNESS', index, oracle['status'],
                  {label: {route: value['status'] for route, value in routes.items()}
                   for label, routes in row['results'].items()}, flush=True)
            shutil.rmtree(directory)
        report['complete'] = True
        args.report.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    finally:
        public.SOURCE = source_path
        shutil.rmtree(args.scratch)


if __name__ == '__main__':
    main()
