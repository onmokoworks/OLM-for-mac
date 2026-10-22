#!/usr/bin/env python3
"""Assemble the C07 opacity evidence, asserting monotone production results."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


def strength_evidence(read, scratch, root):
    result = dict(schema='olm-kira-C07-strength/1', campaigns={}, matrices={}, traces={},
        limitations=['CPU emulation/fake-host evidence, not native AE/UCRT.',
                     'Host float powf matches the retained worker import; it is not a Windows powf proof.'])
    for seed in (1, 5):
        a, b = (read(f'strength-campaigns/{kind}-seed{seed}') for kind in ('before', 'after'))
        assert a['status'] == b['status'] == 'complete'
        assert a['completed'] == b['completed'] == 300
        old, new = ({r['index']: r for r in report['cases']} for report in (a, b))
        changes = []
        for index in range(300):
            x, y = (r[index]['result'] for r in (old, new))
            assert x['oracles'] == y['oracles'] and x['routes']['classic'] == y['routes']['classic']
            x, y = (r['routes']['smart'] for r in (x, y))
            assert x == y or x['status'] == 'refusal' and y['status'] == 'exact'
            if x != y:
                changes.append(dict(index=index, before=x, after=y))
        result['campaigns'][str(seed)] = dict(before=a['summary'], after=b['summary'],
                                              changes=changes, provenance=b['provenance'])
    for name in ('strength-production', 'strength-combined-production'):
        report = read(name)
        assert report['status'] == 'complete' and report['counts'] == {'exact': 288}
        result['matrices'][name] = {k: v for k, v in report.items() if k != 'rows'}
        result['matrices'][name]['rows'] = [dict(index=r['index'], input_sha256=r['input_sha256'],
            reference_sha256=r['reference_sha256'], result=r['result']) for r in report['rows']]
    for name in ('strength-campaign-before-trace', 'strength-campaign-after-trace',
                 'strength-zero-trace', 'strength-zero-after-trace', 'strength-537-trace',
                 'strength-537-bound-before', 'strength-537-bound-after', 'strength-production-trace'):
        result['traces'][name] = read(name)
    for name in ('strength-after-matrix', 'strength-recovered-matrix', 'strength-combined-matrix',
                 'strength-sample-audit'):
        report = read(name)
        result[name] = {k: v for k, v in report.items() if k != 'rows'}
        result[name]['last_row'] = report['rows'][-1]
    result['sample_audit'] = read('strength-final-sample-audit')
    assert len(result['sample_audit']['rows']) == 140
    assert all(not r['changed_not_to_exact'] for r in result['sample_audit']['rows'])
    result['changed_samples_toward_exact'] = sum(r['changed_samples'] for r in result['sample_audit']['rows'])
    result['corpus'] = read('strength-production-corpus')
    assert result['corpus']['status'] == 'passed' and len(result['corpus']['corpus']) == 70
    result['sanitized_campaigns'] = read('strength-sanitized-campaigns')
    assert result['sanitized_campaigns']['status'] == 'passed'
    assert sum(r['sanitized_routes'] for r in result['sanitized_campaigns']['campaigns'].values()) == 600
    replay = read('strength-replay')
    result['replay'] = dict(total=replay['completed'], matches=sum(r['matches_saved'] for r in replay['replays']))
    assert result['replay'] == dict(total=8, matches=8)
    result['logs'] = {name: (scratch / (name + '.log')).read_text()
                      for name in ('strength-fast-tests', 'strength-sanitizer-test')}
    result['source_hashes'] = {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (root / 'mac/OLMKiraKira/OLMKiraKira.cpp',
                     root / 'tools/emulation/probe_kirakira_smart_C07.py',
                     root / 'tools/emulation/trace_kirakira_numeric_F09.py')}
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--scratch', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--cluster', choices=('opacity', 'strength'), default='opacity')
    args = p.parse_args()
    root = Path(__file__).resolve().parents[2]
    def read(name):
        return json.loads((args.scratch / (name + '.json')).read_text())
    if args.cluster == 'strength':
        result = strength_evidence(read, args.scratch, root)
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
        print('PASS', result['changed_samples_toward_exact'], 'samples toward exact; 600 sanitized campaign routes')
        return
    result = dict(schema='olm-kira-C07-opacity/1', campaigns={}, matrices={}, traces={},
                  limitations=['CPU emulation/fake-host evidence, not native AE/UCRT.',
                               'Finite matrices do not prove all inputs.'])
    for seed in (1, 5):
        before, after = (read(f'{kind}-seed{seed}') for kind in ('before', 'after'))
        assert before['status'] == after['status'] == 'complete'
        assert before['completed'] == after['completed'] == 300
        a, b = ({r['index']: r for r in report['cases']} for report in (before, after))
        changes = []
        for index in range(300):
            old, new = (x[index]['result'] for x in (a, b))
            assert old['oracles'] == new['oracles']
            assert old['routes']['classic'] == new['routes']['classic']
            x, y = (r['routes']['smart'] for r in (old, new))
            assert x == y or x['status'] == 'refusal' and y['status'] == 'exact'
            if x != y:
                changes.append(dict(index=index, before=x, after=y))
        result['campaigns'][str(seed)] = dict(before=before['summary'], after=after['summary'],
            changes=changes, provenance=after['provenance'])
    result['gate_off_before'] = read('gateoff-seed1')['summary']
    for name in ('opacity-before-matrix', 'opacity-after-matrix', 'glow-after-matrix',
                 'opacity-combined-production'):
        report = read(name)
        assert report['status'] == 'complete'
        result['matrices'][name] = {k: v for k, v in report.items() if k != 'rows'}
        result['matrices'][name]['rows'] = [dict(index=r['index'], input_sha256=r['input_sha256'],
            reference_sha256=r['reference_sha256'], result=r['result']) for r in report['rows']]
    for name in ('opacity-campaign-before-trace', 'opacity-campaign-after-trace', 'opacity-production-trace'):
        report = read(name)
        assert report['status'] == 'complete' and report['rows'][0]['public_bound']
        result['traces'][name] = report
    result['rejected_unbounded_opacity_audit'] = read('opacity-sample-audit')
    result['sample_audit'] = read('opacity-bounded-sample-audit')
    assert len(result['sample_audit']['rows']) == 140
    assert all(not r['changed_not_to_exact'] for r in result['sample_audit']['rows'])
    result['changed_samples_toward_exact'] = sum(r['changed_samples'] for r in result['sample_audit']['rows'])
    result['corpus'] = read('opacity-production-corpus')
    assert result['corpus']['status'] == 'passed' and len(result['corpus']['corpus']) == 70
    result['sanitized_campaigns'] = read('opacity-sanitized-campaigns')
    assert result['sanitized_campaigns']['status'] == 'passed'
    assert sum(r['sanitized_routes'] for r in result['sanitized_campaigns']['campaigns'].values()) == 600
    for when in ('before', 'after'):
        replay = read(f'opacity-replay-{when}-rebaseline')
        result[f'replay_{when}'] = dict(total=replay['completed'],
            matches=sum(r['matches_saved'] for r in replay['replays']))
    assert result['replay_after'] == dict(total=8, matches=8)
    result['logs'] = {name: (args.scratch / (name + '.log')).read_text()
                      for name in ('opacity-fast-tests', 'opacity-sanitizer-test', 'opacity-builder-asm')}
    result['source_hashes'] = {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (root / 'mac/OLMKiraKira/OLMKiraKira.cpp',
                     root / 'tools/emulation/probe_kirakira_smart_C07.py',
                     root / 'tools/emulation/trace_kirakira_numeric_F09.py')}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print('PASS', result['changed_samples_toward_exact'], 'changed samples; 600 sanitized campaign routes')


if __name__ == '__main__':
    main()
