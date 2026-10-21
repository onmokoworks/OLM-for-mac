#!/usr/bin/env python3
"""Summarize the T12 campaigns and independently measure retained raw witnesses."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import importlib
import json
import math
import os
from pathlib import Path
import re
import struct
import tempfile
import time
from types import SimpleNamespace

from core import load_corpus, raw_diff, save_corpus, sha
from run import ROOT, main_checkout


def smart_oracle(result):
    return result.get('oracles', {}).get('smart', result['oracle'])


def comparable(row):
    result = row['result']
    return dict(input_sha256=row['input_sha256'], oracle=smart_oracle(result),
                candidate=result['routes']['smart'])


def stable_diagnostic(message):
    # ASLR addresses and temporary build names are not distinct failure classes.
    message = re.sub(r'0x[0-9a-fA-F]+', '<address>', message)
    message = re.sub(r'/run_[^/]+/', '/<build>/', message)
    return message.replace(str(ROOT)+'/', '')


def byte_stats(reference, actual, source, depth, geometry):
    unit = depth // 8
    differences = [i for i, (a, b) in enumerate(zip(reference, actual)) if a != b]
    words = sorted(set(i // unit for i in differences))
    fmt = {8: '<B', 16: '<H', 32: '<f'}[depth]
    samples = []
    finite = []
    channels = Counter()
    for word in words:
        offset = word * unit
        a, b = struct.unpack_from(fmt, reference, offset)[0], struct.unpack_from(fmt, actual, offset)[0]
        channel = 'ARGB'[word % 4]
        pixel = word // 4
        channels[channel] += 1
        if math.isfinite(a) and math.isfinite(b):
            finite.append(abs(a - b))
        samples.append(dict(x=pixel % geometry[0], y=pixel // geometry[0], channel=channel,
                            source_hex=source[offset:offset+unit].hex(),
                            aex_hex=reference[offset:offset+unit].hex(),
                            mac_hex=actual[offset:offset+unit].hex()))
    return dict(raw_diff(reference, actual, depth), channels=dict(channels),
                max_abs_byte_diff=max((abs(reference[i]-actual[i]) for i in differences), default=0),
                max_abs_finite_sample_diff=max(finite) if finite else None,
                nonfinite_different_samples=len(words)-len(finite),
                different_samples=samples)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scratch', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--worker', type=Path, required=True)
    parser.add_argument('--jobs', type=int, choices=[2], required=True)
    args = parser.parse_args()
    args.scratch = args.scratch.resolve()
    assert args.scratch.is_relative_to(ROOT/'orchestra/state/T12-triage-colorkeep-colorkey')
    os.environ.update(TMPDIR=str(args.scratch), TMP=str(args.scratch), TEMP=str(args.scratch))
    for key in ('OLM_COLOR_TRIAGE_BYPASS', 'OLM_COLOR_TRIAGE_SANITIZE',
                'OLM_COLOR_TRIAGE_HOST_FLAGS', 'OLM_COLOR_TRIAGE_NO_TRACE'):
        os.environ.pop(key, None)
    options = SimpleNamespace(main=main_checkout(), worker=args.worker, max_size=256, case_timeout=10)
    output = {'schema': 'olm-color-triage-T12/1', 'route': 'smart', 'plugins': {}}
    for plugin in ('colorkeep', 'olmcolorkey'):
        reports = {}
        for mode in ('before', 'trace', 'bypass', 'sanitize-default', 'sanitize-bypass', 'host'):
            path = args.scratch/f'{mode}-{plugin}.json'
            if path.exists():
                reports[mode] = json.loads(path.read_text())
        baseline = reports['trace']['cases']
        refused = {row['index'] for row in baseline if row['result']['routes']['smart']['status']=='refusal'}
        report = dict(provenance={mode: r['provenance'] for mode, r in reports.items()},
                      framework_sha256={mode:r['framework_sha256'] for mode,r in reports.items()},
                      campaign_hashes={mode: sha((args.scratch/f'{mode}-{plugin}.json').read_bytes())
                                       for mode in reports},
                      neutrality=sum(comparable(a)==comparable(b) for a,b in
                                     zip(reports['before']['cases'], baseline)),
                      total=len(baseline),
                      guards=dict(Counter(g.split('@')[0] for row in baseline
                                          for g in row.get('refusal_guards', {}).get('smart', []))),
                      campaigns={}, baseline=[dict(index=r['index'], **comparable(r),
                                                  guards=r.get('refusal_guards',{})) for r in baseline])
        for mode, r in reports.items():
            candidates = [row['result']['routes']['smart'] for row in r['cases']]
            selected = [row['result']['routes']['smart'] for row in r['cases'] if row['index'] in refused]
            report['campaigns'][mode] = dict(
                summary=r['summary'], total=len(r['cases']),
                previously_refused=dict(Counter(c['status'] for c in selected)),
                sanitizer_rows=sum(bool(c.get('sanitizer')) for c in candidates),
                refused_sanitizer_rows=sum(bool(c.get('sanitizer')) for c in selected),
                sanitizer_messages=dict(Counter(stable_diagnostic(msg) for c in candidates
                                                for msg in c.get('sanitizer', []))),
                candidate_errors=[dict(index=row['index'], result=row['result']['routes']['smart'])
                                  for row in r['cases'] if row['result']['routes']['smart']['status']
                                  in ('error','harness_error','budget')])
            if mode.startswith('sanitize-'):
                plain = reports['trace' if mode=='sanitize-default' else 'bypass']
                def numeric_result(row):
                    candidate = dict(row['result']['routes']['smart'])
                    candidate.pop('sanitizer', None)
                    return candidate
                report['campaigns'][mode]['same_as_unsanitized'] = sum(
                    numeric_result(a)==numeric_result(b) for a,b in zip(r['cases'], plain['cases']))
        if plugin == 'colorkeep':
            report['host_vs_bypass_identical_results'] = all(comparable(a)==comparable(b) for a,b in
                zip(reports['host']['cases'], reports['bypass']['cases']))
            # Empty historical corpus: retain all 300 pre-instrumentation results
            # in a scratch replay corpus, generated from the committed seeds.
            adapter = importlib.import_module('adapters.'+plugin).Adapter(options)
            directory = args.scratch/'colorkeep-neutrality-corpus'
            directory.mkdir(exist_ok=True)
            for row in reports['before']['cases']:
                case = adapter.generate(row['seed'], row['index'])
                assert sha(case['pixels']) == row['input_sha256']
                save_corpus(directory/f"{row['index']:03d}.json", adapter, case, case, row['result'],
                            {'accepted': []}, reports['before']['provenance'])
        output['plugins'][plugin] = report

    deadline = time.monotonic()+600
    Adapter = importlib.import_module('adapters.olmcolorkey').Adapter
    output['witnesses'] = []
    for bypass in (False, True):
        os.environ['OLM_COLOR_TRIAGE_BYPASS'] = '1' if bypass else '0'
        with tempfile.TemporaryDirectory(prefix='witness-build-', dir=args.scratch) as build:
            adapter = Adapter(options)
            adapter.prepare(Path(build), deadline)
            cases = []
            if bypass:
                cases.append(('gate-off-seed1-index116', adapter.generate(1, 116), None))
            else:
                for path in sorted((ROOT/'tests/fuzz_corpus/olmcolorkey').glob('*.json')):
                    case, saved = load_corpus(path, adapter)
                    cases.append((str(path.relative_to(ROOT)), case, saved['result']))
            def measure(item):
                name, case, saved = item
                with tempfile.TemporaryDirectory(prefix='witness-', dir=args.scratch) as td:
                    directory = Path(td)
                    # This API is Smart in the old framework, and defaults to
                    # the adapter's Smart oracle in F17. No Classic comparison.
                    oracle, reference = adapter.oracle(case, directory, deadline)
                    candidate, raw, guards = adapter.candidate(case, directory, 'smart', deadline)
                    assert oracle['status'] == candidate['status'] == 'ok', (oracle, candidate)
                    record = dict(name=name, bypass=bypass, geometry=case['geometry'], depth=case['depth'],
                                  input_sha256=sha(case['pixels']), aex_sha256=sha(reference),
                                  mac_sha256=sha(raw), stats=byte_stats(reference, raw, case['pixels'],
                                                                    case['depth'], case['geometry']))
                    if saved:
                        record['matches_saved_smart_hash'] = sha(raw)==saved['routes']['smart']['raw_sha256']
                    return record
            with ThreadPoolExecutor(max_workers=args.jobs) as pool:
                output['witnesses'].extend(pool.map(measure, cases))
    output['source_sha256'] = {str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in
        (ROOT/'mac/ColorKeep/ColorKeep.cpp', ROOT/'mac/OLMColorKey/OLMColorKey.cpp')}
    output['replays'] = {}
    for name in ('colorkeep', 'olmcolorkey', 'colorkeep-300'):
        path = args.scratch/f'replay-{name}.json'
        if path.exists():
            replay = json.loads(path.read_text())
            output['replays'][name] = dict(status=replay['status'],
                count=len(replay.get('replays', [])),
                matches_saved=sum(r['matches_saved'] for r in replay.get('replays', [])),
                error=replay.get('error'))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, sort_keys=True, indent=2)+'\n')
    print(json.dumps({'neutrality': {p:r['neutrality'] for p,r in output['plugins'].items()},
                      'witnesses': len(output['witnesses']), 'output': str(args.output)}))


if __name__ == '__main__':
    main()
