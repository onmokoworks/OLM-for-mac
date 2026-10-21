#!/usr/bin/env python3
"""Reproduce F10's bounded zero-ray admission evidence; never update a corpus.

The campaign directory contains before/after production and gate-off reports
for seeds 1 and 2 from run.py / triage_kirakira.py. This script independently
checks their admission sets, replays production with ASan/UBSan, audits both
committed corpora at both revisions, and runs a separate AEX parameter matrix.
Use the emulation venv: the final paired traces require Unicorn.
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
import tempfile
import time
from types import SimpleNamespace

sys.dont_write_bytecode = True
from trace_kirakira_numeric_F09 import (
    ROOT, build_mac, default_worker, load_corpus, main_checkout, olmkirakira,
    original_trace, raw_diff, sha)


def promoted(case):
    p = {v['slot']: v['value'] for v in case['parameters']}
    w, h = case['geometry']
    # The campaign's SDR profile is generated entirely inside [0,1].
    return (w >= 9 and h >= 7 and w <= 4096 and h <= 4096
            and w*h <= 4096*2160 and case['profile'] == 'sdr'
            and not p[4] and p[9] == 100 and 0 <= p[8] <= 10000
            and 1 <= p[1] <= 6 and 1 <= p[2] <= 3 and p[3] in (1, 2)
            and all(p[s] == 0 for s in (10, 16, 22, 28, 34)))


def adapter_class(source, gate_off=False, sanitizers=True):
    class SourceAdapter(olmkirakira.Adapter):
        def compile(self, argv, deadline):
            argv = list(argv)
            if argv[0] == 'clang++':
                host = next(Path(x) for x in argv if str(x).endswith('/host.cpp'))
                body = source.read_text()
                if gate_off:
                    assert body.count('if (!exact_closure && !generic_beta) {') == 2
                    body = body.replace('if (!exact_closure && !generic_beta) {', 'if (false) {')
                body = body.replace('#include "OLMKiraKira.h"',
                                    '#include "'+str(olmkirakira.SOURCE.with_suffix('.h'))+'"')
                body = body.replace('#include "../../core/', '#include "'+str(ROOT/'core')+'/')
                generated = host.parent/'candidate.cpp'
                generated.write_text(body)
                host.write_text(host.read_text().replace(str(olmkirakira.SOURCE), str(generated)))
                if sanitizers:
                    argv[1:1] = ['-fsanitize=address,undefined', '-fno-sanitize-recover=all',
                                 '-fno-omit-frame-pointer', '-g']
                    self.env.update(ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',
                                    UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
            return super().compile(argv, deadline)

        def prepare(self, scratch, deadline):
            provenance = super().prepare(scratch, deadline)
            source_hash = sha(source.read_bytes())
            provenance['dependencies_sha256']['mac/OLMKiraKira/OLMKiraKira.cpp'] = source_hash
            provenance['F10_source_override'] = dict(path=str(source), sha256=source_hash,
                                                   gate_off=gate_off, sanitizers=sanitizers)
            return provenance
    return SourceAdapter


def build(source, scratch, options, deadline, gate_off=False):
    scratch.mkdir()
    adapter = adapter_class(source, gate_off)(options)
    adapter.binary, _ = adapter.build(scratch, deadline)
    return adapter


def observation(adapter, case, directory, route, deadline, reference):
    result, raw, *_ = adapter.candidate(case, directory, route, deadline)
    assert result['status'] in ('ok', 'refusal'), result
    if result['status'] == 'ok':
        result = dict(result, status='exact' if raw == reference else 'mismatch',
                      raw_sha256=sha(raw))
        if raw != reference:
            result['diff'] = raw_diff(reference, raw, case['depth'])
    return result, raw


def matrix_case(adapter, index, geometry, depth, merge, mode, channel):
    rng = random.Random(1010000 + index)
    params = adapter.defaults(*geometry)
    values = {1: channel, 2: mode, 3: merge, 4: 0, 5: rng.choice([1., 17.25, 100.]),
              6: rng.choice([0, 1, 100, 537, 1000]), 7: rng.random(),
              8: rng.choice([0, 1, 100, 1703, 10000]), 9: 100,
              40: rng.randrange(-360, 361)/65536}
    values.update({s: 0 for s in (10, 16, 22, 28, 34)})
    values.update({s: rng.randrange(2) for s in (13, 19, 25, 31, 37)})
    for p in params:
        if p['kind'] == 'c':
            p['value'] = [rng.randrange(256) for _ in range(4)]
        elif p['slot'] in values:
            p['value'] = values[p['slot']]
    pixels = bytearray()
    for _ in range(geometry[0]*geometry[1]*4):
        if depth == 8:
            pixels.extend(struct.pack('<B', rng.randrange(256)))
        elif depth == 16:
            pixels.extend(struct.pack('<H', rng.choice([0, 1, 32768, rng.randrange(32769)])))
        else:
            edges = [0, 0x80000000, 1, 0x00800000, 0x3f000000, 0x3f7fffff, 0x3f800000]
            pixels.extend(struct.pack('<I', rng.choice(edges)) if rng.random() < .5
                          else struct.pack('<f', rng.random()))
    return dict(seed=1010, index=index, geometry=list(geometry), depth=depth, profile='sdr',
                parameters=params, pixels=bytes(pixels), input_padding=3, output_padding=5)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--before-source', type=Path, required=True)
    p.add_argument('--campaign-dir', type=Path, required=True)
    p.add_argument('--scratch', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    args = p.parse_args()
    scratch = args.scratch.resolve()
    assert scratch.is_relative_to(ROOT/'orchestra/state')
    scratch.mkdir(parents=True, exist_ok=True)
    os.environ.update(TMPDIR=str(scratch), TMP=str(scratch), TEMP=str(scratch),
                      OLM_KK_PROCESS_ATTACH_DIAGNOSTIC='1',
                      OLM_KK_MANUAL_CRT_INITIALIZERS_DIAGNOSTIC='1')
    tempfile.tempdir = str(scratch)
    deadline = time.monotonic()+3600
    options = SimpleNamespace(max_size=256, case_timeout=60,
                              main=main_checkout(), worker=default_worker())
    report = dict(schema='olm-kira-admission-F10/1', status='running',
                  before_source_sha256=sha(args.before_source.read_bytes()),
                  after_source_sha256=sha(olmkirakira.SOURCE.read_bytes()),
                  worker_sha256=sha(options.worker.read_bytes()),
                  aex_sha256=sha((options.main/'plugins_2025/OLMKiraKira.aex').read_bytes()),
                  campaigns={}, corpus=[], matrix=[], negatives=[], traces=[])

    def save():
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')

    # These builds preserve the public entry points and all host/layout guards.
    before = build(args.before_source, scratch/'before', options, deadline)
    after = build(olmkirakira.SOURCE, scratch/'after', options, deadline)
    before_off = build(args.before_source, scratch/'before-off', options, deadline, True)
    after_off = build(olmkirakira.SOURCE, scratch/'after-off', options, deadline, True)
    directory = scratch/'case'
    directory.mkdir(exist_ok=True)
    try:
        for seed in (1, 2):
            campaigns = {kind: json.loads((args.campaign_dir/f'{kind}-seed{seed}.json').read_text())
                         for kind in ('before', 'after', 'gateoff')}
            for campaign in campaigns.values():
                assert campaign['status'] == 'complete' and campaign['completed'] == 300
            mapped = {k: {r['index']: r for r in v['cases']} for k, v in campaigns.items()}
            rows = []
            for index in range(300):
                old, new, off = (mapped[k][index] for k in ('before', 'after', 'gateoff'))
                case = after.generate(seed, index)
                assert sha(case['pixels']) == old['input_sha256'] == new['input_sha256'] == off['input_sha256']
                assert old['result']['oracle'] == new['result']['oracle'] == off['result']['oracle']
                expected = promoted(case)
                for route in ('classic', 'smart'):
                    prior = old['result']['routes'][route]
                    current = new['result']['routes'][route]
                    disabled = off['result']['routes'][route]
                    assert prior['status'] == 'refusal'
                    assert current['status'] == ('exact' if expected else 'refusal'), (seed, index, route, current)
                    if expected:
                        assert disabled['status'] == 'exact'
                        assert disabled['raw_sha256'] == current['raw_sha256']
                    sanitized, raw, *_ = after.candidate(case, directory, route, deadline)
                    assert sanitized['status'] == ('ok' if expected else 'refusal'), sanitized
                    if expected:
                        assert sha(raw) == current['raw_sha256']
                if expected:
                    rows.append(dict(index=index, depth=case['depth'], geometry=case['geometry'],
                                     input_sha256=new['input_sha256'], result=new['result']))
            report['campaigns'][str(seed)] = dict(
                summaries={k: v['summary'] for k, v in campaigns.items()}, admitted=rows,
                provenance={k: v['provenance'] for k, v in campaigns.items()},
                report_sha256={k: sha((args.campaign_dir/f'{k}-seed{seed}.json').read_bytes()) for k in campaigns},
                sanitizer_routes=600, zero_admitted_mismatches=True)
            save()
            print('campaign', seed, 'admitted', len(rows), 'sanitized routes', 600, flush=True)

        # Audit fresh before/after, preserving historical saved expectations.
        for corpus in ('olmkirakira', 'olmkirakira_gate_off_T06'):
            for path in sorted((ROOT/'tests/fuzz_corpus'/corpus).glob('*.json')):
                case, saved = load_corpus(path, after)
                oracle, reference = after.oracle(case, directory, deadline)
                assert oracle['status'] == 'ok', oracle
                for route in ('classic', 'smart'):
                    old, oldraw = observation(before, case, directory, route, deadline, reference)
                    new, newraw = observation(after, case, directory, route, deadline, reference)
                    assert old == new or (old['status'] == 'refusal' and new['status'] == 'exact'), (path, route, old, new)
                    old_off, old_off_raw = observation(before_off, case, directory, route, deadline, reference)
                    new_off, new_off_raw = observation(after_off, case, directory, route, deadline, reference)
                    assert old_off == new_off and old_off_raw == new_off_raw
                    report['corpus'].append(dict(path=str(path.relative_to(ROOT)), route=route,
                        saved=saved['result']['routes'][route], before=old, after=new,
                        diagnostic_unchanged=new_off, reference_sha256=sha(reference)))
            save()
            print('corpus', corpus, 'complete', flush=True)

        combinations = itertools.product(((9, 7), (17, 11), (31, 29)), (8, 16, 32),
                                         (1, 2), (1, 2, 3), range(1, 7))
        for index, (geometry, depth, merge, mode, channel) in enumerate(combinations):
            case = matrix_case(after, index, geometry, depth, merge, mode, channel)
            oracle, reference = after.oracle(case, directory, deadline)
            assert oracle['status'] == 'ok', (index, oracle)
            row = dict(index=index, geometry=list(geometry), depth=depth, merge=merge, mode=mode,
                       channel=channel, input_sha256=sha(case['pixels']), reference_sha256=sha(reference), routes={})
            report['matrix'].append(row)
            for route in ('classic', 'smart'):
                result, _ = observation(after, case, directory, route, deadline, reference)
                row['routes'][route] = result
                assert result['status'] == 'exact', row
            if index % 54 == 53:
                save()
                print('independent matrix', index+1, 'exact both routes', flush=True)

        # One-away settings must still refuse; the host checks unchanged output,
        # source/padding preservation and balanced parameter callbacks on error.
        base = matrix_case(after, 0, (17, 11), 32, 1, 2, 1)
        changes = [(f'active-slot-{s}', s, 1) for s in (10, 16, 22, 28, 34)]
        changes += [('approximated', 4, 1), ('source-opacity', 9, 99), ('mode4', 2, 4)]
        negatives = []
        for label, slot, value in changes:
            case = copy.deepcopy(base)
            next(v for v in case['parameters'] if v['slot'] == slot)['value'] = value
            negatives.append((label, case))
        for label, word in [('hdr', 0x40000000), ('negative', 0xbf800000), ('nonfinite', 0x7fc12345)]:
            case = copy.deepcopy(base)
            case['pixels'] = struct.pack('<I', word)+case['pixels'][4:]
            negatives.append((label, case))
        for geometry in ((8, 7), (9, 6), (1, 1)):
            negatives.append((f'tiny-{geometry}', matrix_case(after, 0, geometry, 32, 1, 2, 1)))
        for label, case in negatives:
            row = dict(label=label, routes={})
            for route in ('classic', 'smart'):
                result, raw, *_ = after.candidate(case, directory, route, deadline)
                row['routes'][route] = result
                assert result['status'] == 'refusal' and not raw, row
            report['negatives'].append(row)
        save()
        print('negative controls', len(negatives)*2, 'refused', flush=True)

        # Three independent original-AEX traces bind zero ray/glow stages to
        # retained exported Smart output, then to Mac Classic production stages.
        traced = build_mac(olmkirakira.SOURCE, scratch/'trace-build', options, deadline, False)
        trace_dir = scratch/'trace-data'
        trace_dir.mkdir(exist_ok=True)
        for depth in (8, 16, 32):
            case = matrix_case(after, depth, (9, 7), depth, 1, 2, 1)
            values = {5: 1., 6: 100, 7: 0., 8: 100, 9: 100}
            values.update({s: 0 for s in (13, 19, 25, 31, 37)})
            for value in case['parameters']:
                if value['slot'] in values:
                    value['value'] = values[value['slot']]
            traced.env['F09_TRACE'] = str(trace_dir)
            oracle, reference = traced.oracle(case, directory, deadline)
            result, raw, *_ = traced.candidate(case, directory, 'classic', deadline)
            original = original_trace(case, traced.aex)
            stages = original['stages']
            assert oracle['status'] == result['status'] == 'ok'
            assert bytes.fromhex(stages['output']) == reference == raw
            pairs = {}
            for name in ('source', 'seed', 'ray0', 'ray1', 'ray2', 'ray3', 'ray4', 'glow', 'composed'):
                aex = bytes.fromhex(stages[name])
                mac = (trace_dir/(name+'.raw')).read_bytes()
                pairs[name] = dict(aex_sha256=sha(aex), mac_sha256=sha(mac), exact=aex == mac,
                                  diff=None if aex == mac else raw_diff(aex, mac, 32))
                if name != 'composed':
                    assert aex == mac, (depth, name, raw_diff(aex, mac, 32))
                if name.startswith('ray') or name == 'glow':
                    assert not any(aex)
            # F09's composed hooks straddle different clamp boundaries for NaN:
            # the AEX hook precedes a raw store, after FUN_181156740/MAXSS;
            # the Mac hook precedes PixelTraits::WriteAexTruncate/Clamp01.
            # PF32 stores have no quantization: reorder actual production bytes
            # from ARGB to RGBA to compare the same post-clamp boundary. Keep
            # the original pre-clamp mismatch above; do not repair either image.
            if depth == 32:
                stored_rgba = b''.join(raw[i+4:i+16]+raw[i:i+4] for i in range(0, len(raw), 16))
                assert stored_rgba == bytes.fromhex(stages['composed'])
                pairs['post_clamp_store'] = dict(exact=True, mac_sha256=sha(stored_rgba),
                    aex_sha256=sha(bytes.fromhex(stages['composed'])))
            assert not original['geometry'], original['geometry']
            report['traces'].append(dict(depth=depth, input_sha256=sha(case['pixels']),
                reference_sha256=sha(reference), output_sha256=sha(raw), paired=pairs,
                geometry_calls=0, abi_leaf_exact=True, public_binding_exact=True))
            save()
            print('trace', depth, 'zero rays/glow exact; public bound; pre-clamp composed exact',
                  pairs['composed']['exact'], flush=True)
        report['status'] = 'passed'
        save()
    except BaseException as exc:
        report['status'] = 'failed'
        report['error'] = repr(exc)
        save()
        raise
    finally:
        for name in ('before', 'after', 'before-off', 'after-off', 'trace-build', 'trace-data', 'case'):
            shutil.rmtree(scratch/name, ignore_errors=True)
    print('PASS', flush=True)


if __name__ == '__main__':
    if '--campaign-source' in sys.argv:
        # Reproduce the pre-change run.py campaign without switching branches
        # or editing production. Remaining arguments are ordinary run.py flags.
        p = argparse.ArgumentParser(add_help=False)
        p.add_argument('--campaign-source', type=Path, required=True)
        args, rest = p.parse_known_args()
        olmkirakira.Adapter = adapter_class(args.campaign_source.resolve(), sanitizers=False)
        import run
        sys.argv = [sys.argv[0], *rest]
        sys.exit(run.main())
    else:
        main()
