#!/usr/bin/env python3
"""F12 active Alpha/box admission: independent oracle matrix and replay audit.

--probe runs the matrix with only final tuple admission disabled, before any
production change. The default verifies the three saved campaigns, sanitizes
production replays, compares both corpora at both revisions, and repeats the
matrix through production. No corpus expectations are written.
"""
import argparse
import copy
import itertools
import json
import os
from pathlib import Path
import random
import shutil
import struct
import sys
import time
from types import SimpleNamespace

sys.dont_write_bytecode = True
from verify_kirakira_admission_F10 import (
    ROOT, build, observation, promoted as zero_ray, load_corpus,
    main_checkout, default_worker, olmkirakira, sha)


def active_alpha(case):
    p = {v['slot']: v['value'] for v in case['parameters']}
    w, h = case['geometry']
    return (case['depth'] in (16, 32) and case['profile'] == 'sdr'
            and 9 <= w <= 4096 and 7 <= h <= 4096 and w*h <= 4096*2160
            and p[1] == 1 and p[2] in (1, 2) and p[3] in (1, 2)
            and p[4] == 0 and p[6] == 100 and p[8] == p[9] == 100
            and 1 <= p[5] <= 100 and -2147483648 < round(p[40]*65536) <= 2147483512
            and all(0 <= p[s] <= 1000 for s in (10, 16, 22, 28)) and 0 <= p[34] <= 500)


def matrix_cases(adapter):
    axes = itertools.product(((9, 7), (17, 11)), (16, 32), (1, 2), (1, 2), range(6))
    for index, (geometry, depth, mode, merge, rays) in enumerate(axes):
        rng = random.Random(1200000+index)
        params = adapter.defaults(*geometry)
        values = {1: 1, 2: mode, 3: merge, 4: 0, 5: [1., 1.25, 7.5, 100.][index % 4],
                  6: 100, 7: rng.random(), 8: 100, 9: 100,
                  40: [0, 1, 22, 90, 180, 359, -31, 137][index % 8]/65536}
        for j, slot in enumerate((10, 16, 22, 28, 34)):
            values[slot] = [1, 2, 7, 15, 50, 300][(index+j) % 6] if rays in (j, 5) else 0
            values[slot+3] = (index+j) % 2
        for param in params:
            if param['slot'] in values:
                param['value'] = values[param['slot']]
            elif param['kind'] == 'c':
                param['value'] = [rng.randrange(256) for _ in range(4)]
        pixels = bytearray()
        for _ in range(geometry[0]*geometry[1]*4):
            if depth == 16:
                pixels.extend(struct.pack('<H', rng.choice([0, 1, 32768, rng.randrange(32769)])))
            else:
                pixels.extend(struct.pack('<I', rng.choice([0, 0x80000000, 1, 0x00800000,
                    0x3f7fffff, 0x3f800000, struct.unpack('<I', struct.pack('<f', rng.random()))[0]])))
        yield dict(seed=12, index=index, geometry=list(geometry), depth=depth, profile='sdr',
                   parameters=params, pixels=bytes(pixels), input_padding=3, output_padding=5)


def boundary_cases(adapter):
    base = next(matrix_cases(adapter))
    for index, (depth, mode, rotation) in enumerate(itertools.product(
            (16, 32), (1, 2), (-2147483647, -3000000, 45000000, 2147483512)), 96):
        case = copy.deepcopy(base)
        case.update(index=index, depth=depth)
        if depth == 32:
            case['pixels'] = b''.join(struct.pack('<f', v/32768)
                                     for (v,) in struct.iter_unpack('<H', base['pixels']))
        values = {2: mode, 40: rotation/65536, 10: 1000, 16: 1000,
                  22: 1000, 28: 1000, 34: 500}
        for param in case['parameters']:
            if param['slot'] in values:
                param['value'] = values[param['slot']]
        yield case


