#!/usr/bin/env python3
"""Assert C57 exact qualification, prior output preservation, and full trace bindings."""
import argparse,gzip,hashlib,json,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def read(p):
    with (gzip.open(p,'rt') if p.suffix=='.gz' else p.open()) as f:return json.load(f)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--state',type=Path,required=True);a=ap.parse_args();s=a.state
    report=dict(campaigns=[],preservation=[],sanitizers=[],corpus=[],traces=[])
    for seed in (1,105,57003):
        d=read(s/f'seed{seed}/campaign.json');rows=d['cases'];assert len(rows)==300
        counts={}
        for r in rows:
            status=r['result']['routes']['smart']['status'];counts[status]=counts.get(status,0)+1
        assert not counts.get('mismatch',0)
        report['campaigns'].append(dict(seed=seed,counts=counts))
        if seed in (1,105):
            old=read(ROOT/f'orchestra/reports/C53b-evidence/seed{seed}.json.gz')
            by={r['index']:r for r in rows};exact=outputs=0
            for r in old['cases']:
                n=by[r['index']];assert r['input_sha256']==n['input_sha256']
                before=r['result']['routes']['smart'];expected=before.get('raw_sha256')
                if expected:
                    assert expected==n['result']['routes']['smart'].get('raw_sha256'),(seed,r['index'])
                    outputs+=1;exact+=before['status']=='exact'
            report['preservation'].append(dict(seed=seed,previous_exact=exact,previous_outputs=outputs))
        sd=read(s/f'san{seed}/report.json');assert len(sd['cases'])==300
        assert not any(r['result'].get('sanitizer') for r in sd['cases'])
        recovered=[]
        for r in sd['cases']:
            if r['matches_campaign']:continue
            before=next(x for x in rows if x['index']==r['index'])['result']['routes']['smart']
            assert before['status']=='budget' and r['result']['status']=='ok', (seed,r['index'])
            retry=read(s/f'retry{seed}-{r["index"]}/report.json')
            assert retry['input_sha256']==r['input_sha256']
            assert retry['candidate']['status']=='ok' and retry['raw_sha256']==r['raw_sha256']
            assert retry['provenance']['source_sha256']==sd['provenance']['source_sha256']
            if retry['oracle']['status']=='ok':assert retry['exact']
            recovered.append(r['index'])
        assert sorted(sd['failures'])==sorted(recovered)
        report['sanitizers'].append(dict(seed=seed,cases=300,initial_budget_completions=recovered,failures=0))
    replay=read(s/'corpus/campaign.json');assert replay['completed']==replay['requested']==61
    for r in replay['replays']:
        saved=read(ROOT/'tests/fuzz_corpus/radialblur'/Path(r['path']).name);matches={}
        for route,before in saved['result']['routes'].items():
            after=r['result']['routes'][route];expected=before.get('raw_sha256')
            matches[route]=expected==after.get('raw_sha256') if expected else before['status']==after['status']
        assert all(matches.values()),r['path']
        report['corpus'].append(dict(path=Path(r['path']).name,matches=matches))
    tr=read(s/'trace-builder/report.json');assert len(tr['cases'])==3
    for r in tr['cases']:
        assert r['bound']
        t=read(s/f'trace-builder/{r["seed"]}-{r["index"]}/trace.json')
        assert not t['trace_configuration']['unhookable_watches'] and not t['dropped_memory_witnesses'] and not t['truncated']
        size=r['geometry'][0]*r['geometry'][1]*4;spans=0
        for w in t['memory_witnesses']:
            if w['watch_id'].endswith('-span'):
                for k in ('before','after'):
                    b=bytes.fromhex(w[k]['hex']);assert len(b)==size and b==bytes(size)
                spans+=1
            if w['watch_id']=='builder-context':
                p=struct.unpack_from('<Q',bytes.fromhex(w['before']['hex']),0xa8)[0]
                assert p==struct.unpack_from('<Q',bytes.fromhex(w['after']['hex']),0xa8)[0]
            if w['watch_id']=='layer-copy-destination':
                assert bytes.fromhex(w['after']['hex'])==bytes(120)
        assert spans==2
        report['traces'].append(dict(seed=r['seed'],index=r['index'],cells=size//4,output_sha256=r['output_sha256'],span_captures=spans))
    controls=read(s/'controls/report.json')['cases'];assert len(controls)==72
    assert not any(r['status']=='mismatch' or r['result'].get('sanitizer') for r in controls)
    invalid=read(s/'invalid-host/report.json')['cases'];assert len(invalid)==9
    assert all(r['result']['status']=='refusal' and not r['result'].get('sanitizer') for r in invalid)
    report['controls']={k:sum(r['status']==k for r in controls) for k in ('exact','mismatch','uncompared')}
    witnesses=read(s/'witnesses/report.json')['cases'];assert len(witnesses)==6 and all(r['exact'] for r in witnesses)
    (s/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(campaigns=report['campaigns'],preservation=report['preservation'],sanitizers=900,corpus=61,controls=report['controls'],traces=3)))
if __name__=='__main__':main()
