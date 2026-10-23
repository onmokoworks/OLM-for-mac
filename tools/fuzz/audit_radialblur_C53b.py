#!/usr/bin/env python3
"""Audit C53b qualification and unchanged retained-reference hashes."""
import argparse
import gzip
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]


def read(p):
    with (gzip.open(p,'rt') if p.suffix=='.gz' else p.open()) as f:return json.load(f)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--state',type=Path,required=True)
    args=ap.parse_args();s=args.state
    report=dict(campaigns=[],preservation=[],sanitizers=[],corpus=[])
    for seed in (1,105,54321):
        d=read(s/f'seed{seed}/campaign.json')
        rows=d['cases'];assert len(rows)==300
        counts={}
        for r in rows:
            status=r['result']['routes']['smart']['status'];counts[status]=counts.get(status,0)+1
        assert not counts.get('mismatch',0)
        report['campaigns'].append(dict(seed=seed,counts=counts))
        if seed in (1,105):
            old=read(ROOT/f'orchestra/reports/C49-evidence/final{seed}.json.gz')
            by={r['index']:r for r in rows};preserved=[]
            for r in old['rows']:
                n=by[r['index']];assert r['input_sha256']==n['input_sha256']
                if r['after']['status']=='exact':
                    assert r['after']['raw_sha256']==n['result']['routes']['smart'].get('raw_sha256'),(seed,r['index'])
                    preserved.append(r['index'])
            report['preservation'].append(dict(seed=seed,previous_exact=len(preserved),preserved=preserved))
        sd=read(s/('san1-fixed' if seed==1 else f'san{seed}')/'report.json')
        assert len(sd['cases'])==300 and not sd['failures']
        report['sanitizers'].append(dict(seed=seed,cases=300,failures=0))
    replay=read(s/'corpus/campaign.json')
    assert replay['completed']==replay['requested']
    for r in replay['replays']:
        saved=read(Path(r['path']))
        matches={}
        for route,before in saved['result']['routes'].items():
            after=r['result']['routes'][route]
            expected=before.get('raw_sha256')
            matches[route]=expected==after.get('raw_sha256') if expected else before['status']==after['status']
        report['corpus'].append(dict(path=Path(r['path']).name,matches=matches,whole_result_matches_saved=r['matches_saved']))
    report['corpus_preserved']=all(all(r['matches'].values()) for r in report['corpus'])
    (s/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(campaigns=report['campaigns'],sanitizers=900,
        preserved=sum(r['previous_exact'] for r in report['preservation']),
        corpus=len(report['corpus']),corpus_preserved=report['corpus_preserved'],
        whole_corpus_matches=replay['replay_matches_saved'])))
    return not report['corpus_preserved']

if __name__=='__main__':raise SystemExit(main())
