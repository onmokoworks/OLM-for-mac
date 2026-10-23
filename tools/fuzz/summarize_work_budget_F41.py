#!/usr/bin/env python3
"""Compact F41 campaign evidence; retain failures and oracle budgets explicitly."""
import argparse
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    evidence = {'campaigns': {}, 'comparisons': {}}
    reports = {}
    for path in sorted(args.state.glob('*.json')):
        report = json.loads(path.read_text())
        if 'provenance' not in report:
            continue
        reports[path.stem] = report
        record = {key: report.get(key) for key in (
            'plugin', 'seed', 'completed', 'status', 'summary', 'elapsed_seconds',
            'jobs', 'case_timeout_seconds', 'replay_matches_saved')}
        record['provenance'] = {key: value for key, value in report['provenance'].items()
            if key.endswith('_sha256') or key in ('worker_path', 'aex_path', 'compiler',
                'oracle_routes', 'original_routes', 'host', 'candidate_bypass')}
        record['report_sha256'] = sha(path)
        record['oracle_non_ok'] = [
            {'index': row['index'], 'route': route, 'oracle': oracle}
            for row in report.get('cases', [])
            for route, oracle in row.get('result', {}).get('oracles', {}).items()
            if oracle['status'] != 'ok']
        if 'replays' in report:
            record['saved_matches'] = sum(r['matches_saved'] for r in report['replays'])
            record['saved_total'] = len(report['replays'])
        evidence['campaigns'][path.stem] = record
    for seed in (1, 41023):
        before = reports[f'base-radialblur-{seed}']
        after = reports[f'work-radialblur-{seed}']
        old_rows = {r['index']: r for r in before['cases']}
        comparison = {'transitions': [], 'lost_exact': [], 'preserved_exact': 0}
        for row in after['cases']:
            old = old_rows[row['index']]
            assert old['input_sha256'] == row['input_sha256']
            assert old['parameters'] == row['parameters']
            for route, new in row['result']['routes'].items():
                prior = old['result']['routes'][route]
                if prior['status'] == 'exact':
                    preserved = (new['status'] == 'exact' and
                        prior['raw_sha256'] == new['raw_sha256'])
                    if preserved:
                        comparison['preserved_exact'] += 1
                    else:
                        comparison['lost_exact'].append({'index': row['index'], 'route': route,
                            'before': prior, 'after': new})
                if prior['status'] != new['status']:
                    comparison['transitions'].append({'index': row['index'], 'route': route,
                        'depth': row['depth'], 'geometry': row['geometry'],
                        'input_sha256': row['input_sha256'], 'parameters': row['parameters'],
                        'before': prior, 'after': new,
                        'oracle': row['result']['oracles'][route]})
        evidence['comparisons'][str(seed)] = comparison
    args.output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + '\n')
    for seed, result in evidence['comparisons'].items():
        print(seed, 'preserved exact:', result['preserved_exact'],
            'lost exact:', len(result['lost_exact']), 'transitions:', len(result['transitions']))


if __name__ == '__main__':
    main()
