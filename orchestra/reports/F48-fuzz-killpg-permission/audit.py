"""Audit the F48 campaign against the saved S01 run (read-only)."""
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name('campaign.json.gz')
raw = gzip.decompress(path.read_bytes()) if path.suffix == '.gz' else path.read_bytes()
current = json.loads(raw)
prior = json.loads(gzip.decompress((ROOT/'orchestra/reports/S01-wide-mismatch-sweep/olmdistancegradation_seed105.json.gz').read_bytes()))
assert current['completed'] == 300 and current['status'] == 'complete'
assert [r['index'] for r in current['cases']] == list(range(300))
assert all('result' in r and 'worker_error' not in r for r in current['cases'])


def outcomes(row):
    r = row['result']
    return {'oracle': r['oracle'], **{'aex_'+k:v for k,v in r.get('oracles', {}).items()},
            **r['routes']}


classification_changes, hash_changes = [], []
same = shared_hashes = 0
for old, new in zip(prior['cases'], current['cases']):
    if 'result' not in old:
        continue
    before, after = outcomes(old), outcomes(new)
    a = {k:v['status'] for k,v in before.items()}
    b = {k:v['status'] for k,v in after.items()}
    if a == b:
        same += 1
    else:
        classification_changes.append({'index': new['index'], 'before': a, 'after': b})
    for k in before:
        if 'raw_sha256' in before[k] and 'raw_sha256' in after[k]:
            shared_hashes += 1
            if before[k]['raw_sha256'] != after[k]['raw_sha256']:
                hash_changes.append({'index': new['index'], 'route': k})
first = next({'index': r['index'], 'route': k, 'diff': v['diff']}
             for r in current['cases'] for k,v in r['result']['routes'].items()
             if v['status'] == 'mismatch')
print(json.dumps({'campaign_sha256': hashlib.sha256(raw).hexdigest(),
                  'completed': current['completed'], 'summary': current['summary'],
                  'elapsed_seconds': current['elapsed_seconds'],
                  'worker_sha256': current['provenance']['worker_sha256'],
                  'aex_sha256': current['provenance']['aex_sha256'],
                  'dependencies_unchanged': prior['provenance']['dependencies_sha256'] == current['provenance']['dependencies_sha256'],
                  'dependency_changes': {k: {'before': prior['provenance']['dependencies_sha256'].get(k),
                                             'after': current['provenance']['dependencies_sha256'].get(k)}
                      for k in prior['provenance']['dependencies_sha256'].keys() | current['provenance']['dependencies_sha256'].keys()
                      if prior['provenance']['dependencies_sha256'].get(k) != current['provenance']['dependencies_sha256'].get(k)},
                  'matching_classifications': same, 'classification_changes': classification_changes,
                  'shared_raw_hashes': shared_hashes, 'raw_hash_changes': hash_changes,
                  'recovered_rows': {str(i): {k:v['status'] for k,v in outcomes(current['cases'][i]).items()} for i in (50,123)},
                  'first_mismatch': first}, indent=2, sort_keys=True))
assert not hash_changes
