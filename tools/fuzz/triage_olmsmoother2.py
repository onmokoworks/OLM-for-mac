#!/usr/bin/env python3
"""T08: scratch-only gate-off experiment and retained-cluster raw-byte census.

No production gate switch is added. The generated translation unit contains an
explicit compile-time switch and includes the worktree's unchanged headers.
All cases are baseline seed/index inputs or retained, hash-checked shrunk inputs.

The baseline oracle is the original AEX Smart path. The original AEX Classic
path is also run as a diagnostic owner so a classic gate-off result is not
mistaken for a cross-route comparison.
"""
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
from adapters.olmsmoother2 import Adapter, HARNESS, SHIM, SOURCE
from adapters.public import ROOT, replace_once
from core import load_corpus, raw_diff, sha

SCRATCH = ROOT/'orchestra/state/T08-triage-smoother2'
BASELINE = ROOT/'reports/fuzz/olmsmoother2_20261021.json'
CLASSIC_PROD = '	(void)depth;\n	return OLM_SM2_REFUSAL("classic-entry-unowned");'
CLASSIC_GATE_OFF = '''	(void)depth;
#if OLM_SM2_TRIAGE_CLASSIC_OFF
	if (depth == 8) return RenderBits<PF_Pixel8>(in_data, params, input, output);
	if (depth == 16) return RenderBits<PF_Pixel16>(in_data, params, input, output);
	return RenderBits<PF_PixelFloat>(in_data, params, input, output);
#else
	return OLM_SM2_REFUSAL("classic-entry-unowned");
#endif'''


