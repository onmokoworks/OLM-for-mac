#!/usr/bin/env python3
"""Bind C26's rejected admission experiments and unchanged-production checks."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--state', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    state = args.state.resolve()
    assert state.is_relative_to(ROOT/'orchestra/state/C26-radial-smart-r4')
    assert args.output.resolve().is_relative_to(ROOT)
    bindings = {}
    def read(name):
        raw = (state/name).read_bytes()
        bindings[name] = hashlib.sha256(raw).hexdigest()
        return json.loads(raw)
    base = read('base.json')
    assert base['completed'] == 300
    assert [base['summary'].get('smart_'+s, 0) for s in ('exact','mismatch','refusal')] == [241,0,59]
    census = Counter()
    for r in base['cases']:
        if r['result']['routes']['smart']['status'] == 'refusal' and r['result']['oracles']['smart']['status'] == 'ok':
            census[','.join(g.split('@')[0] for g in r.get('refusal_guards',{}).get('smart',[])) or 'host'] += 1
    experiments = {}
    for name in ('centers32','budget'):
        p = read(name+'/report.json')
        assert all(not r['after'].get('sanitizer') for r in p['rows'])
        experiments[name] = dict(counts=dict(Counter(r['after']['status'] for r in p['rows'])), **p)
    matrices = {}
    for name in ('finite-matrix','centers32-matrix'):
        p = read(name+'/report.json')
        rows = p['independent']
        assert len(rows) == 72
        assert all(l['clean'] for r in rows for l in r['layouts'])
        matrices[name] = dict(provenance=p['provenance'], references=len(rows),
            layouts=sum(len(r['layouts']) for r in rows),
            exact=sum(l['exact'] for r in rows for l in r['layouts']),
            failures=[r for r in rows if not all(l['exact'] for l in r['layouts'])])
    verify = read('production-verify/report.json')
    assert verify['status'] == 'pass' and not verify['failures']
    assert len(verify['campaigns'][0]['rows']) == 300 and verify['smoke']['tests'] == 8
    replay = read('replay.json')
    assert len(replay['replays']) == 35 and all(r['matches_saved'] for r in replay['replays'])
    corpus = []
    for r in replay['replays']:
        path = Path(r['path'])
        if not path.is_absolute(): path = ROOT/path
        saved = json.loads(path.read_text())['result']['routes']['smart']
        actual = r['result']['routes']['smart']
        assert saved['status'] == actual['status'] == 'exact' and saved['raw_sha256'] == actual['raw_sha256']
        corpus.append(dict(path=str(path.relative_to(ROOT)), before=saved, after=actual))
    production = ['mac/OLMRadialBlur/OLMRadialBlur.cpp','core/dblur_noise.h']
    for rel in production:
        raw = (ROOT/rel).read_bytes()
        assert raw == subprocess.check_output(['git','show','c4a0b92a:'+rel],cwd=ROOT)
        bindings[rel] = hashlib.sha256(raw).hexdigest()
    report = dict(status='blocked',production_changed=False,bindings=bindings,
        baseline=dict(provenance=base['provenance'],summary=base['summary'],elapsed_seconds=base['elapsed_seconds'],
            rendered_refusal_census=dict(census),rows=[dict(index=r['index'],input_sha256=r['input_sha256'],
                smart=r['result']['routes']['smart'],oracle=r['result']['oracles']['smart'],
                guards=r.get('refusal_guards',{}).get('smart',[])) for r in base['cases']]),
        experiments=experiments,matrices=matrices,production_verification=verify,corpus=corpus)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: unchanged 241/0/59; production 300 same/clean; smoke 8; corpus 35 unchanged')
    print('EXPERIMENTS', {k:v['counts'] for k,v in experiments.items()})
    print('MATRICES', {k:(v['exact'],v['layouts']) for k,v in matrices.items()})


if __name__ == '__main__':
    main()
