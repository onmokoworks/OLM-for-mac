#!/usr/bin/env python3
"""Fast audit of committed C18 demand-admission evidence and final source bindings."""
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT/'reports/fuzz/c18_dblur_smart'


def read(name): return json.loads((D/name).read_text())


def main():
    manifests = []
    for prefix in ('demand', 'pf16', 'pf32'):
        path = D/f'{prefix}-verify.json'
        if not path.exists(): continue
        regression = read(path.name)
        assert len(regression['cases']) == 656
        changed = []
        for row in regression['cases']:
            before, after = row['before'], row['after']['routes']
            for route in ('classic', 'smart'):
                assert {k:v for k,v in after[route].items() if k != 'diff'} == row['sanitized'][route]
            b, a = before['smart'], after['smart']
            if b['status'] == 'exact':
                assert a['status'] == 'exact' and a['raw_sha256'] == b['raw_sha256']
            if b.get('raw_sha256') != a.get('raw_sha256'):
                assert b['status'] == 'refusal' and a['status'] == 'exact'
                changed.append(row['name'])
            if row['name'].startswith('tests/'):
                for route in ('classic', 'smart'):
                    assert before[route] == {k:v for k,v in after[route].items() if k != 'diff'}
        matrix = read(f'{prefix}-matrix.json')
        assert len(matrix['cases']) == 192
        for row in matrix['cases']:
            for route in ('classic', 'smart'):
                result = row['routes'][route]
                assert result['sanitizer_same']
                assert result['after']['status'] == 'refusal' or result['exact']
        counts = Counter(row['routes']['smart']['after']['status'] for row in matrix['cases'])
        print(prefix, 'PASS656; matrix', dict(counts), 'new', ','.join(changed))
        manifests.append(regression['source_sha256'])
    assert manifests
    for relative, expected in manifests[-1].items():
        assert hashlib.sha256((ROOT/relative).read_bytes()).hexdigest() == expected, relative
    trace = read('sampling.json')
    assert {row['index']: row['invalid_sampled_cells'] for row in trace['cases']} == {
        167: [], 183: [], 222: [], 246: [53,102,119,167]}
    for row in trace['cases']:
        assert row['original_fixture_vs_session']['different_units'] == 0
        assert row['padding_output_delta']['different_units'] == 0
    print('PASS final source bindings, base-exact preservation, sanitizer equality, corpus56 unchanged, original sampling boundaries')


if __name__ == '__main__': main()
