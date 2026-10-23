#!/usr/bin/env python3
"""Compact, hash-bound evidence for the F32 default qualification."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
S = ROOT/'orchestra/state/F37-default-worker-f32'
OUT = ROOT/'orchestra/reports/F37-evidence/measurements.json'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

out = {'worker_sha256': sha(Path.home()/'.cache/olm-emu/worker-F32-deep/aex-guest-worker'),
       'campaigns': [], 'corpora': []}
for path in sorted(S.glob('*.json')):
    if not path.stem.endswith(('-replay', '-seed1')):
        continue
    data = json.loads(path.read_text())
    row = {'report': path.name, 'report_sha256': sha(path), 'status': data['status'],
           'provenance': data.get('provenance'), 'completed': data.get('completed')}
    if 'replays' in data:
        row['completed'] = len(data['replays'])
        row['matches_saved'] = sum(r['matches_saved'] for r in data['replays'])
        row['changes'] = []
        for replay in data['replays']:
            p = Path(replay['path'])
            saved = json.loads(p.read_text())
            if saved['result'] != replay['result']:
                row['changes'].append({'path': str(p.relative_to(ROOT)),
                    'depth': saved['case']['depth'], 'input_sha256': saved['input_sha256'],
                    'saved': saved['result'], 'observed': replay['result']})
        out['corpora'].append(row)
        print(path.stem, row['matches_saved'], '/', row['completed'])
    else:
        row['summary'] = data['summary']
        row['completed'] = len(data['cases'])
        row['first_mismatches'] = {}
        for case in data['cases']:
            for route, result in case.get('result', {}).get('routes', {}).items():
                if result['status'] == 'mismatch' and route not in row['first_mismatches']:
                    row['first_mismatches'][route] = {k: case[k] for k in
                        ('index', 'depth', 'geometry', 'input_sha256', 'result')}
        row['worker_errors'] = [c for c in data['cases'] if 'worker_error' in c]
        out['campaigns'].append(row)
        print(path.stem, data['summary'])
control = S/'t06-f30.json'
if control.exists():
    old = json.loads(control.read_text())
    new = json.loads((S/'olmkirakira_gate_off_T06-replay.json').read_text())
    assert [Path(r['path']).resolve() for r in old['replays']] == [Path(r['path']).resolve() for r in new['replays']]
    out['t06_f30_control'] = {
        'report_sha256': sha(control), 'provenance': old['provenance'],
        'completed': old['completed'],
        'matches_saved': sum(r['matches_saved'] for r in old['replays']),
        'identical_results_f30_f32': sum(a['result'] == b['result']
            for a, b in zip(old['replays'], new['replays']))}
    print('T06 F30 control', out['t06_f30_control']['identical_results_f30_f32'], 'identical')
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(out, indent=2, sort_keys=True)+'\n')
