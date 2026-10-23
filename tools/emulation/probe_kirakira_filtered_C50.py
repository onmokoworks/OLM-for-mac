#!/usr/bin/env python3
"""Independent filtered-source admission matrices; original public Smart oracle."""
import argparse
from collections import Counter
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
from types import SimpleNamespace

from probe_kirakira_smart_C07 import cases as prior_cases
from trace_kirakira_numeric_F09 import build_mac, original_trace, raw_diff
from verify_kirakira_admission_F10 import (
    ROOT, adapter_class, observation, main_checkout, default_worker, olmkirakira, sha)


def cases(adapter, domain, boundary, negative=False):
    if negative:
        families = ('finite-color-negative',) if domain == 'color-approx' else (
            'finite-color-negative', 'finite-brightness-negative')
        for family in families:
            for case in prior_cases(adapter, family):
                for param in case['parameters']:
                    if param['slot'] == 4: param['value'] = 1
                yield case
        return
    if domain == 'color-approx':
        family = 'finite-color-boundary' if boundary else 'finite-color-box'
        for case in prior_cases(adapter, family):
            if boundary:
                case['geometry'] = list(((4, 4), (4, 9), (9, 4), (17, 11))[case['index'] % 4])
                size = case['geometry'][0] * case['geometry'][1] * 16
                case['pixels'] = (case['pixels'] * (1 + size // len(case['pixels'])))[:size]
            elif min(case['geometry']) < 4:
                continue
            p = {v['slot']: v for v in case['parameters']}
            p[4]['value'] = 1
            p[7]['value'] = (0, .1, .5, 1)[case['index'] % 4]
            yield case
    else:
        family = 'nonfinite-alpha-lengths' if boundary else 'nonfinite-alpha-box'
        for case in prior_cases(adapter, family):
            if case['geometry'] != [7, 11]:
                continue
            p = {v['slot']: v for v in case['parameters']}
            modes = (1, 3) if p[2]['value'] == 1 else (2,)
            for mode in modes:
                for geometry in ((4, 4), (7, 11), (9, 7)):
                    c = copy.deepcopy(case)
                    c['geometry'] = list(geometry)
                    size = geometry[0] * geometry[1] * 16
                    c['pixels'] = (case['pixels'] * 2)[:size]
                    for v in c['parameters']:
                        if v['slot'] == 2: v['value'] = mode
                        if v['slot'] == 4: v['value'] = 1
                    yield c


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--domain', choices=('color-approx', 'alpha-approx'), required=True)
    p.add_argument('--negative', action='store_true', help='Require refusal outside the admitted source domain')
    p.add_argument('--boundary', action='store_true')
    p.add_argument('--trace-index', type=int, help='Trace this independent matrix index with F46 imports')
    p.add_argument('--gate-off', action='store_true')
    p.add_argument('--source', type=Path, default=olmkirakira.SOURCE)
    p.add_argument('--scratch', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--require-exact', action='store_true')
    args = p.parse_args()
    s = args.scratch.resolve()
    assert s.is_relative_to(ROOT/'orchestra/state')
    s.mkdir(parents=True, exist_ok=True)
    os.environ.update(TMPDIR=str(s), TMP=str(s), TEMP=str(s))
    options = SimpleNamespace(max_size=256, case_timeout=180,
                              main=main_checkout(), worker=default_worker())
    deadline = time.monotonic() + 7200
    a = adapter_class(args.source, args.gate_off)(options)
    r = dict(schema='olm-kira-filtered-C50/1', status='running', domain=args.domain,
             boundary=args.boundary, negative=args.negative, gate_off=args.gate_off, rows=[],
             source_sha256=sha(args.source.read_bytes()),
             worker_sha256=sha(options.worker.read_bytes()),
             aex_sha256=sha(a.aex.read_bytes()))
    def save():
        r['counts'] = dict(Counter(x['result']['status'] for x in r['rows']))
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(r, indent=2, sort_keys=True)+'\n')
    try:
        if args.trace_index is None:
            (s/'build').mkdir()
            a.binary, _ = a.build(s/'build', deadline)
        else:
            a = build_mac(args.source, s/'build', options, deadline, args.gate_off)
            objects = sorted((s/'build'/'ucrtmath').glob('*.o'))
            assert len(objects) == 7
            library = s/'trace-ucrt.dylib'
            subprocess.run(['clang', '-dynamiclib', *map(str, objects), '-o', str(library)], check=True)
            a.env['F09_TRACE'] = str(s/'case')
        (s/'case').mkdir()
        for i, c in enumerate(cases(a, args.domain, args.boundary, args.negative)):
            if args.trace_index is not None and i != args.trace_index: continue
            oracle, ref = a.oracle(c, s/'case', deadline, 'smart')
            result, raw = observation(a, c, s/'case', 'smart', deadline, ref)
            row = {k:v for k,v in c.items() if k != 'pixels'}
            row.update(matrix_index=i, input_sha256=sha(c['pixels']), oracle=oracle,
                       reference_sha256=sha(ref), result=result)
            r['rows'].append(row)
            if args.trace_index is not None:
                original = original_trace(c, a.aex, aex_percent_materialization=True,
                                          ucrt_math=library)
                row['original_trace_status'] = original['status']
                row['original_trace_error'] = original.get('error')
                stages = original['stages']
                row['public_bound'] = bytes.fromhex(stages.get('output', '')) == ref
                row['paired'] = {}
                for name in ('source_full', 'source', 'seed', 'ray0', 'ray1', 'ray2', 'ray3',
                             'ray4', 'glow', 'glow_full', 'composed'):
                    expected = bytes.fromhex(stages[name])
                    actual = (s/'case'/(name+'.raw')).read_bytes()
                    row['paired'][name] = dict(exact=expected == actual,
                        diff=None if expected == actual else raw_diff(expected, actual, 32))
                row['first_divergent_stage'] = next((k for k,v in row['paired'].items() if not v['exact']), None)
                save()
                assert row['public_bound'], 'trace must bind to public F46 output'
            save()
            assert oracle['status'] == 'ok', row
            if args.require_exact: assert result['status'] == 'exact', row
            if args.negative: assert result['status'] == 'refusal', row
            if (i+1)%24 == 0: print(i+1, r['counts'], flush=True)
        r['status'] = 'complete'; save()
        print('COMPLETE', r['counts'], flush=True)
    except BaseException as exc:
        r.update(status='failed', error=repr(exc)); save(); raise
    finally:
        for name in ('build', 'case'): shutil.rmtree(s/name, ignore_errors=True)


if __name__ == '__main__':
    main()
