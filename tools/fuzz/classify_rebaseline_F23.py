"""Audit every changed corpus route before F23 production rebaseline."""
from pathlib import Path
from collections import Counter
import json

scratch = Path('orchestra/state/F23-corpus-rebaseline-all')
summary = []
expected_reports = {scratch / f'before-{p.name}.json'
                    for p in Path('tests/fuzz_corpus').iterdir() if p.is_dir()}
if not expected_reports.issubset(set(scratch.glob('before-*.json'))):
    raise SystemExit('missing corpus replay reports; finish replay_all_F23.py before first')
for report in sorted(scratch.glob('before-*.json')):
    data = json.loads(report.read_text())
    corpus = Path('tests/fuzz_corpus') / report.stem.removeprefix('before-')
    expected = {p.resolve() for p in corpus.glob('*.json')}
    if not expected:
        if data.get('status') != 'setup_error':
            raise SystemExit(f'{corpus}: unexpected empty-corpus outcome')
    elif (data.get('status') != 'replay_complete' or
          len(data.get('replays', [])) != len(expected) or
          {Path(r['path']).resolve() for r in data['replays']} != expected):
        raise SystemExit(f'{corpus}: incomplete replay')
    transitions = Counter()
    changes = []
    forbidden = []
    oracle_matches = 0
    for row in data.get('replays', []):
        case = json.loads(Path(row['path']).read_text())
        saved = case['result']
        for entry in case.get('rebaseline_history', []):
            if entry['ticket'] == 'F23-corpus-rebaseline-all':
                saved = entry['previous_result']
                break
        current = row['result']
        if saved['routes'].keys() != current['routes'].keys():
            raise SystemExit(f'{row["path"]}: changed route set')
        oracle_ok = saved['oracle'] == current['oracle'] and ('oracles' not in saved or saved['oracles'] == current.get('oracles'))
        oracle_matches += oracle_ok
        if not oracle_ok: forbidden.append({'path': str(Path(row['path']).resolve().relative_to(Path.cwd())), 'reason': 'oracle drift'})
        if saved == current: continue
        routes = []
        for route, before in saved['routes'].items():
            after = current['routes'][route]
            start, end = before['status'], after['status']
            transitions[(route, start, end)] += 1
            allowed = before == after or end == 'exact' or (start, end) in {('mismatch','mismatch'),('mismatch','refusal'),('refusal','refusal')}
            if start == 'exact' and (end != 'exact' or before.get('raw_sha256') != after.get('raw_sha256')): allowed = False
            if start == end == 'refusal' and before.get('raw_sha256') != after.get('raw_sha256'): allowed = False
            detail = {'route':route, 'before':start, 'after':end, 'before_sha256':before.get('raw_sha256'), 'after_sha256':after.get('raw_sha256'), 'before_diff':before.get('diff'), 'after_diff':after.get('diff'), 'changed':before != after, 'allowed':allowed}
            routes.append(detail)
            if not allowed: forbidden.append({'path':str(Path(row['path']).resolve().relative_to(Path.cwd())), **detail})
        changes.append({'path':str(Path(row['path']).resolve().relative_to(Path.cwd())), 'routes':routes})
    summary.append({'corpus':report.stem.removeprefix('before-'), 'plugin':data['plugin'], 'cases':len(data.get('replays',[])), 'matches_saved':sum(r['matches_saved'] for r in data.get('replays',[])), 'oracle_matches':oracle_matches, 'transitions':[{'route':r,'before':b,'after':a,'count':n} for (r,b,a),n in sorted(transitions.items())], 'forbidden':forbidden,'changes':changes})
output=Path('orchestra/reports/F23-corpus-rebaseline-all-transitions.json')
output.write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
for item in summary:
    print(item['corpus'], item['matches_saved'], '/',item['cases'], 'forbidden',len(item['forbidden']), item['transitions'])
