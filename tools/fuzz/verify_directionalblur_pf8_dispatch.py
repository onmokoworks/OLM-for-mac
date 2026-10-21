#!/usr/bin/env python3
"""Validate committed F06 evidence, corpus updates and production bindings."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT/'reports/fuzz/f06_dblur_pf8_dispatch'


def read(name):
    return json.loads((EVIDENCE/name).read_text())


def main():
    before, after = read('before.json'), read('after.json')
    assert before['completed'] == after['completed'] == 300
    for path, expected in after['provenance']['dependencies_sha256'].items():
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == expected, path
    for route in ('classic','smart'):
        assert before['summary'][route+'_exact'] == 228
        assert after['summary'][route+'_exact'] == 235
        transitions = {}
        for a,b in zip(before['cases'],after['cases']):
            assert a['index']==b['index'] and a['input_sha256']==b['input_sha256']
            assert a['result']['oracle']==b['result']['oracle']
            x,y = a['result']['routes'][route],b['result']['routes'][route]
            key = x['status']+' -> '+y['status']
            transitions[key] = transitions.get(key,0)+1
            if x.get('raw_sha256')!=y.get('raw_sha256') and y['status']!='refusal':
                assert y['status']=='exact'
        assert transitions == {'exact -> exact':227,'exact -> refusal':1,
            'mismatch -> exact':8,'mismatch -> mismatch':23,'mismatch -> refusal':25,
            'refusal -> refusal':14,'uncompared -> uncompared':2}
    corpus = read('corpus.json')['cases']
    assert len(corpus)==56
    changed = 0
    for row in corpus:
        assert row['sanitizer_same'] and row['gate_off']==row['sanitized']
        assert row['before']['oracle']==row['gate_off']['oracle']
        assert json.loads((ROOT/row['path']).read_text())['result']==row['gate_off']
        if row['before']!=row['gate_off']:
            changed += 1
            assert all(r['status']=='exact' for r in row['gate_off']['routes'].values())
    assert changed==37
    for name in ('gate_campaign.json','production_campaign.json'):
        rows = read(name)['cases']
        assert len(rows)==300 and all(r['sanitizer_same'] for r in rows)
    trace = read('trace.json')['cases']
    assert {r['cluster'] for r in trace} == {4,5,6,7,16,17}
    assert all(r['paired_writer_exact'] for r in trace)
    replay = read('replay.json')
    assert replay['completed']==56 and all(r['matches_saved'] for r in replay['replays'])
    print('PASS: six targets; corpus 37 improved/19 unchanged; 228 -> 235 exact per route; sanitizer 356/356; replay 56/56')


if __name__ == '__main__': main()
