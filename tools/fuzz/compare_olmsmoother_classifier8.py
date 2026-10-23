#!/usr/bin/env python3
"""Compare Mac Classifier8 trace values with the original AEX classifier.

The Mac trace labels are emitted by ScanlinePixel8_Main; the AEX side calls the
captured Classifier8 entry directly with the same 3x3 neighbor table. This is a
paired stage comparison for the two T11 mismatch representatives.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import struct
import sys
import tempfile
import time
from collections import Counter

sys.dont_write_bytecode = True
from adapters.olmsmoother import Adapter, ROOT
from core import command, load_corpus, raw_diff, sha

ENTRY = 0x180008060
DIRS = (5, 3, 1, 7)
TRACE = re.compile(r'\[cls8\] \(\d+,\d+\) dir=(\d+) scan_type=(-?\d+)')


def aex_classifier(loader, case, x, y):
    w, h = case['geometry']
    pixels = case['pixels']
    state = loader.host_alloc(64, align=16)
    loader.write_bytes(state, b'\0'*64)
    loader.write_bytes(state+8, struct.pack('<i', case['parameters'][2]['value']))
    neigh = []
    for yy in range(y-1, y+2):
        for xx in range(x-1, x+2):
            if 0 <= xx < w and 0 <= yy < h:
                pixel = loader.host_alloc(4, align=4)
                loader.write_bytes(pixel, pixels[(yy*w+xx)*4:(yy*w+xx+1)*4])
                neigh.append(pixel)
            else:
                neigh.append(0)
    table = loader.host_alloc(72, align=16)
    loader.write_bytes(table, struct.pack('<9Q', *neigh))
    result = {}
    for direction in DIRS:
        value = loader.call_function(ENTRY, [state, x, y, table, direction],
                                     max_instructions=100000)['rax']
        result[direction] = value-(1 << 64) if value >> 63 else value
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--jobs', type=int, choices=[1, 2], required=True,
                   help='One/two-job cap; the stateful Unicorn leaf probe runs serially')
    p.add_argument('--corpus', type=Path, action='append', required=True)
    p.add_argument('--owner-corpus', type=Path,
                   help='Also compare an existing direct original Classic harness to the worker and Mac')
    p.add_argument('--main', type=Path, default=ROOT.parent.parent)
    p.add_argument('--worker', type=Path,
                   default=Path.home()/'.cache/olm-emu/radial_frozen_reference_bd878da/'
                   'target/release/aex-guest-worker')
    p.add_argument('--scratch', type=Path,
                   default=ROOT/'orchestra/state/T11-triage-smoother/classifier8')
    p.add_argument('--report', type=Path, required=True)
    args = p.parse_args()
    args.max_size, args.case_timeout = 256, 10
    args.scratch = args.scratch.resolve()
    assert args.scratch.is_relative_to(ROOT/'orchestra/state')
    args.scratch.mkdir(parents=True, exist_ok=True)
    os.environ.update(TMPDIR=str(args.scratch), TMP=str(args.scratch), TEMP=str(args.scratch))
    tempfile.tempdir = str(args.scratch)
    sys.path.insert(0, str(ROOT/'tools/emulation'))
    from aex_loader import AexLoader

    adapter = Adapter(args)
    build = args.scratch/'build'
    build.mkdir(exist_ok=True)
    provenance = adapter.prepare(build, time.monotonic()+600)
    aex = args.main/'plugins_2025/OLMSmoother.aex'
    assert sha(aex.read_bytes()) == adapter.binding['aex_sha256']
    loader = AexLoader(str(aex), verbose=False, fast=True)
    from test_olmsmoother_v1_key_tolerance_geometry_actual_aex_20260810 import register_smoother_math
    register_smoother_math(loader)
    report = {'schema': 'olm-smoother-classifier8-compare/1', 'entry': hex(ENTRY),
              'directions': list(DIRS), 'aex_sha256': sha(aex.read_bytes()),
              'candidate_sha256': provenance['candidate_sha256'],
              'provenance': provenance, 'jobs': args.jobs,
              'script_sha256': sha(Path(__file__).read_bytes()),
              'mac_trace': '[cls8] emitted by ScanlinePixel8_Main',
              'cases': [], 'total_pixels': 0, 'total_mismatches': 0}
    for path in args.corpus:
        case, _ = load_corpus(path, adapter)
        w, h = case['geometry']
        outdir = args.scratch/path.stem
        outdir.mkdir(exist_ok=True)
        argv, data = adapter.candidate_command(case, outdir, 'classic')
        row = {'corpus': str(path.resolve().relative_to(ROOT)), 'geometry': [w, h],
               'input_sha256': sha(case['pixels']), 'pixels': w*h, 'mismatches': []}
        for y in range(h):
            for x in range(w):
                env = dict(adapter.env, OLMSMOOTHER_TRACE_X=str(x), OLMSMOOTHER_TRACE_Y=str(y))
                status, _, err = command(argv, data=data, timeout=adapter.timeout,
                                         deadline=time.monotonic()+60, env=env)
                assert status['status'] == 'ok', status
                mac = {int(d): int(v) for d, v in TRACE.findall(err.decode(errors='replace'))}
                aex_values = aex_classifier(loader, case, x, y)
                if mac != aex_values:
                    row['mismatches'].append({'x': x, 'y': y, 'mac': mac, 'aex': aex_values})
        row['matched'] = row['pixels']-len(row['mismatches'])
        report['total_pixels'] += row['pixels']
        report['total_mismatches'] += len(row['mismatches'])
        report['cases'].append(row)
        print(path.stem, row['matched'], '/', row['pixels'], flush=True)
    if args.owner_corpus:
        import test_olmsmoother_v1_key_tolerance_geometry_actual_aex_20260810 as owner
        owner.AEX = aex
        report['owner_helper_sha256'] = sha(Path(owner.__file__).read_bytes())
        report['owner_scope'] = (
            'Original PF_Cmd_RENDER through the retained Python host, with zero-initialized '
            'InData and hand-materialized parameter unions. Its existing serial guest iterate '
            'and copy/new-world providers are unchanged; ceilf/floorf now have explicit providers. This cross-host diagnostic does not '
            'replace the frozen worker or prove native AE behavior.')
        report['owner_cases'] = []
        code = owner.guest_code(build, 4)
        for path in sorted(args.owner_corpus.glob('*.json')):
            case, _ = load_corpus(path, adapter)
            assert case['depth'] == 8 and case['parameters'][0]['value'] == 0
            owner.W, owner.H = case['geometry']
            owner.KEY = tuple(case['parameters'][1]['value'][1:])
            direct, trace = owner.actual(8, case['pixels'], owner.W*4, 0,
                                         case['parameters'][2]['value'], code)
            with tempfile.TemporaryDirectory(dir=args.scratch) as td:
                directory = Path(td)
                oracle, reference = adapter.oracle(case, directory, time.monotonic()+60)
                status, mac, _ = adapter.candidate(case, directory, 'classic', time.monotonic()+60)
                assert oracle['status'] == status['status'] == 'ok'
            report['owner_cases'].append({
                'corpus': str(path.resolve().relative_to(ROOT)),
                'input_sha256': sha(case['pixels']),
                'direct_sha256': sha(direct), 'worker_sha256': sha(reference), 'mac_sha256': sha(mac),
                'direct_mac_equal': direct == mac, 'direct_worker_equal': direct == reference,
                'direct_mac_diff': raw_diff(direct, mac, 8),
                'direct_worker_diff': raw_diff(direct, reference, 8),
                'callback_counts': dict(Counter(trace))})
        print('OWNER', len(report['owner_cases']),
              'Mac equal', sum(c['direct_mac_equal'] for c in report['owner_cases']),
              'worker equal', sum(c['direct_worker_equal'] for c in report['owner_cases']), flush=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    print('REPORT', args.report, flush=True)
    assert report['total_mismatches'] == 0


if __name__ == '__main__':
    main()
