#!/usr/bin/env python3
"""Assert complete C32 campaign preservation; retain compact review evidence."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


def main():
    p=argparse.ArgumentParser();p.add_argument('--scratch',type=Path,required=True);p.add_argument('--phase',required=True);p.add_argument('--previous',required=True);p.add_argument('--report',type=Path,required=True)
    args=p.parse_args();s=args.scratch
    evidence={'phase':args.phase,'campaigns':{},'matrices':{},'replay':{}}
    for seed in (1,43):
        paths={label:s/f'{phase}{seed}.json' for label,phase in (('before',args.previous),('after',args.phase),('gate','off'))}
        data={k:json.loads(v.read_text()) for k,v in paths.items()}
        for d in data.values():assert d['status']=='complete' and d['completed']==300
        trans=Counter();changes=[]
        for x,y,z in zip(*(data[k]['cases'] for k in ('before','after','gate'))):
            assert x['index']==y['index']==z['index'] and x['input_sha256']==y['input_sha256']==z['input_sha256']
            a,b,c=(r['result'] for r in (x,y,z))
            assert a['oracles']==b['oracles']==c['oracles']
            assert a['routes']['classic']==b['routes']['classic']==c['routes']['classic']
            u,v=a['routes']['smart'],b['routes']['smart']
            trans[u['status']+' -> '+v['status']]+=1
            if u['status']=='exact':assert u==v
            if u!=v:
                assert u['status']=='refusal' and v['status']=='exact' and v==c['routes']['smart']
                changes.append({'before':x,'after':y})
            assert v['status'] in ('exact','refusal')
        evidence['campaigns'][str(seed)]={'transitions':dict(trans),'changes':changes,'summary':{k:v['summary'] for k,v in data.items()},'provenance':{k:v['provenance'] for k,v in data.items()},'sha256':{k:hashlib.sha256(v.read_bytes()).hexdigest() for k,v in paths.items()}}
        if args.phase=='final':
            path=s/f'normal{seed}.json';normal=json.loads(path.read_text())
            assert normal['status']=='complete' and normal['completed']==300
            for x,y in zip(normal['cases'],data['after']['cases']):
                assert x['input_sha256']==y['input_sha256'] and x['result']==y['result']
            evidence['campaigns'][str(seed)]['normal_verification']={'identical_results':300,
                'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'provenance':normal['provenance']}
        print(seed,dict(trans))
    replay=json.loads((s/f'{args.phase}-replay.json').read_text())
    evidence['replay']=replay
    # Strict saved-result replay includes the corpus oracle binding.
    assert replay['status']=='replay_complete'
    assert replay['completed']==39 and replay['replay_matches_saved']
    assert all(c['matches_saved'] for c in replay['replays'])
    for name in ('legacy-gate','nonfinite-gate'):
        path=s/f'{name}.json'
        if path.exists():
            matrix=json.loads(path.read_text())
            evidence['matrices'][name]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                                       'transitions':matrix['transitions'],'provenance':matrix['provenance']}
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(evidence,indent=2,sort_keys=True)+'\n')

if __name__=='__main__':main()
