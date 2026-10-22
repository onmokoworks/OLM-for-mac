#!/usr/bin/env python3
"""Audit committed C09 measurements; this is not a substitute for live AEX replay."""
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'reports/fuzz/c09_dblur_smart'


def read(name):
    return json.loads((DATA/f'{name}.json').read_text())


def main():
    previous=read('before')
    assert previous['completed']==300
    for phase,expected in (('noise',269),('back',273),('zero',275)):
        if not (DATA/f'{phase}-verify.json').exists(): break
        current=read(f'{phase}-after')
        assert current['completed']==300
        assert current['summary']['smart_exact']==expected
        improvements=[]
        for old,new in zip(previous['cases'],current['cases']):
            assert old['index']==new['index'] and old['input_sha256']==new['input_sha256']
            assert old['parameters']==new['parameters']
            b,a=old['result']['routes']['smart'],new['result']['routes']['smart']
            if b['status']=='exact':
                assert a['status']=='exact' and b['raw_sha256']==a['raw_sha256']
            if b.get('raw_sha256')!=a.get('raw_sha256'):
                assert b['status']=='refusal' and a['status']=='exact'
                improvements.append(new['index'])
            bo,ao=old['result']['oracles']['smart'],new['result']['oracles']['smart']
            if bo['status']==ao['status']=='ok': assert bo['raw_sha256']==ao['raw_sha256']
        verification=read(f'{phase}-verify')
        assert len(verification['cases'])==956
        corpus=0
        for row in verification['cases']:
            assert row['sanitizer_same']
            for route in ('classic','smart'):
                observed={k:v for k,v in row['after']['routes'][route].items() if k!='diff'}
                assert observed==row['sanitized'][route]
            b,a=row['before']['smart'],row['after']['routes']['smart']
            if b['status']=='exact': assert a['status']=='exact' and b['raw_sha256']==a['raw_sha256']
            if b.get('raw_sha256')!=a.get('raw_sha256'):
                assert b['status']=='refusal' and a['status']=='exact'
            if row['name'].startswith('tests/'):
                corpus+=1
                assert json.loads((ROOT/row['name']).read_text())['result']==row['after']
        assert corpus==56
        matrix=read(f'matrix-{phase}-production')
        assert len(matrix['cases'])==(192 if phase=='noise' else 128)
        for row in matrix['cases']:
            for route in ('classic','smart'):
                assert row['routes'][route]['sanitizer_same']
                assert row['routes'][route]['exact_smart_reference']
        print(phase,dict(Counter(r['result']['routes']['smart']['status'] for r in current['cases'])),
              'improved',improvements,'956 sanitizer/base comparisons; corpus unchanged')
        previous=current
    for path,digest in verification['source_sha256'].items():
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,path
    gate=read('gate')
    assert len(gate['cases'])==900 and all(r['sanitizer_same'] for r in gate['cases'])
    assert [(r['seed'],r['index']) for r in gate['cases'] if r.get('exact') is False]==[(1,200),(2,152)]
    matrix=read('matrix-gate-all')
    assert len(matrix['cases'])==576
    assert [r['name'] for r in matrix['cases'] if not r['routes']['smart']['exact_smart_reference']]==['fade-only:19','fade-only:51']
    for name in ('seed2-152','fade-only19'):
        double=read(f'{name}-double-round')['cases'][0]
        native=read(f'{name}-native-f32')['cases'][0]
        assert double['fixture_session']['different_units']==1
        assert native['fixture_session']['different_units']==0
        assert all(s['different_units']==0 for s in double['stages'].values())
        assert native['final']['different_units']==1
        assert native['trace']['abi_leaf_instructions']>0
    for name in ('seed1-sizefade-stages','back-zero-stages'):
        if not (DATA/f'{name}.json').exists(): continue
        for row in read(name)['cases']:
            assert row['fixture_session']['different_units']==row['final']['different_units']==0
    if (DATA/'seed1-84-native-f32.json').exists():
        double=read('seed1-84-double-round')['cases'][0]
        native=read('seed1-84-native-f32')['cases'][0]
        assert double['fixture_session']['different_units']==2
        assert native['fixture_session']['different_units']==0
        assert double['stages']['weights-752']['different_units']==0
        assert native['stages']['weights-752']['different_units']==8
    if (DATA/'refusals.json').exists():
        refusals=read('refusals')['cases']
        assert len(refusals)==4
        assert all(r['status']=='refusal' for case in refusals for r in case['routes'].values())
    if (DATA/'final-replay.json').exists():
        replay=read('final-replay')
        assert replay['completed']==56 and replay['replay_matches_saved']
    print('PASS: current source bindings, measured admission, sanitizer equality, corpus preservation and import boundaries')


if __name__=='__main__':main()
