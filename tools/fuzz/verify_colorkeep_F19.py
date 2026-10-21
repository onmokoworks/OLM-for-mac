#!/usr/bin/env python3
"""F19 evidence, seed snapshot replay, and existing tests using MAIN's SDK read-only."""
import argparse
from collections import Counter
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import struct
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
from adapters.colorkeep import Adapter
from core import crop, evaluate, save_corpus, sha
from run import ROOT, main_checkout

TICKET = 'F19-colorkeep-host-flags-and-byte-safe'
WORKER = Path('/Users/onmk/.cache/olm-emu/radial_windows_reference_v2_20261001/target/release/aex-guest-worker')
EVIDENCE = ROOT/'reports/fuzz/colorkeep_F19.json'


def read(path):
    return json.loads(path.read_text())


def clean(result):
    result = copy.deepcopy(result)
    for value in result['routes'].values():
        value.pop('sanitizer', None)
    return result


def snapshot(report, destination, phase):
    destination.mkdir(parents=True, exist_ok=True)
    if phase == 'shrunk':
        for row in report['shrunk_corpus']:
            (destination/f"{row['index']:03d}.json").write_text(json.dumps(row, indent=2)+'\n')
        print(f"snapshot: {len(report['shrunk_corpus'])} retained shrunk cases -> {destination}")
        return
    adapter = Adapter(SimpleNamespace(main=main_checkout(), worker=WORKER, max_size=256, case_timeout=10))
    rows = report['cases']
    for row in rows:
        case = adapter.generate(1, row['index'])
        assert sha(case['pixels']) == row['input_sha256']
        result = row[phase] if phase else row['result']
        save_corpus(destination/f"{row['index']:03d}.json", adapter, case, case, result,
                    {'accepted': []}, report.get('provenance', {}))
    print(f'snapshot: {len(rows)} cases -> {destination}')


def record(scratch, destination):
    reports = {name: read(scratch/(name+'.json')) for name in
               ('before', 'host-before-sanitize', 'final', 'after-sanitize')}
    for report in reports.values():
        assert report['status'] == 'complete' and report['completed'] == 300
    rows = {name: sorted(report['cases'], key=lambda r: r['index']) for name, report in reports.items()}
    evidence = {'schema': 'olm-colorkeep-F19/1', 'summary': {}, 'provenance': {}, 'cases': [], 'replays': {}}
    for name, report in reports.items():
        evidence['provenance'][name] = report['provenance']
        evidence['summary'][name] = dict(report['summary'], sanitizer_cases={
            route: sum(bool(row['result']['routes'][route].get('sanitizer')) for row in rows[name])
            for route in ('classic', 'smart')}, smart_sanitizer_by_depth={
            depth: sum(bool(row['result']['routes']['smart'].get('sanitizer'))
                       for row in rows[name] if row['depth'] == depth) for depth in (8, 16, 32)})
    transitions = Counter()
    for before, host, final, sanitized in zip(*(rows[n] for n in reports)):
        assert before['index'] == host['index'] == final['index'] == sanitized['index']
        assert before['input_sha256'] == host['input_sha256'] == final['input_sha256'] == sanitized['input_sha256']
        assert clean(host['result']) == final['result'] == sanitized['result']
        assert before['result']['oracles'] == final['result']['oracles']
        for route in ('classic', 'smart'):
            a, b = before['result']['routes'][route], final['result']['routes'][route]
            transitions[f"{route}: {a['status']} -> {b['status']}"] += 1
            assert a == b or (route == 'smart' and a['status'] == 'refusal' and b['status'] == 'exact')
        evidence['cases'].append(dict(index=before['index'], input_sha256=before['input_sha256'],
            before=before['result'], after=final['result']))
    evidence['transitions'] = dict(transitions)
    evidence['witnesses'] = read(scratch/'witnesses.json')
    evidence['first_refusal'] = {key: rows['before'][2][key] for key in
        ('index', 'geometry', 'depth', 'input_padding', 'output_padding', 'refusal_guards')}
    evidence['first_mismatch'] = rows['before'][0]['result']['routes']['classic']['diff']
    for name in ('replay-before', 'replay-after', 'replay-shrunk'):
        report = read(scratch/(name+'.json'))
        evidence['replays'][name] = dict(status=report['status'], completed=report['completed'],
            matches_saved=sum(r['matches_saved'] for r in report['replays']))
    assert evidence['replays'] == {
        'replay-before': {'status': 'replay_complete', 'completed': 300, 'matches_saved': 205},
        'replay-after': {'status': 'replay_complete', 'completed': 300, 'matches_saved': 300},
        'replay-shrunk': {'status': 'replay_complete', 'completed': 100, 'matches_saved': 100}}
    # Preserve procedural inputs/operations so the byte-capped selection from
    # the parallel baseline is reproducible without retaining scratch files.
    evidence['shrunk_corpus'] = []
    for replay in read(scratch/'replay-shrunk.json')['replays']:
        saved = read(Path(replay['path']))
        evidence['shrunk_corpus'].append({key: saved[key] for key in
            ('schema', 'plugin', 'generator_version', 'seed', 'index', 'max_size',
             'operations', 'input_sha256', 'result')})
    destination.write_text(json.dumps(evidence, sort_keys=True, indent=2)+'\n')
    print(json.dumps({'transitions': evidence['transitions'], 'replays': evidence['replays']}))


