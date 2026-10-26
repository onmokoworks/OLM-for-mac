#!/usr/bin/env python3
"""Collect measured evidence without changing saved corpus expectations."""
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[3]
SCRATCH = ROOT / 'orchestra/state/N02-olmkirakira-nightly-20261025'
DEST = Path(__file__).resolve().parent
summary = {'campaigns': {}, 'replays': {}, 'traces': {}, 'witnesses_before': {}, 'sources': {}}

for file in sorted(SCRATCH.glob('*.json')):
    data = json.loads(file.read_text())
    if isinstance(data, dict) and data.get('cases'):
        counts = {route: Counter() for route in ('classic', 'smart')}
        first = {}
        for row in data['cases']:
            for route in counts:
                result = row['result']['routes'][route]
                oracle = row['result']['oracles'][route]
                status = result['status'] if oracle['status'] == 'ok' else 'oracle_unavailable'
                counts[route][status] += 1
                if status in ('mismatch', 'refusal') and route not in first:
                    first[route] = {'index': row['index'], 'result': result}
        summary['campaigns'][file.stem] = dict(completed=data['completed'],
            counts={route: dict(value) for route, value in counts.items()}, first_failure=first)
    if file.stem.startswith('replay-') and 'replays' in data:
        summary['replays'][file.stem] = dict(completed=data.get('completed'),
            matches_saved=data.get('replay_matches_saved'))
    if file.stem.startswith('trace-') and 'rows' in data:
        row = data['rows'][0]
        summary['traces'][file.stem] = {key: row[key] for key in (
            'public_bound', 'reference_sha256', 'first_divergent_stage', 'stage_nan_differences', 'paired')}
    if file.stem in ('odd-before', '894b9e527a8549c453de514b', 'f005762cfd5e3a7d4520b293'):
        summary['witnesses_before'][file.stem] = data['replays'][0]['result']

for filename in ('matrix192.json', 'matrix384.json', 'nonfinite-matrix2.json'):
    summary[filename] = json.loads((SCRATCH / filename).read_text())['counts']
summary['perf'] = json.loads((SCRATCH / 'perf/olmkirakira/summary.json').read_text())['counts']
before = json.loads((SCRATCH / 'baseline-default-1.json').read_text())['cases']
after = json.loads((SCRATCH / 'default-1.json').read_text())['cases']
assert len(before) == len(after) == 300
regressions, changes = [], []
for old, new in zip(before, after):
    assert (old['index'], old['input_sha256'], old['parameters']) == (new['index'], new['input_sha256'], new['parameters'])
    for route in ('classic', 'smart'):
        a, b = old['result']['routes'][route], new['result']['routes'][route]
        fields = ('status', 'raw_sha256', 'error', 'output_rect')
        if any(a.get(key) != b.get(key) for key in fields):
            changes.append(dict(index=old['index'], route=route, before=a, after=b))
        if a['status'] == 'exact' and b['status'] != 'exact':
            regressions.append(dict(index=old['index'], route=route))
summary['default_comparison'] = dict(conditions=300, route_comparisons=600,
                                     exact_to_nonexact=regressions, changes=changes)
for filename in ('mac/OLMKiraKira/OLMKiraKira.cpp', 'tools/emulation/trace_kirakira_numeric_F09.py',
                 'tools/emulation/verify_kirakira_admission_F10.py'):
    with (ROOT / filename).open('rb') as stream:
        summary['sources'][filename] = hashlib.file_digest(stream, 'sha256').hexdigest()
summary['corpus_total'] = sum(row['completed'] for row in summary['replays'].values())
summary['all_corpora_match_saved'] = all(row['matches_saved'] for row in summary['replays'].values())
(DEST / 'summary.json').write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n')
# Stream reports and logs; do not retain regenerable binaries.
files = [*SCRATCH.glob('*.json'), *SCRATCH.glob('*.log'),
         *list((SCRATCH / 'perf/olmkirakira').glob('*.json')),
         SCRATCH / 'perf/olmkirakira/results.jsonl']
for source in files:
    if not source.is_file():
        continue
    label = source.name if source.parent == SCRATCH else 'perf-' + source.name
    with source.open('rb') as inp, gzip.open(DEST / (label + '.gz'), 'wb') as out:
        shutil.copyfileobj(inp, out)
print(json.dumps({key: summary[key] for key in ('corpus_total', 'all_corpora_match_saved', 'perf', 'default_comparison')}))
