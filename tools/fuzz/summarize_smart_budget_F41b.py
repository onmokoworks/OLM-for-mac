#!/usr/bin/env python3
"""Keep measured Smart transitions and provenance without copying raw frames."""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    reports = {}
    evidence = {'campaigns': {}, 'comparisons': {}}
    for path in sorted(args.state.glob('*.json')):
        report = json.loads(path.read_text())
        if 'provenance' not in report:
            continue
        reports[path.stem] = report
        record = {key: report.get(key) for key in (
            'plugin', 'seed', 'completed', 'status', 'summary', 'jobs',
            'case_timeout_seconds', 'elapsed_seconds', 'replay_matches_saved')}
        record['report_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        record['provenance'] = report['provenance']
        if 'replays' in report:
            record['saved_matches'] = sum(row['matches_saved'] for row in report['replays'])
            record['saved_total'] = len(report['replays'])
        if path.stem.startswith('retry'):
            record['cases'] = report.get('cases', [])
        evidence['campaigns'][path.stem] = record
    for prefix in ('', 'blur-', 'directional-', 'kira-', 'toon-', 'dg-'):
        for seed in (1, 41123):
            if f'{prefix}base-{seed}' not in reports:
                continue
            before = {row['index']: row for row in reports[f'{prefix}base-{seed}']['cases']}
            for phase in ('work', 'final'):
                name = f'{prefix}{phase}-{seed}'
                if name not in reports:
                    continue
                result = {'preserved_exact': 0, 'lost_exact': [], 'transitions': []}
                for row in reports[name]['cases']:
                    old = before[row['index']]
                    assert old['input_sha256'] == row['input_sha256']
                    assert old['parameters'] == row['parameters']
                    prior = old['result']['routes']['smart']
                    new = row['result']['routes']['smart']
                    if prior['status'] == 'exact':
                        if new['status'] == 'exact' and prior['raw_sha256'] == new['raw_sha256']:
                            result['preserved_exact'] += 1
                        else:
                            result['lost_exact'].append({'index': row['index'], 'before': prior, 'after': new})
                    if prior['status'] != new['status']:
                        result['transitions'].append({
                            **{key: row[key] for key in ('index', 'depth', 'geometry', 'input_sha256', 'parameters')},
                            'before': prior, 'after': new, 'oracle': row['result']['oracle']})
                evidence['comparisons'][name] = result
                print(name, 'preserved exact', result['preserved_exact'],
                      'lost exact', len(result['lost_exact']), 'transitions', len(result['transitions']))
    qualification = {'preserved_exact': 0, 'lost_exact': [],
                     'new_exact': [], 'unverified_new_outputs': []}
    for name, comparison in evidence['comparisons'].items():
        if 'final-' not in name:
            continue
        report = reports[name]
        qualification['preserved_exact'] += comparison['preserved_exact']
        qualification['lost_exact'].extend(comparison['lost_exact'])
        for transition in comparison['transitions']:
            if transition['before']['status'] != 'refusal':
                continue
            final = transition['after']
            witness = name
            if final['status'] != 'exact':
                for retry_name, retry in reports.items():
                    if not retry_name.startswith('retry') or retry.get('seed') != report.get('seed'):
                        continue
                    if retry['provenance'].get('source_sha256') != report['provenance'].get('source_sha256'):
                        continue
                    for row in retry.get('cases', []):
                        if (row['index'] == transition['index'] and
                            row['input_sha256'] == transition['input_sha256'] and
                            row['parameters'] == transition['parameters'] and
                            row['result']['routes']['smart']['status'] == 'exact'):
                            final = row['result']['routes']['smart']
                            witness = retry_name
            item = {'campaign': name, 'index': transition['index'],
                    'witness': witness, 'result': final}
            qualification['new_exact' if final['status'] == 'exact'
                          else 'unverified_new_outputs'].append(item)
    evidence['qualification'] = qualification
    print('FINAL QUALIFICATION', qualification['preserved_exact'], 'preserved;',
          len(qualification['lost_exact']), 'lost;', len(qualification['new_exact']),
          'new exact;', len(qualification['unverified_new_outputs']), 'unverified new outputs')
    args.output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + '\n')


if __name__ == '__main__':
    main()