def check(report, evidence):
    rows = sorted(report['cases'], key=lambda r: r['index'])
    assert report['status'] == 'complete' and len(rows) == 300
    for actual, saved in zip(rows, evidence['cases']):
        assert actual['index'] == saved['index']
        assert actual['input_sha256'] == saved['input_sha256']
        assert actual['result'] == saved['after'], actual['index']
    print('300/300 complete result dictionaries match F19; no sanitizer diagnostics')


def tests():
    # Existing tests assume SDK symlinks in the checkout. Resolve only those
    # missing SDK paths to MAIN; all production code stays in this worktree.
    main = main_checkout()
    real_run = subprocess.run
    def sdk_run(argv, *args, **kwargs):
        rewritten = []
        for arg in argv:
            value = str(arg)
            include = value.startswith('-I')
            path = Path(value[2:] if include else value)
            absolute = path if path.is_absolute() else ROOT/path
            if absolute.is_relative_to(ROOT):
                relative = absolute.relative_to(ROOT)
                if relative.parts and relative.parts[0] in ('Headers', 'Util', 'Resources'):
                    value = ('-I' if include else '') + str(main/relative)
            rewritten.append(value)
        return real_run(rewritten, *args, **kwargs)
    def load(name):
        spec = importlib.util.spec_from_file_location(name, ROOT/'tests'/f'{name}.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    callbacks = load('test_colorkeep_windows_callback_contract_20260731')
    generic = load('test_colorkeep_generic_beta_20260820')
    roi = load('test_colorkeep_roi_tile_beta_20260820')
    suite = unittest.defaultTestLoader.loadTestsFromModule(callbacks)
    for function in (generic.test_checkout_cleanup_contract_and_windows_owner_evidence,
                     generic.test_generic_worlds_counts_and_typed_workers,
                     roi.test_roi_tile_admission_contract_is_one_to_one):
        suite.addTest(unittest.FunctionTestCase(function))
    with patch.object(subprocess, 'run', sdk_run):
        assert unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful()


def witnesses(scratch):
    os.environ['OLM_COLOR_TRIAGE_SANITIZE'] = '1'
    os.environ['ASAN_OPTIONS'] = 'detect_leaks=0'
    os.environ['UBSAN_OPTIONS'] = 'halt_on_error=1'
    adapter = Adapter(SimpleNamespace(main=main_checkout(), worker=WORKER, max_size=256, case_timeout=10))
    adapter.routes = ('smart',)
    adapter.oracle_routes = {'smart': 'smart'}
    deadline = time.monotonic() + 120
    with tempfile.TemporaryDirectory(prefix='witness-', dir=scratch) as raw:
        directory = Path(raw)
        provenance = adapter.prepare(directory, deadline)
        cases = [(f'seed1-index{index}-crop1x2', crop(adapter.generate(1, index), 1, 2))
                 for index in (2, 3)]
        # Black palette, alpha 1. Keep signaling NaN payloads as integer words;
        # packing Python floats would quiet them before either plugin sees them.
        for name, words in (
            ('snan-alpha-and-rgb', (0x7f812345, 0xff854321, 0x80000000, 0)),
            ('rejected-alpha-snan-rgb', (0x3f000000, 0x7f812345, 0, 0)),
            ('signed-zero', (0x3f800000, 0x80000000, 0, 0x80000000)),
            ('infinite-rgb', (0x3f800000, 0x7f800000, 0xff800000, 0))):
            case = adapter.generate(1, 2)
            case.update(geometry=[1, 2], parameters=adapter.defaults(1, 2),
                        input_padding=1, output_padding=3, pixels=struct.pack('<4I', *words)*2)
            cases.append((name, case))
        records = []
        for name, case in cases:
            trace = {}
            result = evaluate(adapter, case, directory, deadline, trace)
            assert result['routes']['smart']['status'] == 'exact', (name, result)
            assert 'sanitizer' not in result['routes']['smart'] and not trace
            records.append(dict(name=name, depth=case['depth'], geometry=case['geometry'],
                input_sha256=sha(case['pixels']), result=result))
        (scratch/'witnesses.json').write_text(json.dumps(dict(provenance=provenance, cases=records), indent=2)+'\n')
        print(f'{len(records)}/{len(records)} shrunk/float-bit witnesses AEX exact, sanitizer clean')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('snapshot', 'record', 'check', 'tests', 'witnesses'))
    parser.add_argument('--scratch', type=Path, default=ROOT/'orchestra/state'/TICKET)
    parser.add_argument('--report', type=Path)
    parser.add_argument('--evidence', type=Path, default=EVIDENCE)
    parser.add_argument('--destination', type=Path)
    parser.add_argument('--phase', choices=('before', 'after', 'shrunk'))
    args = parser.parse_args()
    args.scratch = args.scratch.resolve()
    assert args.scratch.is_relative_to(ROOT/'orchestra/state'/TICKET)
    args.scratch.mkdir(parents=True, exist_ok=True)
    os.environ.update(TMPDIR=str(args.scratch), TMP=str(args.scratch), TEMP=str(args.scratch), PYTHONDONTWRITEBYTECODE='1')
    tempfile.tempdir = str(args.scratch)
    if args.action == 'snapshot':
        assert args.destination.resolve().is_relative_to(args.scratch)
        snapshot(read(args.report or args.evidence), args.destination, args.phase)
    elif args.action == 'record':
        record(args.scratch, args.evidence)
    elif args.action == 'check':
        check(read(args.report), read(args.evidence))
    elif args.action == 'witnesses':
        witnesses(args.scratch)
    else:
        tests()


if __name__ == '__main__':
    main()
