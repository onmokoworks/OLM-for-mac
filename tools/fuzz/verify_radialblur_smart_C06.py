#!/usr/bin/env python3
"""Replay C06 Smart campaign hashes with sanitizers and independent odd strides.

Only the retained original worker supplies numerical expectations. Campaigns
regenerate their inputs from seed/index; no saved final pixels enter production.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import random
import shutil
import struct
import sys
import tempfile
import time
import unittest
from types import SimpleNamespace

sys.dont_write_bytecode = True
from adapters.radialblur import Adapter, public
from core import sha, raw_diff

ROOT = Path(__file__).resolve().parents[2]
MAIN = ROOT.parent.parent if ROOT.parent.name == 'worktrees' else ROOT
WORKER = Path('/Users/onmk/.cache/olm-emu/radial_offset_reference_20261002/target/release/aex-guest-worker')


def independent_cases(adapter, matrix='alignment'):
    for geometry in ((3, 5), (11, 7)):
        w, h = geometry
        for depth in ((16, 32) if matrix == 'alignment' else (8, 16, 32)):
            rng = random.Random(61000 + w * 100 + depth)
            pixels = b''
            for i in range(w * h):
                values = [rng.choice([0, 16384, 32768]), *[rng.randrange(32769) for _ in range(3)]]
                pixels += (struct.pack('<4B', *[v * 255 // 32768 for v in values]) if depth == 8 else
                           struct.pack('<4H', *values) if depth == 16 else
                           struct.pack('<4f', *[v / 32768 for v in values]))
            for blur_type in (1, 2):
                variants = range(3) if matrix == 'alignment' else range(20)
                for variant in variants:
                    params = adapter.defaults(w, h)
                    changes = ({1: blur_type, 4: 4},
                               {1: blur_type, 4: 7, 10: 3, 6: 2, 12: 4},
                               {1: blur_type, 4: 4, 7: 25, 13: 50})[variant % 3]
                    if matrix == 'angles':
                        angles = [-32768, -32768 + 1/65536, -720, -360 - 1/65536,
                                  -360, 0, 360, 360 + 1/65536, 720, 32768 - 1/65536]
                        changes = {1: blur_type, 4: 7, 10: 3, 17: 1 if variant < 10 else 2.25,
                                   18: angles[variant % 10]}
                    for p in params:
                        if p['slot'] in changes:
                            p['value'] = changes[p['slot']]
                    yield dict(geometry=list(geometry), depth=depth, profile='sdr', parameters=params,
                               input_padding=0, output_padding=0, pixels=pixels, variant=variant)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source', type=Path, default=public.SOURCE)
    ap.add_argument('--campaign', type=Path, action='append', default=[])
    ap.add_argument('--evidence', type=Path, help='Replay compact C06 comparison evidence')
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--independent', action='store_true')
    ap.add_argument('--matrix', choices=('alignment', 'angles'), default='alignment')
    ap.add_argument('--ordinary', action='store_true')
    ap.add_argument('--smoke', action='store_true')
    args = ap.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT / 'orchestra/state/C06-radial-smart')
    out.mkdir(parents=True, exist_ok=True)
    public.SOURCE = args.source.resolve()
    os.environ.update(TMPDIR=str(out), TMP=str(out), TEMP=str(out),
                      OLM_RADIAL_CANDIDATE_SANITIZE='0' if args.ordinary else '1')
    os.environ.pop('OLM_RADIAL_CANDIDATE_BYPASS', None)
    adapter = Adapter(SimpleNamespace(max_size=256, case_timeout=60, main=MAIN, worker=WORKER))
    deadline = time.monotonic() + 7200
    report = dict(provenance=adapter.prepare(out, deadline), campaigns=[], independent=[], failures=[])
    work = out / 'case'
    work.mkdir(exist_ok=True)

    def render(case):
        result, raw, guards = adapter.candidate(case, work, 'smart', deadline)
        result = dict(result, raw_sha256=sha(raw), guards=guards)
        # Harness metadata includes lifecycle and input/padding guards.
        return result, raw

    campaigns = [(path, json.loads(path.read_text())) for path in args.campaign]
    if args.evidence:
        for comparison in json.loads(args.evidence.read_text())['comparisons']:
            if comparison['kind'] != 'cases':
                continue
            campaigns.append((args.evidence, dict(seed=comparison['seed'], cases=[dict(
                index=row['identity'], input_sha256=row['input_sha256'], result=dict(
                    routes=dict(smart=row['after']), oracles=dict(smart=row['oracle'])))
                for row in comparison['rows']])))
    for path, campaign in campaigns:
        rows = []
        for row in campaign['cases']:
            case = adapter.generate(campaign['seed'], row['index'])
            assert sha(case['pixels']) == row['input_sha256']
            actual, raw = render(case)
            expected = row['result']['routes']['smart']
            oracle = row['result']['oracles']['smart']
            same = ((actual['status'] == 'ok' and expected['status'] in ('exact', 'mismatch', 'uncompared')
                     and actual['raw_sha256'] == expected['raw_sha256']) or
                    (actual['status'] == expected['status'] == 'refusal' and actual['error'] == expected['error']))
            exact = actual['status'] == 'ok' and oracle['status'] == 'ok' and actual['raw_sha256'] == oracle['raw_sha256']
            clean = not actual.get('sanitizer')
            rows.append(dict(index=row['index'], same=same, exact=exact, clean=clean, result=actual))
            if not same or not clean or (expected['status'] == 'exact' and not exact):
                report['failures'].append(dict(campaign=str(path), index=row['index'], same=same, clean=clean, exact=exact))
        report['campaigns'].append(dict(path=str(path), seed=campaign['seed'], rows=rows))
        print('CAMPAIGN', campaign['seed'], len(rows), 'same', sum(r['same'] for r in rows),
              'clean', sum(r['clean'] for r in rows), flush=True)

    if args.independent:
        for index, case in enumerate(independent_cases(adapter, args.matrix)):
            oracle, reference = adapter.oracle(case, work, deadline, 'smart')
            row = dict(index=index, case={k:v for k,v in case.items() if k != 'pixels'},
                       input_sha256=sha(case['pixels']), oracle=oracle, reference_sha256=sha(reference), layouts=[])
            for ip, op in ((0, 0), (1, 5), (3, 11)):
                varied = dict(case, input_padding=ip, output_padding=op)
                result, raw = render(varied)
                exact = oracle['status'] == result['status'] == 'ok' and raw == reference
                clean = not result.get('sanitizer')
                layout = dict(input_padding=ip, output_padding=op, result=result, exact=exact, clean=clean)
                if oracle['status'] == result['status'] == 'ok' and not exact:
                    layout['diff'] = raw_diff(reference, raw, case['depth'])
                row['layouts'].append(layout)
                if not exact or not clean:
                    report['failures'].append(dict(independent=index, input_padding=ip, exact=exact, clean=clean))
            report['independent'].append(row)
            print('INDEPENDENT', index, [r['exact'] for r in row['layouts']], flush=True)
    if args.smoke:
        from validate_radialblur_tests_T01 import SMOKE, Results
        tempfile.tempdir = str(out)
        with tempfile.TemporaryDirectory(prefix='sdk_', dir=out) as name:
            sdk = Path(name)
            for directory in ('Headers', 'Util', 'Resources'):
                (sdk / directory).symlink_to(MAIN / directory, target_is_directory=True)
            (sdk / 'mac').symlink_to(ROOT / 'mac', target_is_directory=True)
            suite = unittest.TestSuite()
            for stem in SMOKE:
                if stem == 'parameter_ui_parity_20260806':
                    continue  # Existing unrelated stale Thickness string assertion.
                path = ROOT / 'tests' / f'test_olmradialblur_{stem}.py'
                spec = importlib.util.spec_from_file_location(path.stem, path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                module.ROOT = sdk
                module.SOURCE = public.SOURCE
                for key, function in vars(module).items():
                    if key.startswith('test_') and callable(function):
                        suite.addTest(unittest.FunctionTestCase(function, description=path.name + ':' + key))
            result = unittest.TextTestRunner(verbosity=2, resultclass=Results).run(suite)
            report['smoke'] = dict(tests=result.testsRun, failures=len(result.failures),
                                   errors=len(result.errors), rows=result.rows)
            if not result.wasSuccessful():
                report['failures'].append(dict(smoke=report['smoke']))
    report['status'] = 'pass' if not report['failures'] else 'fail'
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    shutil.rmtree(out / 'build')
    print('RESULT', report['status'], 'failures', len(report['failures']), flush=True)
    return bool(report['failures'])


if __name__ == '__main__':
    raise SystemExit(main())