def byte_stats(expected, actual, case):
    result = raw_diff(expected, actual, case['depth'])
    unit = case['depth']//8
    words = [i//unit for i in range(0, len(expected), unit)
             if expected[i:i+unit] != actual[i:i+unit]]
    pixels = sorted({i//4 for i in words})
    w, h = case['geometry']
    result.update(max_abs_byte_diff=max((abs(a-b) for a, b in zip(expected, actual)), default=0),
                  channels=dict(Counter('ARGB'[i % 4] for i in words)),
                  different_pixels=len(pixels), total_pixels=w*h,
                  bbox=[min(p % w for p in pixels), min(p//w for p in pixels),
                        max(p % w for p in pixels), max(p//w for p in pixels)] if pixels else None,
                  first_xy_channel=[result['first_word']//4 % w, result['first_word']//4//w,
                                    'ARGB'[result['first_word'] % 4]])
    fmt = {8: 'B', 16: 'H', 32: 'f'}[case['depth']]
    pairs = list(zip(struct.unpack('<'+fmt*(len(expected)//unit), expected),
                     struct.unpack('<'+fmt*(len(actual)//unit), actual)))
    result['max_abs_finite_sample_diff'] = max(
        (abs(a-b) for a, b in pairs if math.isfinite(a) and math.isfinite(b)), default=None)
    result['nonfinite_sample_pairs'] = sum(not (math.isfinite(a) and math.isfinite(b)) for a, b in pairs)
    return result


def candidate_outcome(adapter, case, directory, route, deadline):
    status, raw, guards = adapter.candidate(case, directory, route, deadline)
    result = dict(status, guards=guards)
    if status['status'] == 'ok':
        result['raw_sha256'] = sha(raw)
    elif status['status'] == 'error':
        diagnostic = status.get('diagnostic', '')
        result['status'] = ('sanitizer_error' if 'runtime error:' in diagnostic or 'Sanitizer' in diagnostic
                            else 'crash' if status.get('returncode', 0) < 0 else 'harness_error')
    return result, raw


def compare(result, raw, case, oracle, reference):
    if result['status'] != 'ok':
        return result
    if oracle['status'] != 'ok':
        result['status'] = 'uncompared'
    elif raw == reference:
        result['status'] = 'exact'
    else:
        result['status'] = 'mismatch'
        result['diff'] = byte_stats(reference, raw, case)
    return result


def build_variant(base, directory, name, flags, deadline):
    directory.mkdir()
    source = SOURCE.read_text()
    source = replace_once(source, '#include "../../../core/olm_sha256_rows.h"',
                          '#include "'+str(ROOT/'core/olm_sha256_rows.h')+'"')
    source = replace_once(source, CLASSIC_PROD, CLASSIC_GATE_OFF)
    (directory/'production_under_test.cpp').write_text(source)

    body = HARNESS.read_text()
    body = replace_once(body, 'static PF_EffectWorld *source_world, *destination_world;',
                        'static bool fuzz_classic; static size_t fuzz_pad;\nstatic PF_EffectWorld *source_world, *destination_world;')
    body = replace_once(body, 'const size_t pad = sizeof(Pixel) == 4 ? 5 : (sizeof(Pixel) == 8 ? 7 : 13);',
                        'const size_t pad = fuzz_pad;')
    body = replace_once(body, '    PF_PreRenderInput pre_input{};', '''    int error;
    if (fuzz_classic) {
        definitions[0].u.ld=iw;
        PF_ParamDef *params[SM_NUM_PARAMS];
        for(int i=0;i<SM_NUM_PARAMS;++i) params[i]=definitions+i;
        error=EffectMain(PF_Cmd_RENDER,&in,&out,params,&ow,nullptr);
    } else {
    PF_PreRenderInput pre_input{};''')
    body = replace_once(body, '    int error = pre_error ? pre_error : EffectMain(PF_Cmd_SMART_RENDER, &in, &out, nullptr, nullptr, &smart);',
                        '    error = pre_error ? pre_error : EffectMain(PF_Cmd_SMART_RENDER, &in, &out, nullptr, nullptr, &smart);\n    }')
    for old, new in [('argc != 5', 'argc != 7'), ('w > 32 || h > 32', 'w > 256 || h > 256'),
                     ('int w = atoi(argv[1]), h = atoi(argv[2]);',
                      'int w = atoi(argv[1]), h = atoi(argv[2]); fuzz_classic=!strcmp(argv[5],"classic"); fuzz_pad=atoi(argv[6]);')]:
        body = replace_once(body, old, new)
    host = directory/'host.cpp'
    host.write_text(body)
    variant = copy.copy(base)
    variant.binary = directory/'mac'
    variant.env = dict(base.env)
    variant.compile(['clang++', '-std=c++17', '-O2', '-fno-fast-math', '-ffp-contract=off',
                     '-Wno-deprecated-declarations', *flags, '-I', directory, '-I', SHIM,
                     '-I', SOURCE.parent, host, '-o', variant.binary], deadline)
    variant.env.update(ASAN_OPTIONS='detect_leaks=0',
                       UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
    return variant, {'candidate_sha256': sha(variant.binary.read_bytes()),
                     'source_sha256': sha(source.encode()),
                     'flags': flags}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--jobs', type=int, choices=[2], required=True)
    parser.add_argument('--report', type=Path, default=SCRATCH/'triage.json')
    args = parser.parse_args()
    if not args.report.resolve().is_relative_to(ROOT):
        parser.error('report must be in worktree')
    SCRATCH.mkdir(parents=True, exist_ok=True)
    os.environ.update(TMPDIR=str(SCRATCH), TMP=str(SCRATCH), TEMP=str(SCRATCH))
    baseline = json.loads(BASELINE.read_text())
    opts = argparse.Namespace(max_size=256, case_timeout=10, main=ROOT.parent.parent,
                              worker=Path(baseline['provenance']['worker_path']))
    adapter = Adapter(opts)
    deadline = time.monotonic()+1800
    report = {'schema': 'olm.smoother2-triage/1', 'jobs': args.jobs,
              'baseline_sha256': sha(BASELINE.read_bytes()),
              'paired_stage_support': False, 'variants': {}, 'cases': [], 'clusters': []}
    with tempfile.TemporaryDirectory(prefix='experiment_', dir=SCRATCH) as td:
        directory = Path(td)
        prod = directory/'production'
        prod.mkdir()
        report['provenance'] = adapter.prepare(prod, deadline)
        assert report['provenance']['worker_sha256'] == baseline['provenance']['worker_sha256']
        variants = {'production': adapter}
        for name, flags in {
            'classic_gate_off': ['-DOLM_SM2_TRIAGE_CLASSIC_OFF=1'],
            'classic_gate_off_sanitized': ['-DOLM_SM2_TRIAGE_CLASSIC_OFF=1',
                                           '-fsanitize=address,undefined', '-fno-sanitize-recover=all'],
        }.items():
            variants[name], report['variants'][name] = build_variant(
                adapter, directory/name, name, flags, deadline)
        classic_oracle = copy.copy(adapter)
        classic_oracle.oracle_route = 'classic'
        classic_oracle.oracle_path = 'classic'
        print('BUILT', flush=True)

        def run(row):
            case = adapter.generate(row['seed'], row['index'])
            assert sha(case['pixels']) == row['input_sha256']
            with tempfile.TemporaryDirectory(prefix='case_', dir=directory) as wd:
                work = Path(wd)
                oracle, reference = adapter.oracle(case, work, deadline)
                aex_classic, aex_classic_raw = classic_oracle.oracle(case, work, deadline)
                result = {'index': row['index'], 'depth': case['depth'],
                          'profile': case['profile'], 'oracle': oracle,
                          'aex_classic': aex_classic, 'variants': {}}

                mac_classic, mac_classic_raw = candidate_outcome(adapter, case, work, 'classic', deadline)
                result['variants']['classic_production'] = compare(
                    mac_classic, mac_classic_raw, case, oracle, reference)

                mac_smart, mac_smart_raw = candidate_outcome(adapter, case, work, 'smart', deadline)
                result['variants']['smart_production'] = compare(
                    mac_smart, mac_smart_raw, case, oracle, reference)

                for name in ('classic_gate_off', 'classic_gate_off_sanitized'):
                    outcome, raw = candidate_outcome(variants[name], case, work, 'classic', deadline)
                    result['variants'][name+'_vs_smart'] = compare(
                        dict(outcome), raw, case, oracle, reference)
                    result['variants'][name+'_vs_classic'] = compare(
                        dict(outcome), raw, case, aex_classic, aex_classic_raw)
                    if outcome['status'] == 'ok':
                        result['variants'][name+'_same_as_mac_smart'] = raw == mac_smart_raw
                if aex_classic['status'] == 'ok':
                    result['aex_classic_equals_input'] = aex_classic_raw == case['pixels']
                    result['aex_classic_equals_smart'] = aex_classic_raw == reference
                    result['aex_classic_all_zero'] = not any(aex_classic_raw)
                    result['aex_classic_nonzero_bytes'] = sum(x != 0 for x in aex_classic_raw)
                return result

        with ThreadPoolExecutor(max_workers=args.jobs) as pool:
            for i, result in enumerate(pool.map(run, baseline['cases'])):
                report['cases'].append(result)
                if (i+1) % 25 == 0:
                    print('CASES', i+1, flush=True)
        report['summary'] = {
            name: dict(Counter(r['variants'][name]['status'] for r in report['cases']))
            for name in ('classic_production', 'smart_production',
                         'classic_gate_off_vs_smart', 'classic_gate_off_vs_classic',
                         'classic_gate_off_sanitized_vs_smart',
                         'classic_gate_off_sanitized_vs_classic')}
        report['aex_classic_status'] = dict(Counter(
            r['aex_classic']['status'] for r in report['cases']))
        report['aex_classic_equals_input'] = sum(
            1 for r in report['cases'] if r.get('aex_classic_equals_input'))
        report['aex_classic_equals_smart'] = sum(
            1 for r in report['cases'] if r.get('aex_classic_equals_smart'))
        report['aex_classic_all_zero'] = sum(
            1 for r in report['cases'] if r.get('aex_classic_all_zero'))
        report['same_as_mac_smart'] = sum(
            1 for r in report['cases'] if r['variants'].get('classic_gate_off_same_as_mac_smart'))
        report['guard_ranking'] = dict(Counter(
            g.split('@')[0] for r in report['cases']
            for g in r['variants']['classic_production'].get('guards', [])))
        report['guard_ranking_by_route'] = {
            route: dict(Counter(
                g.split('@')[0] for r in report['cases']
                for g in (r['variants'].get(route+'_production', {}).get('guards') or [])))
            for route in ('classic', 'smart')}

        # Smallest retained by pixel count, then active bytes, then corpus path.
        # These are bounded greedy shrinks, not globally minimal witnesses.
        for cluster, group in sorted(baseline['clusters'].items()):
            loaded = [(ROOT/p, *load_corpus(ROOT/p, adapter)) for p in group['corpus']]
            path, case, saved = min(loaded, key=lambda x: (
                math.prod(x[1]['geometry']), len(x[1]['pixels']), str(x[0])))
            with tempfile.TemporaryDirectory(prefix='cluster_', dir=directory) as wd:
                work = Path(wd)
                oracle, reference = adapter.oracle(case, work, deadline)
                aex_classic, aex_classic_raw = classic_oracle.oracle(case, work, deadline)
                smart, smart_raw = candidate_outcome(adapter, case, work, 'smart', deadline)
                smart = compare(smart, smart_raw, case, oracle, reference)
                gate, gate_raw = candidate_outcome(variants['classic_gate_off'], case, work, 'classic', deadline)
                gate_smart = compare(dict(gate), gate_raw, case, oracle, reference)
                gate_classic = compare(gate, gate_raw, case, aex_classic, aex_classic_raw)
                prod_classic, prod_classic_raw = candidate_outcome(adapter, case, work, 'classic', deadline)
                defaults = {p['slot']: p['value'] for p in adapter.defaults(*case['geometry'])}
                nondefault = [p['slot'] for p in case['parameters'] if p['value'] != defaults[p['slot']]]
                report['clusters'].append(dict(
                    cluster=cluster, count=group['count'], corpus=str(path.relative_to(ROOT)),
                    geometry=case['geometry'], depth=case['depth'], profile=case['profile'],
                    input_sha256=sha(case['pixels']), parameters=case['parameters'],
                    nondefault_slots=nondefault,
                    oracle=oracle, aex_classic=aex_classic,
                    aex_classic_sha256=sha(aex_classic_raw) if aex_classic['status'] == 'ok' else None,
                    aex_classic_all_zero=(aex_classic['status'] == 'ok' and not any(aex_classic_raw)),
                    smart=smart, classic_production=compare(
                        prod_classic, prod_classic_raw, case, oracle, reference),
                    classic_gate_off_vs_classic=gate_classic,
                    classic_gate_off_vs_smart=gate_smart))

        report['script_sha256'] = sha(Path(__file__).read_bytes())
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
        print('RESULT', json.dumps(report['summary'], sort_keys=True), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
