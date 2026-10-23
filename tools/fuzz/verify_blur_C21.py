#!/usr/bin/env python3
"""Verify monotonic C21 campaigns and corpus; retain complete result evidence."""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import sys
sys.dont_write_bytecode = True
from run import ROOT
from verify_blur_retained_C12 import verify
from verify_blur_smart_C05 import retained


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--scratch', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--before', required=True)
    p.add_argument('--after', required=True)
    p.add_argument('--rebaseline', action='store_true')
    p.add_argument('--matrix', nargs='+', required=True)
    p.add_argument('--trace', required=True)
    args = p.parse_args()
    s = args.scratch.resolve()
    assert s.is_relative_to(ROOT/'orchestra/state/C21-olmblur-smart-r5')
    os.environ.update(TMPDIR=str(s), TMP=str(s), TEMP=str(s))
    load = lambda name: json.loads((s/(name+'.json')).read_text())
    report = {'before': args.before, 'after': args.after, 'campaigns': {}}
    for seed in (1, 7):
        b, a, z = [load(f'{label}-seed{seed}') for label in
                   (args.before, args.after, args.after+'-san')]
        assert all(r['completed'] == 300 and r['jobs'] == 1 for r in (b, a, z))
        transitions = Counter()
        for old, new, san in zip(b['cases'], a['cases'], z['cases']):
            assert old['input_sha256'] == new['input_sha256'] == san['input_sha256']
            assert new['result'] == san['result'], (seed, new['index'], 'sanitizer drift')
            assert old['result']['oracles'] == new['result']['oracles']
            assert old['result']['routes']['classic'] == new['result']['routes']['classic']
            br, ar = [r['result']['routes']['smart'] for r in (old, new)]
            transitions[br['status']+' -> '+ar['status']] += 1
            assert ar['status'] in ('exact', 'mismatch', 'refusal')
            if br != ar:
                assert br['status'] in ('mismatch', 'refusal') and ar['status'] == 'exact', (seed, new['index'], br, ar)
        report['campaigns'][str(seed)] = {'before': b, 'after': a, 'sanitized': z, 'transitions': dict(transitions)}
    b, a = [load(label+'-replay') for label in (args.before, args.after)]
    assert b['completed'] == a['completed'] == 39
    report['corpus'] = {'before': b, 'after': a}
    transitions = Counter()
    updates = []
    for old, new in zip(b['replays'], a['replays']):
        assert old['path'] == new['path']
        assert old['result']['oracles'] == new['result']['oracles']
        assert old['result']['routes']['classic'] == new['result']['routes']['classic']
        br, ar = [r['result']['routes']['smart'] for r in (old, new)]
        transitions[br['status']+' -> '+ar['status']] += 1
        if old['result'] != new['result']:
            assert br['status'] in ('mismatch', 'refusal') and ar['status'] == 'exact'
            path = Path(new['path'])
            assert path.resolve().is_relative_to(ROOT/'tests/fuzz_corpus/olmblur')
            saved = json.loads(path.read_text())
            if saved['result'] != new['result']:
                assert saved['result'] == old['result']
                saved.setdefault('C21_updates', []).append({'stage': args.after, 'previous_result': saved['result']})
                saved['result'] = new['result']
                updates.append((path, saved))
    report['corpus']['transitions'] = dict(transitions)
    report['matrices'] = {name: load(name) for name in args.matrix}
    for matrix in report['matrices'].values():
        assert len(matrix['rows']) == 720
        assert all(row['after']['status'] == 'exact' for row in matrix['rows'])
        assert all(row['before']['status'] in ('exact', 'mismatch') for row in matrix['rows'])
    report['trace'] = load(args.trace)
    assert all(row['cached_binding'] and row['output_exact'] and row['first_difference'] is None
               for row in report['trace']['rows'])
    report['retained'] = retained(s)
    report['extended_retained'] = verify(s)
    assert report['extended_retained']['status']['status'] == 'ok'
    assert len(report['extended_retained']['lines']) == 80
    assert all('exact=1' in x for x in report['extended_retained']['lines'])
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    if args.rebaseline:
        for path, saved in updates:
            path.write_text(json.dumps(saved, indent=2, sort_keys=True)+'\n')
    print({seed: row['transitions'] for seed, row in report['campaigns'].items()})
    print('corpus', dict(transitions), 'updates', len(updates), 'retained', len(report['retained']['lines']), '+ 80')


if __name__ == '__main__':
    main()
