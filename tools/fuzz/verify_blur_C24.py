#!/usr/bin/env python3
"""Validate and compact C24 diagnostics; never edit a corpus or renderer."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--scratch',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    args=p.parse_args()
    evidence=dict(campaigns={},traces={},probes={},files={})
    def read(name):
        path=args.scratch/(name+'.json')
        evidence['files'][name]=hashlib.sha256(path.read_bytes()).hexdigest()
        return json.loads(path.read_text())
    for seed,expected in ((1,(281,2,17,293,7)),(11,(282,4,14,295,5))):
        base,off=read(f'base-seed{seed}'),read(f'off-seed{seed}')
        assert base['status']==off['status']=='complete'
        assert base['completed']==off['completed']==300
        counts=tuple(base['summary'].get('smart_'+s,0) for s in ('exact','mismatch','refusal'))
        counts+=tuple(off['summary'].get('smart_'+s,0) for s in ('exact','mismatch'))
        assert counts==expected,(seed,counts)
        transitions=Counter(); residuals=[]
        for a,b in zip(base['cases'],off['cases']):
            assert a['index']==b['index'] and a['input_sha256']==b['input_sha256']
            x,y=a['result'],b['result']
            assert x['oracles']==y['oracles'] and x['routes']['classic']==y['routes']['classic']
            x,y=x['routes']['smart'],y['routes']['smart']
            transitions[x['status']+'->'+y['status']]+=1
            if x['status']=='exact':assert x==y
            if x['status']!='exact':residuals.append(dict(before=a,gate_off=b['result']['routes']['smart']))
        evidence['campaigns'][str(seed)]=dict(base=base['summary'],gate_off=off['summary'],
            transitions=dict(transitions),residuals=residuals,provenance=base['provenance'])
    for name in ('legacy-trace','legacy-invalid','nonlegacy-ops'):
        result=read(name)
        for row in result['rows']:
            assert row['cached_binding']
            row.pop('nonfinite_ops',None)
        evidence['traces'][name]=result
    for name in ('legacy-invalid-probe','nonlegacy-probe'):
        result=read(name)
        assert result['summary']['instruction-matrix']==dict(count=432,arm64_different=36,x86_64_different=12)
        per_case={}
        for index in sorted({r['case'] for r in result['rows'] if 'case' in r}):
            rows=[r for r in result['rows'] if r.get('case')==index]
            per_case[index]=dict(count=len(rows))
            for arch in ('arm64','x86_64'):
                different=[r for r in rows if r[arch]!=r['result']]
                assert different
                per_case[index][arch]=dict(different=len(different),first=different[0])
        # Keep all independent boundary rows, but compact repeated public events.
        result['rows']=[r for r in result['rows'] if r['kind']=='instruction-matrix']
        result['public_cases']=per_case
        evidence['probes'][name]=result
    replay=read('replay')
    assert replay['replay_matches_saved'] and len(replay['replays'])==39
    statuses=Counter(r['result']['routes']['smart']['status'] for r in replay['replays'])
    assert statuses==dict(exact=38,mismatch=1)
    evidence['corpus']=dict(matches_saved=39,transitions={k+'->'+k:v for k,v in statuses.items()},
                            provenance=replay['provenance'])
    evidence['scope']='CPU AEX Unicorn vs Mac fake host; no renderer changes or native Windows claim'
    args.report.write_text(json.dumps(evidence,indent=2,sort_keys=True)+'\n')
    print('PASS: 563 base-exact campaign cases unchanged under bypass; corpus 39/39 unchanged; instruction boundaries reproduced')


if __name__=='__main__':main()
