#!/usr/bin/env python3
"""Assert F20 regression direction and retain compact, hash-bound evidence."""
import argparse
from collections import Counter
import copy
import json
from pathlib import Path

from core import sha


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--scratch',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    def read(name): return json.loads((args.scratch/(name+'.json')).read_text())
    before, after = read('before'), read('after')
    assert before['completed']==after['completed']==300
    campaigns = {}
    for name in ('before','sanitize-before','gateoff','gateoff-final','after','sanitize-after'):
        if not (args.scratch/(name+'.json')).exists(): continue
        report = read(name)
        campaigns[name] = dict(provenance=report['provenance'],completed=report['completed'],
            counts={route:dict(Counter(c['result']['routes'][route]['status'] for c in report['cases']))
                    for route in ('classic','smart')},
            sanitizer_rows={route:sum(bool(c['result']['routes'][route].get('sanitizer')) for c in report['cases'])
                            for route in ('classic','smart')})
    changes = []
    for b,a in zip(before['cases'],after['cases']):
        assert b['index']==a['index'] and b['input_sha256']==a['input_sha256']
        assert b['result']['oracles']==a['result']['oracles']
        for route in ('classic','smart'):
            old,new = b['result']['routes'][route],a['result']['routes'][route]
            if old['status']=='exact': assert new==old,(a['index'],route)
        assert a['result']['routes']['classic']['raw_sha256']==a['result']['routes']['smart']['raw_sha256']
        changes.append(dict(index=a['index'],input_sha256=a['input_sha256'],
            count=next(p['value'] for p in a['parameters'] if p['slot']==22),
            before=b['result'],after=a['result']))
    zero = [c for c in changes if c['count']==0]
    assert len(zero)==41 and all(c['after']['routes']['smart']['status']=='exact' for c in zero)
    assert campaigns['after']['counts']['smart']=={'exact':299,'uncompared':1}
    assert campaigns['after']['counts']['classic']=={'mismatch':300}
    for route in ('classic','smart'):
        assert campaigns['after']['counts'][route].get('exact',0)>=campaigns['before']['counts'][route].get('exact',0)
        assert campaigns['sanitize-after']['sanitizer_rows'][route]==0
    for plain,sanitized in (('before','sanitize-before'),('after','sanitize-after')):
        for a,b in zip(read(plain)['cases'],read(sanitized)['cases']):
            cleaned=copy.deepcopy(b['result'])
            for route in cleaned['routes'].values(): route.pop('sanitizer',None)
            assert a['result']==cleaned,(plain,a['index'])
    corpus = []
    for b,a in zip(read('replay-before')['replays'],read('replay-after')['replays']):
        assert b['matches_saved']
        assert a['result']['routes']['smart']['status']=='exact'
        for route in ('classic','smart'):
            old,new=b['result']['routes'][route],a['result']['routes'][route]
            assert new.get('diff',{}).get('different_words',0)<=old.get('diff',{}).get('different_words',0)
        corpus.append(dict(path=Path(a['path']).name,before=b['result'],after=a['result']))
    boundaries=read('boundaries')
    assert boundaries['exact']==boundaries['case_count']*4==1152
    stages=read('stages-after')
    assert all(c['matte_diff']['different_words']==c['final_diff']['different_words']==0 for c in stages['cases'])
    result=dict(schema='olm-colorkey-F20/1',campaigns=campaigns,campaign_cases=changes,
        corpus=corpus,stages_after=stages,alpha_trace=read('alpha-trace'),
        boundaries=dict(case_count=boundaries['case_count'],exact=boundaries['exact'],
            provenance=boundaries['provenance'],cases=[{k:c[k] for k in ('label','input_sha256','oracle_sha256')}
                                                    for c in boundaries['cases']]))
    if (args.scratch/'stages-intermediate.json').exists():
        result['stages_subtraction_only']=read('stages-intermediate')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print('F20: 255 -> 299 Smart exact; Classic 0 -> 0; 41 zero-count exact; 3 corpus improvements; sanitizer clean')


if __name__=='__main__': main()
