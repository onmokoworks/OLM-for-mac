#!/usr/bin/env python3
"""Assert C10 promotion monotonicity and retain reviewable per-commit evidence.

Corpus writes require --rebaseline and are restricted to refusal -> exact.
Run the campaigns/matrices first as documented in the C10 worker report.
"""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import sys
sys.dont_write_bytecode=True
from core import sha
from run import ROOT
from verify_blur_smart_C05 import retained


def load(path):return json.loads(path.read_text())


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--scratch',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    p.add_argument('--before',required=True)
    p.add_argument('--after',required=True)
    p.add_argument('--base',required=True)
    p.add_argument('--admitted-depths',type=int,nargs='+',required=True)
    p.add_argument('--rebaseline',action='store_true')
    args=p.parse_args();s=args.scratch.resolve()
    assert s.is_relative_to(ROOT/'orchestra/state/C10-olmblur-smart-r2')
    os.environ.update(TMPDIR=str(s),TMP=str(s),TEMP=str(s))
    report={'schema':'olmblur-admission-C10/1','base':args.base,'stage':args.after,'seeds':{},
            'source_sha256':sha((ROOT/'mac/OLMBlur/OLMBlur.cpp').read_bytes())}
    for seed in (1,4):
        data={k:load(s/f'{label}-{seed}.json') for k,label in
              (('before',args.before),('after',args.after),('sanitized',args.after+'-san'),('gateoff','off'))}
        assert all(d['completed']==300 and d['jobs']==2 and d['seed']==seed for d in data.values())
        changes=[];transitions=Counter();preserved=0
        for b,a,z,g in zip(*(data[k]['cases'] for k in ('before','after','sanitized','gateoff'))):
            assert b['input_sha256']==a['input_sha256']==z['input_sha256']==g['input_sha256']
            assert b['result']['oracles']==a['result']['oracles']==z['result']['oracles']==g['result']['oracles']
            assert a['result']==z['result'],(seed,a['index'],'sanitizer drift')
            assert b['result']['routes']['classic']==a['result']['routes']['classic']
            br=b['result']['routes']['smart'];ar=a['result']['routes']['smart']
            assert ar['status'] in ('exact','mismatch','refusal')
            transitions[br['status']+' -> '+ar['status']]+=1
            if br['status']=='exact':assert br==ar;preserved+=1
            if br!=ar:
                assert br['status']=='refusal' and ar['status']=='exact',(seed,a['index'])
                assert ar==g['result']['routes']['smart'],(seed,a['index'],'gate-off drift')
                changes.append({k:a[k] for k in ('index','geometry','depth','parameters','input_sha256')}|
                               {'before':br,'after':ar,'oracle':a['result']['oracles']['smart']})
        report['seeds'][str(seed)]={'counts':{k:d['summary'] for k,d in data.items()},
            'provenance':{k:d['provenance'] for k,d in data.items()},'transitions':dict(transitions),
            'base_exact_preserved':preserved,'sanitized_routes':600,'changed_cases':changes}
    b=load(s/f'{args.before}-replay.json');a=load(s/f'{args.after}-replay.json')
    assert b['completed']==a['completed']==39
    corpus=[];updates=[]
    for old,new in zip(b['replays'],a['replays']):
        assert old['path']==new['path']
        path=Path(new['path']).resolve();assert path.is_relative_to(ROOT/'tests/fuzz_corpus/olmblur')
        saved=load(path)
        history=saved.get('C10_updates',[])
        previous=next((h['previous_result'] for h in history if h['stage']==args.after),saved['result'])
        assert old['result']==previous,path
        assert old['result']['oracles']==new['result']['oracles']
        assert old['result']['routes']['classic']==new['result']['routes']['classic']
        br=old['result']['routes']['smart'];ar=new['result']['routes']['smart']
        if br!=ar:
            assert br['status']=='refusal' and ar['status']=='exact',path
            updates.append((path,saved,new['result']))
        corpus.append({'path':str(path.relative_to(ROOT)),'before':old['result'],'after':new['result']})
    report['corpus']=corpus
    report['corpus_smart_transitions']=dict(Counter(r['before']['routes']['smart']['status']+' -> '+r['after']['routes']['smart']['status'] for r in corpus))
    report['corpus_updates']=[str(v[0].relative_to(ROOT)) for v in updates]
    for label in ('matrix-'+args.after,'boundaries-'+args.after):
        d=load(s/f'{label}.json')
        assert d['provenance']['source_sha256']==report['source_sha256']
        assert all(r['status']==('exact' if r['expected_admitted'] else 'refusal') for r in d['cases'])
        report[label]=d
    d=load(s/'matrix-off.json')
    report['diagnostic_matrix']={'counts':d['counts'],'by_depth':d['by_depth'],'provenance':d['provenance'],
        'mismatches':[r for r in d['cases'] if r['status']!='exact']}
    report['retained']=retained(s)
    if args.rebaseline:
        for path,saved,result in updates:
            if saved['result']==result:continue
            saved.setdefault('C10_updates',[]).append({'stage':args.after,'previous_result':saved['result'],
                'report':'orchestra/reports/C10-olmblur-smart-r2.md'})
            saved['result']=result
            path.write_text(json.dumps(saved,indent=2,sort_keys=True)+'\n')
    args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print({k:v['transitions'] for k,v in report['seeds'].items()})
    print('corpus',report['corpus_smart_transitions'],'retained',len(report['retained']['lines']))


if __name__=='__main__':main()
