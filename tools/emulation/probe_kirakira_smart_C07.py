#!/usr/bin/env python3
"""C07 independent control matrices and public-bound paired Smart traces.

Uses the original AEX and retained public worker. No corpus is rewritten.
"""
import argparse
from collections import Counter
import itertools
import json
import os
import random
import struct
from pathlib import Path
import shutil
import sys
import time
from types import SimpleNamespace

sys.dont_write_bytecode = True
from verify_kirakira_admission_F10 import (
    ROOT, adapter_class, matrix_case, observation, main_checkout, default_worker,
    olmkirakira, sha)
from trace_kirakira_numeric_F09 import build_mac, original_trace, raw_diff


def cases(adapter, family):
    if family in ('finite-nonnegative', 'finite-sdr-alpha'):
        for case in cases(adapter, 'finite-alpha'):
            data = bytearray(case['pixels'])
            for offset in range(0, len(data), 16):
                word = struct.unpack_from('<I', data, offset)[0] & 0x7fffffff
                if family == 'finite-sdr-alpha':
                    word = min(word, 0x3f800000)
                struct.pack_into('<I', data, offset, word)
            case['pixels'] = bytes(data)
            yield case
        return
    if family == 'finite-alpha':
        for i, (geometry, mode, merge, strength, profile) in enumerate(itertools.product(
                ((1, 1), (1, 9), (7, 11), (9, 7)), (1, 2), (1, 2),
                (0, 1, 97, 100, 537, 1000), ('hdr', 'signed', 'extreme'))):
            case = matrix_case(adapter, i, geometry, 32, merge, mode, 1)
            controls = {5: (1, 1.25, 100)[i % 3], 6: strength, 8: 100, 9: 100,
                        40: 22 / 65536, 10: 7, 16: 2, 22: 0, 28: 0, 34: 3}
            controls.update({s: 0 for s in (13, 19, 25, 31, 37)})
            for param in case['parameters']:
                if param['slot'] in controls:
                    param['value'] = controls[param['slot']]
            rng = random.Random(2026070000 + i)
            pixels = bytearray()
            for word in range(geometry[0] * geometry[1] * 4):
                if profile == 'extreme':
                    value = rng.choice((0, 0x80000000, 1, 0x80000001, 0x00800000,
                        0x80800000, 0x3f800000, 0xbf800000, 0x7f7fffff, 0xff7fffff))
                    pixels.extend(struct.pack('<I', value))
                else:
                    pixels.extend(struct.pack('<f', rng.uniform(-4 if profile == 'signed' else 0,
                                                               4 if profile == 'signed' else 8)))
            case.update(pixels=bytes(pixels), profile=profile)
            yield case
        return
    values = (0, 1, 40, 97, 100, 101, 1703, 10000)
    if family.startswith('strength'):
        values = (0, 1, 40, 97, 100, 101, 537, 1000)
    for i, (geometry, depth, mode, merge, value) in enumerate(itertools.product(
            ((1, 1), (7, 11), (9, 7)), (8, 16, 32), (1, 2), (1, 2), values)):
        case = matrix_case(adapter, i, geometry, depth, merge, mode, 1)
        controls = {5: 1.25, 6: 100, 8: 100, 9: 100, 40: 22 / 65536,
                    10: 7, 16: 2, 22: 0, 28: 0, 34: 3}
        controls.update({s: 0 for s in (13, 19, 25, 31, 37)})
        controls[{'source-opacity': 9, 'glow-opacity': 8, 'strength': 6, 'strength-combined': 6, 'opacity-combined': 8}[family]] = value
        if family == 'strength-combined':
            controls[8] = (0, 1, 40, 97, 100, 101, 1703, 10000)[(i // 8) % 8]
            controls[9] = (0, 1, 40, 97, 100)[i % 5]
            controls.update({s: (i + s) % 2 for s in (13, 19, 25, 31, 37)})
        if family == 'opacity-combined':
            controls[9] = (0, 1, 40, 97, 100)[i % 5]
            controls.update({s: (i + s) % 2 for s in (13, 19, 25, 31, 37)})
        if family == 'source-opacity' and value > 100:
            continue  # The declared source opacity range is 0..100.
        for param in case['parameters']:
            if param['slot'] in controls:
                param['value'] = controls[param['slot']]
        yield case


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--scratch', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--source', type=Path, default=olmkirakira.SOURCE)
    p.add_argument('--family', choices=('source-opacity', 'glow-opacity', 'opacity-combined', 'strength', 'strength-combined', 'finite-alpha', 'finite-nonnegative', 'finite-sdr-alpha'), default='source-opacity')
    p.add_argument('--trace-index', type=int)
    p.add_argument('--campaign-seed', type=int)
    p.add_argument('--gate-off', action='store_true')
    p.add_argument('--require-exact', action='store_true')
    args = p.parse_args()
    scratch = args.scratch.resolve()
    assert scratch.is_relative_to(ROOT / 'orchestra/state')
    scratch.mkdir(parents=True, exist_ok=True)
    os.environ.update(TMPDIR=str(scratch), TMP=str(scratch), TEMP=str(scratch),
                      OLM_KK_PROCESS_ATTACH_DIAGNOSTIC='1',
                      OLM_KK_MANUAL_CRT_INITIALIZERS_DIAGNOSTIC='1')
    options = SimpleNamespace(max_size=256, case_timeout=180,
                              main=main_checkout(), worker=default_worker())
    deadline = time.monotonic() + 7200
    report = dict(schema='olm-kira-C07/1', family=args.family, rows=[], status='running',
                  gate_off=args.gate_off, trace_powf='host float powf, matching retained worker; not native UCRT', source_sha256=sha(args.source.read_bytes()),
                  worker_sha256=sha(options.worker.read_bytes()),
                  aex_sha256=sha((options.main / 'plugins_2025/OLMKiraKira.aex').read_bytes()))
    def save():
        args.report.parent.mkdir(parents=True, exist_ok=True)
        report['counts'] = dict(Counter(r['result']['status'] for r in report['rows']))
        args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    try:
        if args.trace_index is not None:
            adapter = build_mac(args.source, scratch / 'build', options, deadline, args.gate_off)
        else:
            (scratch / 'build').mkdir()
            adapter = adapter_class(args.source, args.gate_off)(options)
            adapter.binary, _ = adapter.build(scratch / 'build', deadline)
        directory = scratch / 'case'
        directory.mkdir(exist_ok=True)
        selected = cases(adapter, args.family)
        if args.campaign_seed is not None:
            assert args.trace_index is not None
            selected = [adapter.generate(args.campaign_seed, args.trace_index)]
        for case in selected:
            if args.trace_index is not None and case['index'] != args.trace_index:
                continue
            if args.trace_index is not None:
                adapter.env['F09_TRACE'] = str(directory)
            oracle, reference = adapter.oracle(case, directory, deadline, 'smart')
            result, raw = observation(adapter, case, directory, 'smart', deadline, reference)
            row = {k: v for k, v in case.items() if k != 'pixels'}
            row.update(input_sha256=sha(case['pixels']), oracle=oracle, result=result,
                       reference_sha256=sha(reference))
            report['rows'].append(row)
            if args.trace_index is not None:
                original = original_trace(case, adapter.aex, aex_percent_materialization=True, host_powf=True)
                stages = original['stages']
                row['public_bound'] = oracle['status'] == 'ok' and bytes.fromhex(stages['output']) == reference
                paired = {}
                for name in ('source', 'seed', 'ray0', 'ray1', 'ray2', 'ray3', 'ray4', 'glow', 'composed'):
                    expected = bytes.fromhex(stages[name])
                    actual = (directory / (name + '.raw')).read_bytes()
                    paired[name] = dict(exact=expected == actual, aex_sha256=sha(expected),
                        mac_sha256=sha(actual), diff=None if expected == actual else raw_diff(expected, actual, 32))
                row['paired'] = paired
                row['first_divergent_stage'] = next((k for k, v in paired.items() if not v['exact']), None)
                save()
                assert row['public_bound'], 'unbound trace: no first-stage claim'
            save()
            assert oracle['status'] == 'ok', oracle
            if args.require_exact:
                assert result['status'] == 'exact', (case['index'], result)
            if len(report['rows']) % 24 == 0:
                print('PROGRESS', len(report['rows']), report['counts'], flush=True)
        report['status'] = 'complete'
        save()
        print('COMPLETE', report['counts'], flush=True)
    except BaseException as exc:
        report.update(status='failed', error=repr(exc))
        save()
        raise
    finally:
        shutil.rmtree(scratch / 'build', ignore_errors=True)
        shutil.rmtree(scratch / 'case', ignore_errors=True)


if __name__ == '__main__':
    main()
