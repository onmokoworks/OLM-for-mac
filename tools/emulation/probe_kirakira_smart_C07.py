#!/usr/bin/env python3
"""C07 independent control matrices and public-bound paired Smart traces.

Uses the original AEX and retained public worker. No corpus is rewritten.
"""
import argparse
import copy
from collections import Counter
import itertools
import ctypes
import math
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
    if family == 'gaussian-controls':
        for case in cases(adapter, 'strength-combined'):
            i = case['index']
            values = {2: 3, 10: 2+i%4, 16: 7, 22: 3 if i%2 else 0,
                      28: 15 if i%3 else 0, 34: 0}
            for param in case['parameters']:
                if param['slot'] in values: param['value'] = values[param['slot']]
                if param['slot'] in (13,19,25,31,37): param['value'] = 0
            yield case
        return
    if family == 'approximation-zero-negative':
        for i, (geometry, depth) in enumerate(itertools.product(
                ((1, 1), (1, 9), (2, 2), (2, 9), (3, 3)), (8, 16, 32))):
            case = matrix_case(adapter, i, geometry, depth, 1, 2, 1)
            for param in case['parameters']:
                if param['slot'] == 4: param['value'] = 1
            yield case
        for i in range(3):
            case = matrix_case(adapter, 15+i, (7, 11), 32, 1, 2, 1)
            for param in case['parameters']:
                if param['slot'] == 4: param['value'] = 1
                if i == 0 and param['slot'] == 10: param['value'] = 1
                if i == 1 and param['slot'] == 9: param['value'] = 97
            if i == 2: case['pixels'] = struct.pack('<f', 2.0) + case['pixels'][4:]
            yield case
        return
    if family == 'approximation-zero':
        for i, (geometry, depth, mode, channel) in enumerate(itertools.product(
                ((4, 4), (4, 9), (9, 4), (6, 8), (7, 11), (9, 7), (17, 13)),
                (8, 16, 32), (1, 2, 3), (1, 2, 3, 4, 5, 6))):
            case = matrix_case(adapter, i, geometry, depth, 1+i%2, mode, channel)
            for param in case['parameters']:
                if param['slot'] == 4: param['value'] = 1
            yield case
        return
    if family == 'approximation':
        for i, (geometry, depth, mode, merge, rays) in enumerate(itertools.product(
                ((2, 2), (2, 9), (9, 2), (6, 8), (7, 11), (9, 7), (17, 13)),
                (8, 16, 32), (1, 2), (1, 2), (0, 1, 2))):
            case = matrix_case(adapter, i, geometry, depth, merge, mode, 1)
            controls = {4: 1, 5: (1, 1.25, 100)[i % 3],
                        6: (0, 1, 97, 100, 537, 1000)[i % 6],
                        8: (0, 1, 40, 100, 1703, 10000)[(i // 3) % 6],
                        9: (0, 1, 40, 97, 100)[i % 5], 40: 22 / 65536}
            for j, slot in enumerate((10, 16, 22, 28, 34)):
                controls[slot] = (0, 1, (7, 2, 3, 15, 5)[j])[rays]
            for param in case['parameters']:
                if param['slot'] in controls: param['value'] = controls[param['slot']]
            yield case
        return
    if family == 'invalid-input':
        base = next(cases(adapter, 'finite-seed'))
        for i, (channel, bits) in enumerate(((0, 0xbf800000), (0, 0x7f800000),
                (0, 0x7fc00001), (1, 0x7fc00001), (2, 0xff800000), (0, 0x7f7fffff))):
            case = copy.deepcopy(base)
            data = bytearray(case['pixels'])
            struct.pack_into('<I', data, channel * 4, bits)
            case.update(index=i, pixels=bytes(data))
            if i == 5:
                for param in case['parameters']:
                    if param['slot'] == 6: param['value'] = 1000
            yield case
        return
    if family in ('finite-lengths', 'signed-finite-lengths'):
        for case in cases(adapter, 'signed-finite-seed' if family.startswith('signed-') else 'finite-seed'):
            i = case['index']
            lengths = (1, 2, 3, 4, 5, 6, 7, 15, 50, 1000)
            for param in case['parameters']:
                if param['slot'] in (10, 16):
                    param['value'] = lengths[(i + (param['slot'] == 16)) % len(lengths)]
            yield case
        return
    if family in ('finite-seed', 'signed-finite-seed'):
        powf = ctypes.CDLL(None).powf
        powf.argtypes = (ctypes.c_float, ctypes.c_float)
        powf.restype = ctypes.c_float
        f32 = lambda x: struct.unpack('<f', struct.pack('<f', x))[0]
        for case in cases(adapter, 'finite-alpha' if family.startswith('signed-') else 'finite-nonnegative'):
            params = {p['slot']: p['value'] for p in case['parameters']}
            exponent = max(f32(0.001), f32(f32(params[6]) * f32(0.01)))
            if all(math.isfinite(powf(struct.unpack_from('<f', case['pixels'], i)[0], exponent))
                   for i in range(0, len(case['pixels']), 16)):
                yield case
        return
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
    p.add_argument('--family', choices=('source-opacity', 'glow-opacity', 'opacity-combined', 'strength', 'strength-combined', 'finite-alpha', 'finite-nonnegative', 'finite-sdr-alpha', 'finite-seed', 'finite-lengths', 'signed-finite-seed', 'signed-finite-lengths', 'invalid-input', 'approximation', 'approximation-zero', 'approximation-zero-negative', 'gaussian-controls'), default='source-opacity')
    p.add_argument('--trace-index', type=int)
    p.add_argument('--campaign-seed', type=int)
    p.add_argument('--gate-off', action='store_true')
    p.add_argument('--require-exact', action='store_true')
    p.add_argument('--require-refusal', action='store_true')
    p.add_argument('--expect-finite-domain', action='store_true')
    p.add_argument('--keep-trace', action='store_true', help='Keep raw trace planes in ticket scratch')
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
                row['aex_row_filter_calls_kernel_width_channels'] = original['row_filters']
                row['aex_resize_writers'] = original.get('resize_writers', [])
                stages = original['stages']
                if args.keep_trace:
                    for name, data in stages.items():
                        if isinstance(data, str): (directory / ('aex_' + name + '.raw')).write_bytes(bytes.fromhex(data))
                row['public_bound'] = oracle['status'] == 'ok' and bytes.fromhex(stages['output']) == reference
                paired = {}
                for name in ('source_full', 'source', 'seed', 'ray0', 'ray1', 'ray2', 'ray3', 'ray4', 'glow', 'glow_full', 'composed'):
                    expected = bytes.fromhex(stages[name])
                    actual = (directory / (name + '.raw')).read_bytes()
                    paired[name] = dict(exact=expected == actual, aex_sha256=sha(expected),
                        mac_sha256=sha(actual), diff=None if expected == actual else raw_diff(expected, actual, 32))
                row['helper_paired'] = {}
                for name, data in stages.items():
                    file = directory / (name + '.raw')
                    if name.startswith('helper') and not name.endswith('_shape') and file.exists():
                        expected, actual = bytes.fromhex(data), file.read_bytes()
                        row['helper_paired'][name] = dict(exact=expected == actual,
                            diff=None if expected == actual else raw_diff(expected, actual, 32))
                row['paired'] = paired
                row['first_divergent_stage'] = next((k for k, v in paired.items() if not v['exact']), None)
                save()
                assert row['public_bound'], 'unbound trace: no first-stage claim'
            save()
            if args.require_refusal:
                assert not args.require_exact and result['status'] == 'refusal', (case['index'], result)
                continue
            assert oracle['status'] == 'ok', oracle
            if args.expect_finite_domain:
                assert not args.gate_off and case['depth'] == 32
                params = {p['slot']: p['value'] for p in case['parameters']}
                powf = ctypes.CDLL(None).powf
                powf.argtypes = (ctypes.c_float, ctypes.c_float)
                powf.restype = ctypes.c_float
                f32 = lambda x: struct.unpack('<f', struct.pack('<f', x))[0]
                exponent = max(f32(0.001), f32(f32(params[6]) * f32(0.01)))
                words = struct.unpack('<' + 'f' * (len(case['pixels']) // 4), case['pixels'])
                valid = all(math.isfinite(x) for x in words) and all(
                    a >= 0 and math.isfinite(powf(a, exponent)) for a in words[::4])
                row['expected_domain_status'] = 'exact' if valid else 'refusal'
                save()
                assert result['status'] == row['expected_domain_status'], (case['index'], result)
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
        if not args.keep_trace: shutil.rmtree(scratch / 'case', ignore_errors=True)


if __name__ == '__main__':
    main()
