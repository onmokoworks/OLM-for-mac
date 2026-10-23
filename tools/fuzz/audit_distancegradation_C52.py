#!/usr/bin/env python3
"""Attribute DG residuals to the public route that failed; audit retained evidence."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'orchestra/reports/C52-evidence'


def read(path):
    data = path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix == '.gz' else data)


def census(report):
    counts = Counter()
    residuals = []
    for row in report['cases']:
        result = row.get('result', {})
        mac = result.get('routes', {}).get('smart', {})
        oracle = result.get('oracles', {}).get('smart', {})
        pair = mac.get('status', 'framework_error'), oracle.get('status', 'missing')
        counts[' / '.join(pair)] += 1
        if pair != ('exact', 'ok'):
            residuals.append(dict(index=row['index'], mac=mac, oracle=oracle,
                                  geometry=row.get('geometry'), depth=row.get('depth'),
                                  profile=row.get('profile'), parameters=row.get('parameters')))
    return dict(completed=report['completed'], counts=dict(sorted(counts.items())), residuals=residuals)


def compare(before, after):
    old = {r['index']: r for r in before['cases']}
    changes, lost = [], []
    preserved = 0
    for row in after['cases']:
        prior = old[row['index']]
        if 'depth' not in prior:
            continue
        for key in ('input_sha256', 'geometry', 'depth', 'parameters', 'input_padding', 'output_padding', 'profile'):
            assert prior[key] == row[key], (row['index'], key)
        a = prior['result']['routes']['smart']
        b = row['result']['routes']['smart']
        if a['status'] == 'exact':
            if b['status'] == 'exact':
                assert a['raw_sha256'] == b['raw_sha256'], row['index']
                preserved += 1
            else:
                lost.append(dict(index=row['index'], status=b['status']))
        if a['status'] != b['status']:
            changes.append([row['index'], a['status'], b['status']])
    return dict(preserved_exact=preserved, unconfirmed_previous_exact=lost, transitions=changes)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--campaign', type=Path, action='append', default=[])
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    historical = {}
    for seed in range(101, 106):
        path = ROOT / f'orchestra/reports/S01-wide-mismatch-sweep/olmdistancegradation_seed{seed}.json.gz'
        data = read(path)
        if seed == 105:
            retry = read(path.with_name('olmdistancegradation_seed105_retry.json'))
            rows = {r['index']: r for r in data['cases']}
            rows.update({r['index']: r for r in retry['cases']})
            data['cases'] = list(rows.values())
        historical[str(seed)] = census(data)
    output = dict(historical=historical, campaigns={})
    paths = args.campaign
    if not paths:
        manifest = read(EVIDENCE / 'manifest.json')
        for name, digest in manifest.items():
            assert hashlib.sha256((EVIDENCE / name).read_bytes()).hexdigest() == digest, name
        paths = sorted(EVIDENCE.glob('seed*.json.gz'))
    if not args.campaign:
        for name in ('scalar', 'scalar-linear', 'power', 'box'):
            path = EVIDENCE / (name+'.json.gz')
            if path.exists():
                data = read(path)
                assert data['completed'] and data['rows'], name
                assert all(r['exact'] and r['sanitized_equal'] for r in data['rows']), name
        for path in EVIDENCE.glob('*-negative.json.gz'):
            data = read(path)
            assert data['completed']
            assert all(r['candidate']['status']=='refusal' and r['sanitized_equal'] for r in data['rows'])
        for path in EVIDENCE.glob('*-verify.json.gz'):
            data = read(path)
            assert data['completed']
            for group in data['campaigns']:
                assert all(r['sanitized_equal'] and (not r['changed'] or r['after_exact']) and
                           (not r['before_exact'] or r['after_exact']) for r in group['rows'])
            assert len(data['corpus']) == 147
            assert all(r['after_exact'] and not r['changed'] and r['sanitized_equal'] for r in data['corpus'])
        corpus = read(EVIDENCE/'corpus-before.json.gz')
        assert corpus['completed']==147 and corpus['replay_matches_saved']
    for path in paths:
        data = read(path)
        baseline = ROOT / ('orchestra/reports/C47-evidence/seed1.json.gz' if data['seed'] == 1 else
                           f'orchestra/reports/S01-wide-mismatch-sweep/olmdistancegradation_seed{data["seed"]}.json.gz')
        output['campaigns'][str(data['seed'])] = dict(census=census(data), comparison=compare(read(baseline), data))
    if args.output:
        args.output.write_text(json.dumps(output, indent=2, sort_keys=True)+'\n')
    print(json.dumps({section: {seed: (item['counts'] if section == 'historical' else
          dict(counts=item['census']['counts'], comparison=item['comparison'])) for seed, item in values.items()}
          for section, values in output.items()}, indent=2))


if __name__ == '__main__':
    main()
