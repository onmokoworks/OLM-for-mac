#!/usr/bin/env python3
"""Check final campaigns against committed pre-fix exact hashes and oracle bindings."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
scratch = ROOT / 'orchestra/state/C42-colorkey-pf32-nan-mismatch'
evidence = ROOT / 'orchestra/reports/C42-evidence'
baseline = json.loads((evidence/'baseline.json').read_text())
summary = {'campaigns': {}, 'retained_exact_routes': 0}
for seed, before in baseline['campaigns'].items():
    report = json.loads((scratch/f'final{seed}.json').read_text())
    assert report['status'] == 'complete' and report['completed'] == 300
    assert report['summary']['smart_exact'] == 300
    rows = sorted(report['cases'], key=lambda r: r['index'])
    bindings = [[r['index'], r['input_sha256'], r['result']['oracles']] for r in rows]
    assert hashlib.sha256(json.dumps(bindings, sort_keys=True).encode()).hexdigest() == before['bindings_sha256']
    by_index = {r['index']: r for r in rows}
    for index, route, digest in before['exact']:
        result = by_index[index]['result']['routes'][route]
        assert result['status'] == 'exact' and result['raw_sha256'] == digest
    summary['retained_exact_routes'] += len(before['exact'])
    summary['campaigns'][seed] = {'before': before['summary'], 'after': report['summary'],
        'exact_hashes_retained': len(before['exact']), 'oracle_and_input_bindings_unchanged': True}
boundaries = json.loads((scratch/'boundaries.json').read_text())
assert len(boundaries['cases']) == 16
assert all(r['oracle']['status'] == r['candidate']['status'] == 'ok' and
           r['diff']['different_words'] == 0 for r in boundaries['cases'])
replay = json.loads((scratch/'replay-final.json').read_text())
assert replay['replay_matches_saved'] and replay['completed'] == 9
summary.update(boundaries_exact=16, corpus_matches_saved=9)
(scratch/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
print(json.dumps(summary, indent=2))
