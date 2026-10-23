#!/usr/bin/env python3
"""Retain compact C30 measurements, hashes and every changed regression row."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct


def angle_summary(args):
    names = ('angle-builder', 'angle-matrix', 'angle-verify', 'angle-rebaseline',
             'angle-after', 'angle-replay', 'seed6-stages', 'angle-stages')
    reports = {n: json.loads((args.scratch/(n+'.json')).read_text()) for n in names}
    result = {'report_sha256': {n: hashlib.sha256((args.scratch/(n+'.json')).read_bytes()).hexdigest()
                              for n in names}, 'builder': reports['angle-builder']}
    assert not result['builder']['candidate_mismatches']
    matrix = reports['angle-matrix']
    assert len(matrix['cases']) == 294
    result['matrix'] = {k: v for k, v in matrix.items() if k != 'cases'}
    result['matrix']['cases'] = []
    for c in matrix['cases']:
        assert all(r['exact'] and r['sanitizer_same'] for r in c['routes'].values())
        result['matrix']['cases'].append({k: v for k, v in c.items() if k != 'parameters'})
    verify = reports['angle-verify']
    groups, changes, preserved = {}, [], 0
    assert len(verify['cases']) == 656
    for c in verify['cases']:
        group = c['name'].split(':')[0] if c['name'].startswith('seed') else 'corpus'
        counts = groups.setdefault(group, {'before': Counter(), 'after': Counter()})
        b, a = c['before']['smart'], c['after']['routes']['smart']
        counts['before'][b['status']] += 1
        counts['after'][a['status']] += 1
        assert c['sanitizer_same']
        if b['status'] == 'exact':
            assert a['status'] == 'exact' and b['raw_sha256'] == a['raw_sha256']
            preserved += 1
        if b.get('raw_sha256') != a.get('raw_sha256'):
            assert a['status'] == 'exact'
            changes.append(c)
    result['verify'] = {k: v for k, v in verify.items() if k != 'cases'}
    result['verify'].update(groups=groups, changes=changes, base_exact_preserved=preserved)
    assert reports['angle-replay']['completed'] == 56 and reports['angle-replay']['replay_matches_saved']
    assert len(reports['angle-rebaseline']['cases']) == 56
    result['replay'] = {'completed': 56, 'matches_saved': 56}
    result['after'] = {k: reports['angle-after'][k] for k in ('completed','summary','provenance')}
    assert result['after']['completed'] == 300
    for name in ('seed6-stages', 'angle-stages'):
        r = reports[name]
        for c in r['cases']:
            assert c['fixture_session']['different_units'] == 0
            for s in c['stages'].values():
                s.pop('aex_hex', None); s.pop('mac_hex', None)
        result[name] = r
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print(json.dumps(groups, sort_keys=True))
    print('PASS angle: preserved', preserved, 'improved', len(changes))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--scratch', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--angles', action='store_true')
    args = p.parse_args()
    if args.angles:
        angle_summary(args)
        return
    names = ('baseline', 'gate', 'matrix-gate', 'matrix-production', 'verify',
             'after', 'replay', 'nonfinite', 'nonfinite-stages')
    reports = {n: json.loads((args.scratch/(n+'.json')).read_text()) for n in names}
    evidence = {'base': reports['verify']['baseline'], 'report_sha256': {
        n: hashlib.sha256((args.scratch/(n+'.json')).read_bytes()).hexdigest() for n in names}}
    for n in ('baseline', 'after'):
        r = reports[n]
        assert r['completed'] == 300 and r['status'] == 'complete'
        evidence[n] = {k: r[k] for k in ('summary', 'provenance')}
        evidence[n]['smart_residuals'] = [c for c in r['cases']
            if c['result']['routes']['smart']['status'] != 'exact']
    gate = reports['gate']
    changes = [c for c in gate['cases'] if c['changed']]
    assert len(gate['cases']) == 600 and all(c['sanitizer_same'] for c in gate['cases'])
    assert all(c['exact'] for c in changes)
    evidence['gate'] = {'cases': len(gate['cases']), 'changes': changes,
                        'builds': gate['builds'], 'commands': gate['commands']}
    for n in ('matrix-gate', 'matrix-production'):
        r = reports[n]
        assert len(r['cases']) == 576
        assert all(v['sanitizer_same'] and v['exact_smart_reference']
                   for c in r['cases'] for v in c['routes'].values())
        evidence[n] = {'cases': len(r['cases']), 'families': r['families'],
            'builds': r['builds'], 'commands': r['commands'],
            'source_sha256': r['source_sha256']}
    verify = reports['verify']
    assert len(verify['cases']) == 656
    groups, changes = {}, []
    preserved = 0
    for c in verify['cases']:
        group = c['name'].split(':')[0] if c['name'].startswith('seed') else 'corpus'
        counts = groups.setdefault(group, {'before': Counter(), 'after': Counter(),
                                          'transitions': Counter()})
        b, a = c['before']['smart'], c['after']['routes']['smart']
        counts['before'][b['status']] += 1
        counts['after'][a['status']] += 1
        counts['transitions'][b['status']+' -> '+a['status']] += 1
        assert c['sanitizer_same']
        if b['status'] == 'exact':
            assert a['status'] == 'exact' and b['raw_sha256'] == a['raw_sha256']
            preserved += 1
        if b.get('raw_sha256') != a.get('raw_sha256'):
            assert a['status'] == 'exact'
            changes.append(c)
    evidence['verify'] = {'cases': len(verify['cases']), 'groups': groups,
        'base_exact_preserved': preserved, 'changes': changes,
        'retained_mismatches': [c for c in verify['cases']
            if c['after']['routes']['smart']['status'] == 'mismatch'],
        'builds': verify['builds'], 'commands': verify['commands'],
        'source_sha256': verify['source_sha256']}
    replay = reports['replay']
    assert replay['completed'] == 56 and replay['replay_matches_saved']
    evidence['replay'] = {'completed': 56, 'matches_saved': 56}
    evidence['nonfinite'] = reports['nonfinite']
    stages = reports['nonfinite-stages']
    for c in stages['cases']:
        for s in c['stages'].values():
            if 'aex_hex' in s:
                a, b = bytes.fromhex(s.pop('aex_hex')), bytes.fromhex(s.pop('mac_hex'))
                s['nan_sign_only_words'] = sum(x ^ y == 0x80000000 and
                    (x & 0x7fffffff) > 0x7f800000 for (x,), (y,) in zip(
                        struct.iter_unpack('<I', a), struct.iter_unpack('<I', b)))
    evidence['nonfinite-stages'] = stages
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, indent=2, sort_keys=True)+'\n')
    print(json.dumps(groups, sort_keys=True))
    print('PASS: base-exact preserved', preserved, 'changed toward exact', len(changes))


if __name__ == '__main__':
    main()
