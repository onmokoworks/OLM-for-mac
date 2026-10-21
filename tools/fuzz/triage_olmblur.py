#!/usr/bin/env python3
"""OLMBlur fuzz-residual triage: refusal ranking, gate-off probes, cluster stats.

Scratch-only builds. The production source is never modified by this script; a
copy with one compile-time gate removed is compiled per variant.
"""
from __future__ import annotations
import argparse
import copy
import json
import math
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/fuzz'))
from core import evaluate, load_corpus, sha  # noqa: E402
from adapters import olmblur  # noqa: E402
from adapters.public import ROOT as PROOT, replace_once  # noqa: E402

CHANNELS = ('A', 'R', 'G', 'B')


def options():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--census', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--scratch', type=Path, default=ROOT/'orchestra/state/T09-triage-olmblur')
    p.add_argument('--jobs', type=int, default=2)
    p.add_argument('--corpus', type=Path, default=ROOT/'tests/fuzz_corpus/olmblur')
    p.add_argument('--max-size', type=int, default=256)
    p.add_argument('--case-timeout', type=float, default=20)
    p.add_argument('--skip-gates', action='store_true')
    return p.parse_args()


def harness_body(source):
    body = olmblur.HOST.read_text().split('static unsigned char *misaligned_payload', 1)[0]
    body = body.replace('../../mac/OLMBlur/OLMBlur.cpp', str(source))
    body = body.replace('{0, 0, 24, 24}', '{0, 0, g_input->width, g_input->height}')
    body = replace_once(body, 'result->ref_width = 24; result->ref_height = 24;',
                        'result->ref_width = g_input->width; result->ref_height = g_input->height;')
    body = replace_once(body, 'static_cast<size_t>(src->rowbytes));',
                        'static_cast<size_t>(src->width)*(g_depth/8*4));')
    body += '\n#include "' + str(olmblur.PARAMETERS) + '"\n' + olmblur.MAIN.read_text()
    return body


def build_binary(adapter, scratch, sanitize=False):
    body = harness_body(adapter_source())
    host = scratch/'host.cpp'
    host.write_text(body)
    sdk = subprocess.check_output(['xcrun', '--show-sdk-path'], stderr=subprocess.DEVNULL).decode().strip()
    glimpses = []
    for directory in ('Headers', 'Headers/SP', 'Util', 'Resources'):
        glimpses += ['-I', str(adapter.main/directory)]
    source = adapter_source()
    argv = ['clang++', '-std=c++17', '-arch', 'arm64',
            '-O2' if not sanitize else '-O1',
            '-fno-fast-math', '-ffp-contract=off',
            '-Wno-deprecated-declarations', '-Wno-pragma-pack',
            '-ffunction-sections', '-fdata-sections', '-isysroot', sdk,
            *glimpses, '-I', str(ROOT/'core'), str(host),
            str(source.with_name(source.stem+'_Strings.cpp')),
            *[str(p) for p in olmblur.CORES],
            str(adapter.main/'Util/AEGP_SuiteHandler.cpp'),
            str(adapter.main/'Util/MissingSuiteError.cpp')]
    if sanitize:
        argv += ['-fsanitize=address,undefined', '-fno-sanitize-recover=all']
    argv += ['-Wl,-dead_strip', '-framework', 'Cocoa', '-o', str(scratch/'mac')]
    proc = subprocess.run(argv, capture_output=True, env=adapter.env)
    if proc.returncode:
        raise RuntimeError('build failed: '+proc.stderr.decode(errors='replace')[-4000:])
    return scratch/'mac'


def adapter_source():
    return olmblur.SOURCE


def prepare_variant(args, variant, replacement):
    root = args.scratch/f'src_{variant}'
    if root.exists():
        shutil.rmtree(root)
    target = root/'mac/OLMBlur'
    target.mkdir(parents=True)
    (root/'core').symlink_to(ROOT/'core')
    source = Path(olmblur.__file__).resolve().parents[3]/'mac/OLMBlur/OLMBlur.cpp'
    text = source.read_text()
    old, new = replacement
    if text.count(old) != 1:
        raise ValueError(f'variant {variant}: source anchor count {text.count(old)}')
    (target/'OLMBlur.cpp').write_text(text.replace(old, new))
    for name in ('OLMBlur.h', 'OLMBlur_Strings.cpp', 'OLMBlur_Strings.h'):
        shutil.copy2(source.with_name(name), target/name)
    return target/'OLMBlur.cpp'


def make_adapter(args, main):
    ns = argparse.Namespace(max_size=args.max_size, case_timeout=args.case_timeout,
                            main=main, worker=Path(os.environ.get('OLM_AEX_WORKER',
                            '/Users/onmk/Documents/Codex/2026-10-05/task-3/AEXCompat-containment/guest/target/release/aex-guest-worker')))
    return olmblur.Adapter(ns)


