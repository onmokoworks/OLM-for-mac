#!/usr/bin/env python3
"""Audit exact preservation, enumerate sign-only differences, bind full reports."""
import copy
import hashlib
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
S = ROOT/'orchestra/state/F38-x86-default-nan-sign'
OUT = ROOT/'orchestra/reports/F38-evidence/measurements.json'

def clean(result):
    result = copy.deepcopy(result)
    for r in result['routes'].values():
        r.get('diff', {}).pop('only_default_nan_sign', None)
    return result

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

out = {'baseline_commit': '395e5d8a', 'campaigns': [], 'corpora': [], 'sign_only': [], 'regressions': [],
       'worker_sha256': sha(Path.home()/'.cache/olm-emu/worker-F32-deep/aex-guest-worker')}
for path in sorted((S/'before').glob('*.json')):
    after_path = S/'after'/path.name
    assert after_path.exists(), after_path
    before, after = (json.loads(p.read_text()) for p in (path, after_path))
    row = {'report': path.name, 'before_sha256': sha(path), 'after_sha256': sha(after_path),
           'before_provenance': before.get('provenance', before.get('replay_groups')),
           'after_provenance': after.get('provenance', after.get('replay_groups'))}
    replay = 'replays' in before
    a, b = (d['replays' if replay else 'cases'] for d in (before, after))
    assert len(a) == len(b)
    assert before['status'] == after['status'] == ('replay_complete' if replay else 'complete')
    row['cases'] = len(a)
    row['changes'] = []
    row['saved_drifts_after'] = []
    row['baseline_saved_matches'] = 0
    row['exact_preserved'] = 0
    if not replay:
        row['before_summary'], row['after_summary'] = before['summary'], after['summary']
    for old, new in zip(a, b):
        key = Path(old['path']).name if replay else old['index']
        assert (Path(new['path']).name if replay else new['index']) == key
        x, y = clean(old['result']), clean(new['result'])
        if replay:
            saved = json.loads(Path(old['path']).read_text())
            previous = saved['result']
            for h in saved.get('rebaseline_history', []):
                if h.get('ticket') == 'F38-x86-default-nan-sign':
                    previous = h['previous_result']
            row['baseline_saved_matches'] += x == previous
            if y != saved['result']:
                row['saved_drifts_after'].append({'case':key, 'saved':saved['result'], 'observed':y})
        for route, r in x['routes'].items():
            n = y['routes'][route]
            if r['status'] == 'exact':
                if n['status'] != 'exact' or r['raw_sha256'] != n.get('raw_sha256'):
                    out['regressions'].append([path.name, key, route, r, n])
                else:
                    row['exact_preserved'] += 1
            if not replay and old['result']['routes'][route].get('diff', {}).get('only_default_nan_sign'):
                out['sign_only'].append({'campaign':path.name,'index':key,'route':route,
                                        'before':r,'after':n,'input_sha256':old['input_sha256']})
        if x != y:
            if x['routes'] == y['routes']:
                details = []
                for route, old_oracle in x.get('oracles', {'smart':x['oracle']}).items():
                    new_oracle = y.get('oracles', {'smart':y['oracle']})[route]
                    if old_oracle != new_oracle:
                        details.append({'route':route, 'before_status':old_oracle['status'],
                            'after_status':new_oracle['status'],
                            'changed_fields':sorted(k for k in old_oracle.keys() | new_oracle.keys()
                                                    if old_oracle.get(k) != new_oracle.get(k)),
                            'before_object_sha256':hashlib.sha256(json.dumps(old_oracle,sort_keys=True).encode()).hexdigest(),
                            'after_object_sha256':hashlib.sha256(json.dumps(new_oracle,sort_keys=True).encode()).hexdigest()})
                row['changes'].append({'case':key, 'unchanged_routes':True, 'oracle_only_changes':details})
            else:
                row['changes'].append({'case':key, 'before':x, 'after':y})
    if replay:
        row['matches_saved_after'] = sum(c['matches_saved'] for c in b)
        # Initial instrumentation added one diagnostic key to mismatch results;
        # remove that key when comparing measurements, not render data.
        row['identical_before_after'] = len(a)-len(row['changes'])
        out['corpora'].append(row)
    else:
        out['campaigns'].append(row)
    print(path.name, 'cases',len(a),'exact_preserved',row['exact_preserved'], 'changes',len(row['changes']))
assert len(out['campaigns']) == 20
assert len(out['corpora']) == 11
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(out, indent=2, sort_keys=True)+'\n')
print('sign-only', len(out['sign_only']), 'regressions',len(out['regressions']))
assert not out['regressions']
