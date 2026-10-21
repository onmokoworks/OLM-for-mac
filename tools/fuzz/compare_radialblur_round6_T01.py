#!/usr/bin/env python3
"""Apply T01 Round-4 acceptance to two measured fuzz/replay reports.

Reads evidence only. Exact routes must retain their bytes; a mismatch may
remain a mismatch or become a refusal. Unchanged refusals/uncompared routes
are retained limitations. Any route may become exact. No corpus is rewritten.
"""
import argparse
from collections import Counter
import copy
import json
from pathlib import Path


def compare(before, after):
    replay = 'replays' in before
    key = 'replays' if replay else 'cases'
    assert before['completed'] == before['requested'] == after['completed'] == after['requested']
    for field in ['worker_sha256', 'aex_sha256', 'core_sha256', 'header_sha256']:
        assert before['provenance'][field] == after['provenance'][field], field
    counts = Counter()
    policy, forbidden, unlisted, oracle_changes = [], [], [], []
    offset = {'before': Counter(), 'after': Counter()}
    for old, new in zip(before[key], after[key]):
        identity = old['path'] if replay else old['index']
        assert identity == (new['path'] if replay else new['index'])
        if not replay:
            for field in ['input_sha256', 'parameters', 'geometry', 'depth', 'input_padding', 'output_padding']:
                assert old[field] == new[field], (identity, field)
        old_oracle, new_oracle = old['result']['oracle'], new['result']['oracle']
        if old_oracle['status'] != new_oracle['status']:
            oracle_changes.append(dict(case=identity, before=old_oracle, after=new_oracle))
        if old_oracle['status'] == new_oracle['status'] == 'ok':
            assert old_oracle['raw_sha256'] == new_oracle['raw_sha256'], identity
        for route, prev in old['result']['routes'].items():
            curr = new['result']['routes'][route]
            b, a = prev['status'], curr['status']
            counts[(route, b, a)] += 1
            allowed = (a == 'exact' or (b == 'mismatch' and a in ('mismatch', 'refusal')) or
                       (b == a and b not in ('exact', 'mismatch')))
            if b == 'exact':
                allowed = a == 'exact' and prev['raw_sha256'] == curr.get('raw_sha256')
            detail = dict(case=identity, route=route, before=prev, after=curr,
                          refusal_guards=new.get('refusal_guards', {}))
            if b == 'exact' and not allowed:
                forbidden.append(detail)
            elif not allowed:
                unlisted.append(detail)
            if b == 'mismatch' and a == 'refusal':
                policy.append(detail)
            if not replay and old['depth'] == 8 and any(p['slot'] == 6 and p['value'] != 0 for p in old['parameters']):
                offset['before'][(route, b)] += 1
                offset['after'][(route, a)] += 1
    return dict(cases=before['completed'],
                transitions=[dict(route=r, before=b, after=a, count=n)
                             for (r, b, a), n in sorted(counts.items())],
                policy=policy, forbidden=forbidden, unlisted=unlisted, oracle_changes=oracle_changes,
                pf8_outer_offset={label: [dict(route=r, status=s, count=n)
                                         for (r, s), n in sorted(values.items())]
                                  for label, values in offset.items()},
                before_source_sha256=before['provenance']['source_sha256'],
                after_source_sha256=after['provenance']['source_sha256'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before', type=Path, required=True)
    parser.add_argument('--after', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--witnesses', type=Path,
                        help='Optional longer-deadline AEX measurements, keeping original reports intact')
    args = parser.parse_args()
    before, after = (json.loads(p.read_text()) for p in (args.before, args.after))
    raw_result = compare(before, after)
    rechecks = []
    if args.witnesses:
        witnesses = json.loads(args.witnesses.read_text())
        assert witnesses['complete']
        before, after = copy.deepcopy(before), copy.deepcopy(after)
        for label, report in [('base', before), ('after', after)]:
            for field in ['source_sha256', 'worker_sha256', 'aex_sha256', 'header_sha256', 'core_sha256']:
                assert report['provenance'][field] == witnesses['provenance'][label][field]
            for witness in witnesses['rows']:
                assert report['seed'] == witnesses['seed']
                row = next(r for r in report['cases'] if r['index'] == witness['index'])
                assert row['input_sha256'] == witness['input_sha256']
                for field in ['parameters', 'geometry', 'depth', 'input_padding', 'output_padding']:
                    assert row[field] == witness[field]
                if witness['oracle']['status'] != 'ok':
                    continue
                if row['result']['oracle']['status'] == 'ok':
                    assert row['result']['oracle']['raw_sha256'] == witness['oracle']['raw_sha256']
                for route, value in row['result']['routes'].items():
                    observed = witness['results'][label][route]
                    if 'raw_sha256' in value:
                        assert value['raw_sha256'] == observed['raw_sha256']
                    if value['status'] == 'uncompared':
                        assert observed['status'] in ('exact', 'mismatch')
                        rechecks.append(dict(label=label, case=row['index'], route=route,
                                             before='uncompared', after=observed['status']))
                        value['status'] = observed['status']
                        if 'diff' in observed:
                            value['diff'] = observed['diff']
                row['result']['oracle'] = witness['oracle']
    result = compare(before, after)
    result['raw_transitions'] = raw_result['transitions']
    result['oracle_rechecks'] = rechecks
    args.report.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('policy', 'forbidden', 'unlisted', 'oracle_changes')}, sort_keys=True))
    print('FORBIDDEN', len(result['forbidden']), 'POLICY', len(result['policy']),
          'UNLISTED', len(result['unlisted']), 'ORACLE_CHANGES', len(result['oracle_changes']), flush=True)
    return 1 if result['forbidden'] or result['unlisted'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