def run_case(adapter, seed, index, scratch, deadline):
    case = adapter.generate(seed, index)
    with tempfile.TemporaryDirectory(prefix=f'case_{index}_', dir=scratch) as name:
        attribution = {}
        result = evaluate(adapter, case, Path(name), deadline, attribution)
    return {'index': index, 'case': {k: v for k, v in case.items() if k != 'pixels'},
            'geometry': case['geometry'], 'depth': case['depth'],
            'result': result, 'refusal_guards': attribution}


def run_gate_case(adapter, index, route, scratch, deadline):
    case = adapter.generate(1, index)
    with tempfile.TemporaryDirectory(prefix=f'gate_{index}_', dir=scratch) as name:
        directory = Path(name)
        oracle, reference = adapter.oracle(case, directory, deadline, route)
        outcome = adapter.candidate(case, directory, route, deadline)
        result, raw = outcome[0], outcome[1]
        guards = outcome[2] if len(outcome) > 2 else []
    status = result['status']
    diff = None
    if status == 'ok':
        if oracle['status'] == 'ok':
            status = 'exact' if raw == reference else 'mismatch'
            if status == 'mismatch':
                diff = diff_stats(reference, raw, case)
        else:
            status = 'uncompared'
    label = classify_route(dict(result, status=status))
    return {'index': index, 'case': {k: v for k, v in case.items() if k != 'pixels'},
            'status': label, 'error': result.get('error'), 'diff': diff,
            'diagnostic': result.get('diagnostic', ''), 'guards': guards}


def run_gate_cases(adapter, indices, route, scratch, deadline, jobs):
    out = {}

    def one(index):
        return run_gate_case(adapter, index, route, scratch, deadline)
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        for row in pool.map(one, indices):
            out[row['index']] = row
    return out


def classify_route(route):
    status = route['status']
    if status in ('exact', 'mismatch', 'refusal', 'uncompared'):
        return status
    diagnostic = route.get('diagnostic', '')
    if any(token in diagnostic for token in ('AddressSanitizer', 'LeakSanitizer',
                                             'runtime error:', 'UndefinedBehaviorSanitizer',
                                             'SUMMARY: ')):
        return 'sanitizer'
    return 'crash'


