#!/usr/bin/env python3
"""Produce compact, hash-bound C33 evidence without rewriting corpus expectations."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--state', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    result = {'campaigns': {}, 'matrices': {}, 'replays': {}, 'comparisons': []}
    for path in sorted(args.state.rglob('*.json')):
        if path.name not in ('baseline.json', 'campaign.json', 'report.json', 'replay.json'):
            continue
        p = json.loads(path.read_text())
        name = str(path.relative_to(args.state))
        if p.get('cases') and 'seed' in p:
            rows = p['cases']
            counts = Counter(r['result']['routes']['smart']['status'] for r in rows)
            refusal = Counter(tag.split('@')[0] for r in rows
                              if r['result']['routes']['smart']['status'] == 'refusal'
                              and r['result']['oracles']['smart']['status'] == 'ok'
                              for tag in (r.get('refusal_guards', {}).get('smart', []) or ['host-checkout']))
            result['campaigns'][name] = dict(sha256=sha(path), seed=p['seed'], count=len(rows), counts=counts,
                rendered_refusals=refusal, provenance=p.get('provenance'),
                verifier_failures=p.get('failures', []), refusal_error_changes=p.get('refusal_error_changes', []),
                sanitizer_reports=sum(bool(r['result']['routes']['smart'].get('sanitizer')) for r in rows))
        elif p.get('independent'):
            rows = p['independent']
            result['matrices'][name] = dict(sha256=sha(path), references=len(rows),
                layouts=sum(len(r['layouts']) for r in rows),
                exact=sum(l['exact'] for r in rows for l in r['layouts']),
                clean=sum(l['clean'] for r in rows for l in r['layouts']),
                failures=[r for r in rows if not all(l['exact'] and l['clean'] for l in r['layouts'])],
                provenance=p['provenance'])
        elif 'replays' in p:
            result['replays'][name] = dict(sha256=sha(path), count=len(p['replays']),
                saved_matches=sum(r['matches_saved'] for r in p['replays']),
                smart_counts=Counter(r['result']['routes']['smart']['status'] for r in p['replays']))
    names = list(result['campaigns'])
    for before, after in [('baseline.json', 'center-seed1/campaign.json'),
                          ('base-seed2/campaign.json', 'center-seed2/campaign.json'),
                          ('center-seed1/campaign.json', 'center16-seed1/campaign.json'),
                          ('center-seed2/campaign.json', 'center16-seed2/campaign.json')]:
        if before not in names or after not in names:
            continue
        old = json.loads((args.state/before).read_text())['cases']
        new = json.loads((args.state/after).read_text())['cases']
        assert len(old) == len(new) == 300
        transitions, changes, lost, error_changes = Counter(), [], [], []
        for a, b in zip(old, new):
            assert a['index'] == b['index'] and a['input_sha256'] == b['input_sha256']
            x, y = (r['result']['routes']['smart'] for r in (a, b))
            transitions[x['status']+' -> '+y['status']] += 1
            if x['status'] == 'exact' and (y['status'] != 'exact' or x['raw_sha256'] != y['raw_sha256']):
                lost.append(a['index'])
            if x['status'] == y['status'] == 'refusal' and x['error'] != y['error']:
                error_changes.append(dict(index=a['index'], before=x['error'], after=y['error'], guards=b.get('refusal_guards', {})))
            if x['status'] != y['status']:
                changes.append(dict(index=a['index'], before=x, after=y, oracle=b['result']['oracles']['smart']))
        result['comparisons'].append(dict(before=before, after=after, transitions=transitions,
                                          lost_exact=lost, changes=changes, refusal_error_changes=error_changes))
    prod = args.state/'production-verify/report.json'
    if prod.exists():
        p = json.loads(prod.read_text())
        result['production_verify'] = dict(sha256=sha(prod),
            rows=sum(len(c['rows']) for c in p['campaigns']),
            same=sum(r['same'] for c in p['campaigns'] for r in c['rows']),
            clean=sum(r['clean'] for c in p['campaigns'] for r in c['rows']),
            smoke={k:v for k,v in p['smoke'].items() if k != 'rows'},
            smoke_rows=[dict(test=r['test'], status=r['status'],
                            linker_failure='Undefined symbols' in r.get('detail','')) for r in p['smoke']['rows']])
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print('campaigns', len(result['campaigns']), 'matrices', len(result['matrices']), 'replays', len(result['replays']))
    for c in result['comparisons']:
        print(c['before'], '->', c['after'], dict(c['transitions']), 'lost exact', c['lost_exact'])


if __name__ == '__main__':
    main()
