#!/usr/bin/env python3
"""T11 reproducible census analysis and scratch-only gate experiments (two jobs).

Production source only supplies refusal diagnostics. All gate probes below are
applied to a disposable source copy, never to a release build.
"""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import copy
import json
import math
import os
from pathlib import Path
import struct
import sys
import tempfile
import time

sys.dont_write_bytecode = True
from adapters.olmsmoother import Adapter, ROOT, SOURCE
from adapters.public import PublicAdapter, replace_once
from core import command, load_corpus, raw_diff, sha

TICKET = 'T11-triage-smoother'
WORKER = Path.home()/'.cache/olm-emu/radial_frozen_reference_bd878da/target/release/aex-guest-worker'
SANITIZERS = ('AddressSanitizer', 'runtime error:', 'UndefinedBehaviorSanitizer')


def scratch_source():
    body = SOURCE.read_text()
    body = replace_once(body, '#include "../../../core/olm_sha256_rows.h"',
                        f'#include "{ROOT}/core/olm_sha256_rows.h"')
    body = replace_once(body, '#include "../../../core/olm_world_safety.h"',
                        f'#include "{ROOT}/core/olm_world_safety.h"')
    world = ('\tif (input_depth == 32)\n'
             '\t\treturn OLM_SMOOTHER_REFUSAL("world-depth-32-unsupported");')
    body = replace_once(body, world,
        '#if !defined(OLM_SMOOTHER_TRIAGE_WORLD32_OFF)\n'+world+'\n#endif')
    admission = '\tif (depth == 8 || depth == 16) return true;'
    body = replace_once(body, admission,
        '#if defined(OLM_SMOOTHER_TRIAGE_ADMISSION32_OFF)\n'
        '\tif (depth == 8 || depth == 16 || depth == 32) return true;\n'
        '#else\n'+admission+'\n#endif')
    return body


