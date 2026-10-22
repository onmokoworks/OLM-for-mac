#!/usr/bin/env python3
"""Bind C13 cluster evidence and check campaign monotonicity; no corpus writes."""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--scratch', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--cluster', required=True)
    p.add_argument('--seeds', type=int, nargs='+', default=[1, 6])
    p.add_argument('--evidence', nargs='+', required=True)
    args = p.parse_args()
    def read(name):
        return json.loads((args.scratch / (name + '.json')).read_text())
    report = dict(schema='olm-kira-smart-C13/1', cluster=args.cluster,
                  campaigns={}, evidence={}, logs={})
    for seed in args.seeds:
        old, new = (read(f'{kind}-seed{seed}') for kind in ('before', 'after'))
        assert all(c['status'] == 'complete' and c['completed'] == 300 for c in (old,new))
        a,b = ({r['index']:r for r in c['cases']} for c in (old,new))
        improved=[]
        for index in range(300):
            x,y=a[index],b[index]
            for field in ('geometry','depth','parameters','input_padding','output_padding','input_sha256'):
                assert x[field] == y[field], (seed,index,field)
            assert x['result']['oracles'] == y['result']['oracles']
            assert x['result']['routes']['classic'] == y['result']['routes']['classic']
            prior,current=(r['result']['routes']['smart'] for r in (x,y))
            assert prior==current or prior['status']=='refusal' and current['status']=='exact', (seed,index)
            if prior != current:
                improved.append(dict(index=index, before=prior, after=current,
                                     input_sha256=x['input_sha256']))
        report['campaigns'][str(seed)] = dict(before=old['summary'], after=new['summary'],
            before_provenance=old['provenance'], after_provenance=new['provenance'], improved=improved,
            previous_exact_unchanged=True, classic_unchanged=True)
    for name in args.evidence:
        report['evidence'][name]=read(name)
    for path in sorted(args.scratch.glob(args.cluster+'-*.log')):
        report['logs'][path.name]=path.read_text()[-5000:]
    source=Path(__file__).resolve().parents[2]/'mac/OLMKiraKira/OLMKiraKira.cpp'
    report['source_sha256']=hashlib.sha256(source.read_bytes()).hexdigest()
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('PASS',args.cluster,{s:len(v['improved']) for s,v in report['campaigns'].items()})


if __name__ == '__main__':
    main()