def diff_stats(reference, actual, case):
    w, h = case['geometry']
    depth = case['depth']
    channel_bytes = depth//8
    ps = channel_bytes*4
    unit = channel_bytes
    finite = depth != 32
    n = min(len(reference), len(actual))
    diffs = [i for i in range(n) if reference[i] != actual[i]]
    channels = {name: 0 for name in CHANNELS}
    pixels = set()
    words = 0
    max_abs = 0.0
    nonfinite_words = 0
    first = None
    differing_rows = set()
    for i in diffs:
        pixel = i//ps
        col = (i % ps)//channel_bytes
        channels[CHANNELS[col]] += 1
        pixels.add(pixel)
        differing_rows.add(pixel//w)
        if first is None:
            first = {'byte': i, 'pixel': pixel, 'x': pixel % w, 'y': pixel//w,
                     'channel': CHANNELS[col]}
    for pixel in pixels:
        base = pixel*ps
        for c in range(4):
            start = base+c*channel_bytes
            a = reference[start:start+channel_bytes]
            b = actual[start:start+channel_bytes]
            if a == b:
                continue
            words += 1
            if depth == 8:
                max_abs = max(max_abs, abs(a[0]-b[0]))
            elif depth == 16:
                va = struct.unpack('<H', a)[0]
                vb = struct.unpack('<H', b)[0]
                max_abs = max(max_abs, abs(va-vb))
            else:
                va = struct.unpack('<f', a)[0]
                vb = struct.unpack('<f', b)[0]
                if math.isfinite(va) and math.isfinite(vb):
                    max_abs = max(max_abs, abs(va-vb))
                else:
                    nonfinite_words += 1
    xs = [p % w for p in pixels]
    ys = [p//w for p in pixels]
    first_word = None
    if first is not None:
        base = first['pixel']*ps+CHANNELS.index(first['channel'])*channel_bytes
        first_word = {'expected_hex': reference[base:base+channel_bytes].hex(),
                      'actual_hex': actual[base:base+channel_bytes].hex()}
    return {'different_bytes': len(diffs)+abs(len(reference)-len(actual)),
            'different_pixels': len(pixels), 'different_channels': words,
            'channels': channels, 'max_abs_diff': max_abs,
            'nonfinite_words': nonfinite_words,
            'first': first, 'first_word': first_word,
            'bbox': [min(xs), min(ys), max(xs), max(ys)] if xs else None,
            'differing_rows': len(differing_rows),
            'row_span': [min(ys), max(ys)] if ys else None,
            'expected_bytes': len(reference), 'actual_bytes': len(actual),
            'reference_is_input': reference == case['pixels'],
            'actual_is_input': actual == case['pixels']}


def cluster_table(adapter, args, scratch, deadline):
    files = sorted(args.corpus.glob('*.json'))
    groups = {}
    for path in files:
        data = json.loads(path.read_text())
        case, saved = load_corpus(path, adapter)
        defaults = {p['slot']: p['value'] for p in adapter.defaults(*case['geometry'])}
        slots = [p['slot'] for p in case['parameters'] if p['value'] != defaults[p['slot']]]
        key = json.dumps([saved['result'].get('first_mismatching_stage') or 'raw-output', slots, case['depth']],
                         separators=(',', ':'))
        groups.setdefault(key, []).append((path, data, case))
    rows = []
    for key, members in sorted(groups.items()):
        def weight(member):
            path, data, case = member
            w, h = case['geometry']
            slots = len(json.loads(key)[1])
            return (w*h*case['depth']//8*4, slots, path.name)
        path, data, case = min(members, key=weight)
        with tempfile.TemporaryDirectory(prefix='cluster_', dir=scratch) as name:
            directory = Path(name)
            routes, oracles = {}, {}
            for route in adapter.routes:
                oracle, reference = adapter.oracle(case, directory, deadline, route)
                oracles[route] = oracle
                outcome = adapter.candidate(case, directory, route, deadline)
                result, raw = outcome[0], outcome[1]
                entry = {'status': result['status'], 'error': result.get('error')}
                if result['status'] == 'ok':
                    entry['status'] = ('exact' if raw == reference else 'mismatch') if oracle['status'] == 'ok' else 'uncompared'
                if entry['status'] == 'mismatch':
                    entry['diff'] = diff_stats(reference, raw, case)
                routes[route] = entry
        params = {str(p['slot']): p['value'] for p in case['parameters']}
        rows.append({'cluster': key, 'members': [str(m[0].name) for m in members],
                     'member_indices': sorted(m[1]['index'] for m in members),
                     'representative': str(path.name), 'index': data['index'],
                     'geometry': case['geometry'], 'depth': case['depth'],
                     'profile': case.get('profile'), 'parameters': params,
                     'input_sha256': data['input_sha256'],
                     'oracle_status': {route:o['status'] for route,o in oracles.items()}, 'routes': routes,
                     'saved_routes': saved['result']['routes'] if 'result' in data else None})
    return rows


def main():
    args = options()
    args.scratch = args.scratch.resolve()
    args.report = args.report.resolve()
    args.corpus = args.corpus.resolve()
    args.scratch.mkdir(parents=True, exist_ok=True)
    os.environ.update(TMPDIR=str(args.scratch), TMP=str(args.scratch), TEMP=str(args.scratch))
    tempfile.tempdir = str(args.scratch)
    # main_checkout must be the read-only MAIN checkout (the fuzz --main default).
    main_checkout = ROOT.parent.parent if ROOT.parent.name == 'worktrees' else ROOT
    if not (Path(main_checkout)/'plugins_2025/OLMBlur.aex').is_file():
        main_checkout = Path('/Users/onmk/Documents/Projects/Personal/OLM as')

    adapter = make_adapter(args, Path(main_checkout))
    deadline = time.monotonic()+3600
    build_dir = args.scratch/'build_production'
    build_dir.mkdir(exist_ok=True)
    adapter.binary = build_binary(adapter, build_dir)
    provenance = {'candidate_sha256': sha(adapter.binary.read_bytes()),
                  'source_sha256': sha(adapter_source().read_bytes()),
                  'worker_sha256': sha(Path(adapter.worker).read_bytes())}

    census = json.loads(args.census.read_text())
    guards = {'classic': {}, 'smart': {}}
    targets = {}
    for route in ('classic', 'smart'):
        for row in census['cases']:
            res = row['result']['routes'][route]
            tags = row.get('refusal_guards', {}).get(route, [])
            for tag in tags:
                guards[route].setdefault(tag, {'events': 0, 'cases': set()})
                guards[route][tag]['events'] += 1
                guards[route][tag]['cases'].add(row['index'])
        for tag, value in guards[route].items():
            value['cases'] = sorted(value['cases'])

    variants = {
        'smart-small-fixture-off': (
            '	// Preserve the tiny captured fixtures below as exact compatibility owners.\n'
            '	if (width <= 24 && height <= 24) return "generic-small-fixture";',
            '	// triage gate-off: generic small-fixture admission disabled'),
        'classic-nondefault-tuple-off': (
            '	if (blur_amount != 5.0 || blur_smoothness != 100 * 65536 || repeat != 2) {\n'
            '		return OLM_BLUR_REFUSAL("classic-nondefault-tuple");\n'
            '	}',
            '	// triage gate-off: classic default-copy tuple admission disabled'),
        'classic-pf32-naive-off': (
            '		return OLM_BLUR_REFUSAL("classic-pf32-unowned");',
            '		break;'),
        'classic-pf32-copy-off': (
            '		return OLM_BLUR_REFUSAL("classic-pf32-unowned");',
            '		pixel_bytes = sizeof(PF_PixelFloat); break;'),
    }

    gate_report = {}
    if not args.skip_gates:
        targets = {
            'smart-small-fixture-off': ('smart', 'SmartRender:generic-small-fixture'),
            'classic-nondefault-tuple-off': ('classic', 'Render:classic-nondefault-tuple'),
            'classic-pf32-naive-off': ('classic', 'Render:classic-pf32-unowned'),
            'classic-pf32-copy-off': ('classic', 'Render:classic-pf32-unowned'),
        }
        for name, replacement in variants.items():
            patched = prepare_variant(args, name, replacement)
            olmblur.SOURCE = patched
            variant_scratch = args.scratch/f'build_{name}'
            variant_scratch.mkdir(exist_ok=True)
            adapter.binary = build_binary(adapter, variant_scratch)
            route, guard = targets[name]
            if name == 'classic-pf32-copy-off':
                # Compound probe: the copy destination is only reachable when the
                # default-copy tuple gate is also disabled.
                text = patched.read_text()
                text = text.replace(
                    '	if (blur_amount != 5.0 || blur_smoothness != 100 * 65536 || repeat != 2) {\n'
                    '		return OLM_BLUR_REFUSAL("classic-nondefault-tuple");\n'
                    '	}', '	// triage compound: tuple gate off')
                patched.write_text(text)
                variant_scratch = args.scratch/f'build_{name}_full'
                variant_scratch.mkdir(exist_ok=True)
                adapter.binary = build_binary(adapter, variant_scratch)
            key = next(k for k in guards[route] if k.startswith(guard))
            indices = guards[route][key]['cases']
            rows = run_gate_cases(adapter, indices, route, args.scratch, deadline, args.jobs)
            counts = {}
            successor = {}
            details = []
            for index in indices:
                entry = rows[index]
                label = entry['status']
                counts[label] = counts.get(label, 0) + 1
                for tag in entry['guards']:
                    successor[tag] = successor.get(tag, 0)+1
                detail = {'index': index, 'status': label,
                          'geometry': entry['case']['geometry'], 'depth': entry['case']['depth'],
                          'legacy': next((p['value'] for p in entry['case']['parameters']
                                          if p['slot'] == 5), None)}
                if entry['error'] is not None:
                    detail['error'] = entry['error']
                if entry['diff'] is not None:
                    detail['diff'] = entry['diff']
                if label in ('sanitizer', 'crash'):
                    detail['diagnostic'] = entry['diagnostic'][-2000:]
                details.append(detail)
            gate_report[name] = {'route': route, 'guard': guard,
                                 'attempted': len(indices), 'counts': counts,
                                 'successor_tags': successor, 'cases': details}
            print('GATE', name, len(indices), counts, flush=True)

            if name in ('smart-small-fixture-off', 'classic-nondefault-tuple-off'):
                san_scratch = args.scratch/f'build_{name}_san'
                san_scratch.mkdir(exist_ok=True)
                adapter.binary = build_binary(adapter, san_scratch, sanitize=True)
                saved_env = dict(adapter.env)
                adapter.env.update(ASAN_OPTIONS='detect_leaks=0', UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=0')
                san_rows = run_gate_cases(adapter, indices, route, args.scratch, deadline, args.jobs)
                san_counts = {}
                san_details = []
                for index in indices:
                    entry = san_rows[index]
                    label = entry['status']
                    san_counts[label] = san_counts.get(label, 0)+1
                    if label in ('sanitizer', 'crash'):
                        san_details.append({'index': index, 'status': label,
                                            'geometry': entry['case']['geometry'],
                                            'depth': entry['case']['depth'],
                                            'diagnostic': entry['diagnostic'][-2000:]})
                gate_report[name]['sanitized_counts'] = san_counts
                gate_report[name]['sanitized_cases'] = san_details
                adapter.env = saved_env
                print('GATE-SAN', name, san_counts, flush=True)
        olmblur.SOURCE = Path(olmblur.__file__).resolve().parents[3]/'mac/OLMBlur/OLMBlur.cpp'
        adapter.binary = build_binary(adapter, build_dir)

    clusters = cluster_table(adapter, args, args.scratch, deadline)
    report = {'schema': 'olmblur-triage/1', 'census': str(args.census),
              'provenance': provenance,
              'guards': {route: {tag: {'events': v['events'], 'cases': v['cases']}
                                 for tag, v in values.items()}
                         for route, values in guards.items()},
              'gate_off': gate_report, 'clusters': clusters}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    print('WROTE', args.report)


if __name__ == '__main__':
    main()