class ProbeAdapter(Adapter):
    def __init__(self, options, mode, sanitizer=False):
        super().__init__(options)
        self.mode, self.sanitizer = mode, sanitizer
        self.commands = []
        self.env.update(ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',
                        UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')

    def compile(self, argv, deadline):
        argv = list(argv)
        if argv[0] == 'clang++':
            host = next(Path(x) for x in argv if str(x).endswith('/host.cpp'))
            patched = host.with_name('smoother-probe.cpp')
            patched.write_text(scratch_source())
            host.write_text(replace_once(host.read_text(), str(SOURCE), str(patched)))
            argv += ['-I', str(SOURCE.parent)]
            if self.mode in ('world', 'both'):
                argv += ['-DOLM_SMOOTHER_TRIAGE_WORLD32_OFF=1']
            if self.mode in ('admission', 'both'):
                argv += ['-DOLM_SMOOTHER_TRIAGE_ADMISSION32_OFF=1']
            if self.sanitizer:
                argv += ['-fsanitize=address,undefined', '-fno-sanitize-recover=all',
                         '-fno-omit-frame-pointer', '-g']
        self.commands.append(list(map(str, argv)))
        return super().compile(argv, deadline)

    def scope(self):
        return dict(super().scope(),
                    triage_switch=f'mode={self.mode}, sanitizer={self.sanitizer} (scratch source only)')


def outcome(adapter, case, directory, route, deadline):
    result, raw, guards = adapter.candidate(case, directory, route, deadline)
    return dict(result, guards=guards, raw_sha256=sha(raw)), raw


def sanitizer_error(result):
    diagnostic = result.get('diagnostic') or ''
    return any(marker in diagnostic for marker in SANITIZERS)


def diff_stats(expected, actual, case):
    result = raw_diff(expected, actual, case['depth'])
    unit = case['depth']//8
    fmt = {8:'B', 16:'H', 32:'f'}[case['depth']]
    words = [i//unit for i in range(0, len(expected), unit) if expected[i:i+unit] != actual[i:i+unit]]
    pixels = sorted(set(i//4 for i in words))
    w, h = case['geometry']
    finite_diffs, nonfinite = [], 0
    for i in words:
        a, b = (struct.unpack_from('<'+fmt, raw, i*unit)[0] for raw in (expected, actual))
        if math.isfinite(a) and math.isfinite(b):
            finite_diffs.append(abs(a-b))
        else:
            nonfinite += 1
    source = case['pixels']
    pixel_size = 4*unit
    aex_equals_input = [p for p in pixels if expected[p*pixel_size:(p+1)*pixel_size] == source[p*pixel_size:(p+1)*pixel_size]]
    mac_equals_input = [p for p in pixels if actual[p*pixel_size:(p+1)*pixel_size] == source[p*pixel_size:(p+1)*pixel_size]]
    result.update(max_abs_byte_diff=max((abs(a-b) for a,b in zip(expected,actual)), default=0),
        max_abs_finite_sample_diff=max(finite_diffs, default=0), nonfinite_different_words=nonfinite,
        channels=dict(Counter('ARGB'[i%4] for i in words)), different_pixels=len(pixels),
        bbox_xyxy=[min(p%w for p in pixels),min(p//w for p in pixels),
                   max(p%w for p in pixels),max(p//w for p in pixels)] if pixels else None,
        pixels_per_row=dict(sorted(Counter(p//w for p in pixels).items())),
        first_pixel_xy=[words[0]//4%w, words[0]//4//w] if words else None,
        first_channel='ARGB'[words[0]%4] if words else None,
        spatial_pattern='all pixels' if len(pixels)==w*h else 'subset of pixels',
        equals_input=actual==source,
        aex_equals_input_pixels=len(aex_equals_input),
        mac_equals_input_pixels=len(mac_equals_input),
        neither_equals_input_pixels=len(pixels)-len(aex_equals_input)-len(mac_equals_input))
    return result


def dispatch_trace(adapter, case, directory, route, deadline, x, y):
    argv, data = adapter.candidate_command(case, directory, route)
    env = dict(adapter.env, OLMSMOOTHER_TRACE_X=str(x), OLMSMOOTHER_TRACE_Y=str(y))
    status, out, err = command(argv, data=data, timeout=adapter.timeout,
                               deadline=deadline, env=env)
    lines = [line for line in err.decode(errors='replace').splitlines()
             if line.startswith(('[cls', '[disp'))]
    exact = [line for line in lines
             if f'center=({x},{y}) ' in line or line.startswith(f'[cls8] ({x},{y}) ')]
    return {'status': status, 'exact_pixel_lines': exact[:8],
            'nearby_lines': lines[:12], 'line_count': len(lines)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--jobs', type=int, choices=[2], required=True)
    p.add_argument('--worker', type=Path, default=WORKER)
    p.add_argument('--main', type=Path, default=ROOT.parent.parent)
    p.add_argument('--scratch', type=Path, default=ROOT/'orchestra/state'/TICKET)
    p.add_argument('--census', type=Path, required=True)
    p.add_argument('--baseline', type=Path, default=ROOT/'reports/fuzz/olmsmoother_20261021.json')
    p.add_argument('--corpus', type=Path, default=ROOT/'tests/fuzz_corpus/olmsmoother')
    p.add_argument('--report', type=Path, required=True)
    args = p.parse_args()
    args.max_size, args.case_timeout = 256, 10
    args.scratch = args.scratch.resolve()
    assert args.scratch.is_relative_to(ROOT/'orchestra/state'/TICKET)
    args.scratch.mkdir(parents=True, exist_ok=True)
    assert sum(x.stat().st_size for x in args.scratch.rglob('*') if x.is_file()) < 4*1024**3
    os.environ.update(TMPDIR=str(args.scratch), TMP=str(args.scratch), TEMP=str(args.scratch))
    tempfile.tempdir = str(args.scratch)
    deadline = time.monotonic()+1800
    census = json.loads(args.census.read_text())
    baseline = json.loads(args.baseline.read_text())
    report = {'schema':'olm-smoother-triage/1', 'jobs':args.jobs,
              'census_sha256':sha(args.census.read_bytes()),
              'baseline_sha256':sha(args.baseline.read_bytes()),
              'probe_source_sha256':sha(scratch_source().encode()),
              'script_sha256':sha(Path(__file__).read_bytes()),
              'census_summary':census['summary'], 'baseline_summary':baseline['summary'],
              'guards':[], 'neutrality':[], 'unwritable_trace':[], 'clusters':[],
              'mismatch_census':[], 'gate_runs':[], 'gate_summary':{}}
    by_index = {row['index']: row for row in census['cases']}
    declarations = json.loads((ROOT/'tools/fuzz/declarations/olmsmoother.json').read_text())
    bounds = {p['slot']: p for p in declarations['parameters']}
    violations = []
    for row in census['cases']:
        for param in row['parameters']:
            value = param['value']
            if param['kind'] == 'c':
                valid = len(value) == 4 and all(isinstance(v, int) and 0 <= v <= 255 for v in value)
            else:
                decl = bounds[param['slot']]
                valid = isinstance(value, int) and decl['valid_min'] <= value <= decl['valid_max']
            if not valid:
                violations.append({'index': row['index'], 'parameter': param})
    report['parameter_range_violations'] = violations
    report['oracle_status_by_depth'] = dict(Counter(
        f"{r['depth']}/{r['result']['oracle']['status']}" for r in census['cases']))
    report['oracle_rejection_reasons'] = dict(Counter(
        r['result']['oracle'].get('diagnostic', '') for r in census['cases']
        if r['result']['oracle']['status'] == 'reject'))
    assert not violations

    guards = {}
    refused_indices = []
    for row in census['cases']:
        for route, result in row['result']['routes'].items():
            if result['status'] != 'refusal':
                continue
            refused_indices.append(row['index'])
            names = row.get('refusal_guards', {}).get(route) or ['UNATTRIBUTED']
            for name in names:
                name = name.split('@')[0]
                g = guards.setdefault(name, {'guard':name, 'routes':Counter(),
                    'indices':set(), 'aex_ok_indices':set(), 'errors':Counter()})
                g['routes'][route] += 1
                g['indices'].add(row['index'])
                g['errors'][result['error']] += 1
                if row['result']['oracle']['status'] == 'ok':
                    g['aex_ok_indices'].add(row['index'])
    for g in sorted(guards.values(), key=lambda g: -sum(g['routes'].values())):
        g['indices'] = sorted(g['indices'])
        g['aex_ok_indices'] = sorted(g['aex_ok_indices'])
        report['guards'].append(g)
    refused_indices = sorted(set(refused_indices))
    report['refused_indices'] = refused_indices
    report['refused_depths'] = dict(Counter(by_index[i]['depth'] for i in refused_indices))
    report['refused_errors'] = dict(Counter(
        result['error'] for i in refused_indices for result in by_index[i]['result']['routes'].values()
        if result['status'] == 'refusal'))

    with tempfile.TemporaryDirectory(prefix='triage_', dir=args.scratch) as td:
        scratch = Path(td)
        builds = {}
        configurations = [('production', False), ('production', True),
                          ('world', False), ('world', True),
                          ('admission', False), ('admission', True),
                          ('both', False), ('both', True)]
        for mode, san in configurations:
            key = mode + ('-san' if san else '')
            directory = scratch/key
            directory.mkdir()
            adapter = Adapter(args) if mode == 'production' and not san else ProbeAdapter(args, mode, san)
            provenance = adapter.prepare(directory, deadline)
            builds[key] = adapter
            report.setdefault('builds', {})[key] = {
                'provenance': provenance, 'commands': getattr(adapter, 'commands', [])}
            print('BUILT', key, flush=True)
        plain = builds['production']
        traced = builds['production']

        def neutrality(row):
            case = plain.generate(census['seed'], row['index'])
            assert sha(case['pixels']) == row['input_sha256']
            with tempfile.TemporaryDirectory(dir=scratch) as local:
                d = Path(local)
                values = {}
                for route in plain.routes:
                    traced_result, traced_raw, _ = traced.candidate(case, d, route, deadline)
                    plain_result, plain_raw = PublicAdapter.candidate(plain, case, d, route, deadline)
                    values[route] = traced_result == plain_result and traced_raw == plain_raw
                return {'index': row['index'], 'routes': values}
        with ThreadPoolExecutor(max_workers=args.jobs) as pool:
            report['neutrality'] = list(pool.map(neutrality, census['cases']))
        assert all(all(x['routes'].values()) for x in report['neutrality'])
        print('NEUTRALITY', len(report['neutrality']), flush=True)

        broken = copy.copy(traced)
        broken.env = dict(traced.env, OLM_REFUSAL_TRACE=str(scratch/'missing-parent'/'trace'))
        for index in (0, 4, 6, 32, 300):
            case = plain.generate(census['seed'], index)
            with tempfile.TemporaryDirectory(dir=scratch) as local:
                d = Path(local)
                for route in plain.routes:
                    normal, normal_raw = PublicAdapter.candidate(plain, case, d, route, deadline)
                    failed, failed_raw = PublicAdapter.candidate(broken, case, d, route, deadline)
                    same = normal == failed and normal_raw == failed_raw
                    assert same
                    report['unwritable_trace'].append({'index': index, 'route': route, 'same': same})

        representative_cases = {}
        for number, (signature, cluster) in enumerate(baseline['clusters'].items(), 1):
            candidates = [(load_corpus(ROOT/path, plain)[0], path) for path in cluster['corpus']]
            def size(item):
                case, path = item
                defaults = plain.defaults(*case['geometry'])
                return (len(case['pixels']),
                        sum(p['value'] != d['value'] for p, d in zip(case['parameters'], defaults)),
                        path)
            case, path = min(candidates, key=size)
            representative_cases[number] = case
            with tempfile.TemporaryDirectory(dir=scratch) as local:
                d = Path(local)
                oracle, reference = plain.oracle(case, d, deadline)
                assert oracle['status'] == 'ok', oracle
                row = {'cluster':number, 'signature':signature, 'population':cluster['count'],
                       'corpus':path, 'case':{k:v for k,v in case.items() if k != 'pixels'},
                       'input_sha256':sha(case['pixels']),
                       'oracle':dict(oracle, raw_sha256=sha(reference)), 'routes':{},
                       'first_differing_stage':None,
                       'stage_reason':'No paired AEX interior trace exists for these public-session inputs; '
                                      'the Mac dispatch label is unpaired and not a numerical stage.'}
                for route in plain.routes:
                    status, raw = outcome(plain, case, d, route, deadline)
                    assert status['status'] == 'ok', status
                    assert raw != reference, 'Saved mismatch no longer reproduces'
                    stats = diff_stats(reference, raw, case)
                    packed = copy.deepcopy(case)
                    packed['input_padding'] = packed['output_padding'] = 0
                    packed_status, packed_raw = outcome(plain, packed, d, route, deadline)
                    san_status, san_raw = outcome(builds['production-san'], case, d, route, deadline)
                    san_ok = san_status['status'] == 'ok'
                    x, y = stats['first_pixel_xy']
                    dispatch = dispatch_trace(plain, case, d, route, deadline, x, y)
                    row['routes'][route] = {
                        'status':status, 'diff':stats,
                        'packed_same':packed_status['status']=='ok' and packed_raw==raw,
                        'sanitizer':dict(san_status,
                            diagnostic=(san_status.get('diagnostic') or '')[:1200]),
                        'sanitizer_same':san_ok and san_raw==raw if san_ok else None,
                        'sanitizer_error':sanitizer_error(san_status),
                        'dispatch_trace':dispatch}
                row['classification'] = 'unexplained'
                row['classification_basis'] = (
                    'Final-byte differences alone do not distinguish a port bug from a host/oracle '
                    'difference. See the separate paired classifier/owner experiment; an equal '
                    'classifier result cannot establish downstream dispatch equivalence.')
                report['clusters'].append(row)
            print('CLUSTER', number, case['index'], row['classification'], flush=True)

        # Summarize every retained mismatch, not only the two representatives.
        for path in sorted(args.corpus.glob('*.json')):
            case, saved = load_corpus(path, plain)
            assert case['depth'] == 8, 'This retained mismatch census is PF8 only'
            row = {'corpus':str(path.relative_to(ROOT)), 'input_sha256':sha(case['pixels']),
                   'depth':case['depth'], 'geometry':case['geometry'],
                   'nondefault_slots':[p['slot'] for p, d in zip(
                       case['parameters'], plain.defaults(*case['geometry'])) if p['value'] != d['value']],
                   'routes':{}}
            with tempfile.TemporaryDirectory(dir=scratch) as local:
                d = Path(local)
                oracle, reference = plain.oracle(case, d, deadline)
                assert oracle['status'] == 'ok', oracle
                for route in plain.routes:
                    result, raw, _ = plain.candidate(case, d, route, deadline)
                    diffs = [i for i in range(len(reference)) if reference[i] != raw[i]]
                    pixels = sorted(set(i//4 for i in diffs))
                    source = case['pixels']
                    aex_eq = sum(1 for p in pixels if reference[p*4:p*4+4] == source[p*4:p*4+4])
                    mac_eq = sum(1 for p in pixels if raw[p*4:p*4+4] == source[p*4:p*4+4])
                    row['routes'][route] = {
                        'status':result['status'], 'different_bytes':len(diffs),
                        'different_pixels':len(pixels),
                        'aex_equals_input_pixels':aex_eq,
                        'mac_equals_input_pixels':mac_eq,
                        'neither_equals_input_pixels':len(pixels)-aex_eq-mac_eq,
                        'first_pixel_xy':[pixels[0]%case['geometry'][0],
                                          pixels[0]//case['geometry'][0]] if pixels else None}
            report['mismatch_census'].append(row)
        print('MISMATCH_CENSUS', len(report['mismatch_census']), flush=True)

        selected = [by_index[index] for index in refused_indices]

        def gate_run(row):
            case = plain.generate(census['seed'], row['index'])
            assert sha(case['pixels']) == row['input_sha256']
            oracle = row['result']['oracle']
            result = {'index':row['index'], 'depth':case['depth'], 'geometry':case['geometry'],
                      'profile':case['profile'], 'original_guards':row.get('refusal_guards'),
                      'oracle_status':oracle['status'], 'routes':{}}
            with tempfile.TemporaryDirectory(dir=scratch) as local:
                d = Path(local)
                for route in plain.routes:
                    result['routes'][route] = {}
                    for key in ('world', 'world-san', 'admission', 'admission-san',
                                'both', 'both-san'):
                        status, raw, guards = builds[key].candidate(case, d, route, deadline)
                        if status['status'] == 'ok':
                            label = ('exact' if sha(raw) == oracle['raw_sha256'] else 'mismatch') if oracle['status']=='ok' else 'uncompared'
                        elif sanitizer_error(status):
                            label = 'sanitizer_error'
                        elif status.get('returncode', 0) < 0:
                            label = 'crash'
                        else:
                            label = status['status']
                        result['routes'][route][key] = {
                            'status':status['status'], 'error':status.get('error'),
                            'guards':guards, 'classification':label,
                            'returncode':status.get('returncode'),
                            'diagnostic':(status.get('diagnostic') or '')[:1200]}
            return result
        with ThreadPoolExecutor(max_workers=args.jobs) as pool:
            report['gate_runs'] = list(pool.map(gate_run, selected))
        for row in report['gate_runs']:
            for route, modes in row['routes'].items():
                for mode, value in modes.items():
                    counts = report['gate_summary'].setdefault(mode+'/'+route, Counter())
                    counts[value['classification']] += 1
        print('GATES', {k:dict(v) for k,v in report['gate_summary'].items()}, flush=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, sort_keys=True, indent=2)+'\n')
    print('REPORT', args.report, flush=True)


if __name__ == '__main__':
    main()