def overflow_cases(adapter):
    base = next(matrix_cases(adapter))
    for index, (rotation, length) in enumerate(itertools.product(
            (-2147483648, 0, 45000000, 2147483512), (7, 1000))):
        case = copy.deepcopy(base)
        case['index'] = index
        values = {40: rotation/65536, 10: length, 16: length, 22: length,
                  28: length, 34: min(length, 500)}
        for param in case['parameters']:
            if param['slot'] in values:
                param['value'] = values[param['slot']]
        yield case


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scratch', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--before-source', type=Path)
    parser.add_argument('--campaign-dir', type=Path)
    parser.add_argument('--probe', action='store_true')
    parser.add_argument('--overflow-evidence', action='store_true',
                        help='Reproduce the excluded signed-angle overflow counterexample with gates off')
    args = parser.parse_args()
    if args.overflow_evidence:
        args.probe = True
    scratch = args.scratch.resolve()
    assert scratch.is_relative_to(ROOT/'orchestra/state')
    scratch.mkdir(parents=True, exist_ok=True)
    os.environ.update(TMPDIR=str(scratch), TMP=str(scratch), TEMP=str(scratch))
    deadline = time.monotonic()+7200
    options = SimpleNamespace(max_size=256, case_timeout=60, main=main_checkout(), worker=default_worker())
    report = dict(schema='olm-kira-admission-F12/1', status='running', probe=args.probe,
                  source_sha256=sha(olmkirakira.SOURCE.read_bytes()),
                  core_sha256={str(p.relative_to(ROOT)): sha(p.read_bytes())
                               for p in sorted((ROOT/'core').glob('kirakira*.h'))},
                  aex_sha256=sha((options.main/'plugins_2025/OLMKiraKira.aex').read_bytes()),
                  worker_sha256=sha(options.worker.read_bytes()), campaigns={}, corpus=[], matrix=[], negatives=[])

    def save():
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')

    try:
        after = build(olmkirakira.SOURCE, scratch/'after', options, deadline, args.probe)
        directory = scratch/'case'
        directory.mkdir(exist_ok=True)
        if not args.probe:
            assert args.before_source and args.campaign_dir
            report['before_source_sha256'] = sha(args.before_source.read_bytes())
            for seed in (1, 3, 2):
                campaigns = {kind: json.loads((args.campaign_dir/f'{kind}-seed{seed}.json').read_text())
                             for kind in ('before', 'after', 'gateoff')}
                assert all(c['status'] == 'complete' and c['completed'] == 300 for c in campaigns.values())
                for kind, campaign in campaigns.items():
                    provenance = campaign['provenance']
                    assert provenance['worker_sha256'] == report['worker_sha256']
                    assert provenance['aex_sha256'] == report['aex_sha256']
                    if kind in ('before', 'after'):
                        expected_hash = report['before_source_sha256'] if kind == 'before' else report['source_sha256']
                        assert provenance['dependencies_sha256']['mac/OLMKiraKira/OLMKiraKira.cpp'] == expected_hash
                    else:
                        assert provenance['triage']['sanitizers']
                mapped = {k: {r['index']: r for r in v['cases']} for k, v in campaigns.items()}
                admitted = []
                for index in range(300):
                    case = after.generate(seed, index)
                    old, new, off = (mapped[k][index] for k in ('before', 'after', 'gateoff'))
                    assert sha(case['pixels']) == old['input_sha256'] == new['input_sha256'] == off['input_sha256']
                    assert old['result']['oracle'] == new['result']['oracle'] == off['result']['oracle']
                    expected = zero_ray(case) or active_alpha(case)
                    for route in after.routes:
                        prior, current, disabled = (r['result']['routes'][route] for r in (old, new, off))
                        assert prior['status'] in ('exact', 'refusal')
                        assert current['status'] == ('exact' if expected else prior['status']), (seed, index, route, current)
                        if current['status'] == 'exact':
                            assert disabled['status'] == 'exact'
                            assert disabled['raw_sha256'] == current['raw_sha256']
                        result, raw, *_ = after.candidate(case, directory, route, deadline)
                        assert result['status'] == ('ok' if current['status'] == 'exact' else 'refusal'), result
                        if result['status'] == 'ok':
                            assert sha(raw) == current['raw_sha256']
                    if expected:
                        admitted.append(dict(index=index, input_sha256=new['input_sha256'],
                                             before=old['result'], after=new['result']))
                report['campaigns'][str(seed)] = dict(summaries={k: v['summary'] for k, v in campaigns.items()},
                    provenance={k: v['provenance'] for k, v in campaigns.items()}, admitted=admitted,
                    sanitizer_routes=600, zero_admitted_mismatches=True)
                save()
                print('campaign', seed, 'admitted', len(admitted), '600 sanitized routes', flush=True)
            before = build(args.before_source, scratch/'before', options, deadline)
            before_off = build(args.before_source, scratch/'before-off', options, deadline, True)
            after_off = build(olmkirakira.SOURCE, scratch/'after-off', options, deadline, True)
            for corpus in ('olmkirakira', 'olmkirakira_gate_off_T06'):
                for path in sorted((ROOT/'tests/fuzz_corpus'/corpus).glob('*.json')):
                    case, saved = load_corpus(path, after)
                    oracle, reference = after.oracle(case, directory, deadline)
                    assert oracle['status'] == 'ok', oracle
                    for route in after.routes:
                        old, oldraw = observation(before, case, directory, route, deadline, reference)
                        new, newraw = observation(after, case, directory, route, deadline, reference)
                        assert old == new or (old['status'] == 'refusal' and new['status'] == 'exact'), (path, route, old, new)
                        offold, offraw = observation(before_off, case, directory, route, deadline, reference)
                        offnew, newoffraw = observation(after_off, case, directory, route, deadline, reference)
                        assert offold == offnew and offraw == newoffraw
                        report['corpus'].append(dict(path=str(path.relative_to(ROOT)), index=case['index'], route=route,
                            saved=saved['result']['routes'][route], before=old, after=new,
                            diagnostic=offnew, reference_sha256=sha(reference)))
                save()
                print('corpus', corpus, 'complete', flush=True)
        cases = overflow_cases(after) if args.overflow_evidence else itertools.chain(matrix_cases(after), boundary_cases(after))
        for case in cases:
            oracle, reference = after.oracle(case, directory, deadline)
            assert oracle['status'] == 'ok', (case['index'], oracle)
            row = {k: v for k, v in case.items() if k != 'pixels'}
            row.update(input_sha256=sha(case['pixels']), reference_sha256=sha(reference), routes={})
            report['matrix'].append(row)
            for route in after.routes:
                result, _ = observation(after, case, directory, route, deadline, reference)
                row['routes'][route] = result
                angle = next(p['value'] for p in case['parameters'] if p['slot'] == 40)*65536
                expected = 'mismatch' if args.overflow_evidence and angle == -2147483648 else 'exact'
                assert result['status'] == expected, row
            save()
            if case['index'] % 12 == 11:
                print('matrix', case['index']+1, 'exact both routes', flush=True)
        if not args.probe:
            base = next(matrix_cases(after))
            changes = [('channel', 1, 2), ('gaussian', 2, 3), ('exponential', 2, 4),
                       ('approximation', 4, 1), ('gain', 5, .5), ('strength', 6, 99),
                       ('glow-opacity', 8, 99), ('source-opacity', 9, 99),
                       ('length-bound', 10, 1001), ('highlight-bound', 34, 501),
                       ('angle-add-overflow', 40, 2147483647/65536),
                       ('angle-negate-overflow', 40, -2147483648/65536)]
            negatives = []
            for label, slot, value in changes:
                case = copy.deepcopy(base)
                next(p for p in case['parameters'] if p['slot'] == slot)['value'] = value
                negatives.append((label, case))
            case = copy.deepcopy(base)
            case.update(depth=8, pixels=bytes(v//129 for (v,) in struct.iter_unpack('<H', base['pixels'])))
            negatives.append(('PF8-active', case))
            for label, word in [('hdr', 0x40000000), ('signed', 0xbf800000), ('nan', 0x7fc12345)]:
                case = copy.deepcopy(base)
                case.update(depth=32, pixels=struct.pack('<I', word)+bytes(len(base['pixels'])*2-4))
                negatives.append((label, case))
            for geometry in ((8, 7), (9, 6), (1, 1)):
                case = copy.deepcopy(base)
                case.update(geometry=list(geometry), pixels=base['pixels'][:geometry[0]*geometry[1]*8])
                negatives.append((f'tiny-{geometry}', case))
            for label, case in negatives:
                row = dict(label=label, routes={})
                for route in after.routes:
                    result, raw, *_ = after.candidate(case, directory, route, deadline)
                    assert result['status'] == 'refusal' and not raw, (label, result)
                    row['routes'][route] = result
                report['negatives'].append(row)
            print('negative controls', len(negatives)*2, 'clean refusals', flush=True)
        report['status'] = 'passed'
        save()
        print('PASS', flush=True)
    except BaseException as exc:
        report.update(status='failed', error=repr(exc))
        save()
        raise
    finally:
        for name in ('before', 'after', 'before-off', 'after-off', 'case'):
            shutil.rmtree(scratch/name, ignore_errors=True)


if __name__ == '__main__':
    main()
