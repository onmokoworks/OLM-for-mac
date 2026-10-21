#!/usr/bin/env python3
"""Assert monotonic C06 Smart transitions and compact the measured evidence."""
import argparse
from collections import Counter
import json
from pathlib import Path


def compare(before, after, key):
    assert before.keys() == after.keys()
    rows = []
    transitions = Counter()
    refusal_error_changes = []
    for identity, left in before.items():
        right = after[identity]
        a, b = left['result']['routes']['smart'], right['result']['routes']['smart']
        # A changed rendered result must become exact. Refusal diagnostics can
        # move when source lines change; numerical status/hash/error cannot.
        same = all(a.get(k) == b.get(k) for k in ('status', 'raw_sha256', 'error'))
        if key == 'cases' and a['status'] == b['status'] == 'refusal':
            if a.get('error') != b.get('error'):
                refusal_error_changes.append(dict(identity=identity, before=a.get('error'), after=b.get('error')))
            same = True
        assert same or b['status'] == 'exact', (identity, a, b)
        if a['status'] == 'exact':
            assert b['status'] == 'exact' and a['raw_sha256'] == b['raw_sha256'], identity
        if b['status'] == 'exact':
            oracle = right['result']['oracles']['smart']
            assert oracle['status'] == 'ok' and oracle['raw_sha256'] == b['raw_sha256']
        transitions[a['status'] + '->' + b['status']] += 1
        rows.append(dict(identity=identity, input_sha256=left.get('input_sha256'),
                         before=a, after=b, oracle=right['result']['oracles']['smart'],
                         before_guards=left.get('refusal_guards', {}).get('smart', [])))
    return dict(kind=key, transitions=dict(transitions), refusal_error_changes=refusal_error_changes, rows=rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--before', type=Path, action='append', required=True)
    ap.add_argument('--after', type=Path, action='append', required=True)
    ap.add_argument('--sanitizer', type=Path)
    ap.add_argument('--smoke', type=Path)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    assert len(args.before) == len(args.after)
    report = dict(comparisons=[])
    for bp, apath in zip(args.before, args.after):
        b, a = json.loads(bp.read_text()), json.loads(apath.read_text())
        assert b['completed'] == b['requested'] and a['completed'] == a['requested']
        replay = 'replays' in b
        key, ident = ('replays', 'path') if replay else ('cases', 'index')
        result = compare({r[ident]: r for r in b[key]}, {r[ident]: r for r in a[key]}, key)
        result.update(before_path=str(bp), after_path=str(apath), seed=b.get('seed'),
                      before_summary=b.get('summary'), after_summary=a.get('summary'),
                      before_provenance=b['provenance'], after_provenance=a['provenance'])
        report['comparisons'].append(result)
        print('COMPARISON', b.get('seed'), key, result['transitions'])
    for name in ('sanitizer', 'smoke'):
        path = getattr(args, name)
        if path:
            data = json.loads(path.read_text())
            assert data['status'] == 'pass', data['failures']
            report[name] = data
    report['status'] = 'pass'
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
