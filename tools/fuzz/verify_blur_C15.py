#!/usr/bin/env python3
"""C15 per-commit monotonicity, independent matrix, corpus and retained controls."""
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
    for name in ('scratch','report'):p.add_argument('--'+name,type=Path,required=True)
    for name in ('before','after','base'):p.add_argument('--'+name,required=True)
    p.add_argument('--depth',type=int,required=True);p.add_argument('--rebaseline',action='store_true')
    args=p.parse_args();s=args.scratch.resolve();assert s.is_relative_to(ROOT/'orchestra/state/C15-olmblur-smart-r4')
    os.environ.update(TMPDIR=str(s),TMP=str(s),TEMP=str(s))
    report={'schema':'olmblur-C15/1','base':args.base,'stage':args.after,'depth':args.depth,'seeds':{},'source_sha256':sha((ROOT/'mac/OLMBlur/OLMBlur.cpp').read_bytes())}
    for seed in (1,6):
        data={k:load(s/f'{v}-{seed}.json') for k,v in [('before',args.before),('after',args.after),('sanitized',args.after+'-san'),('gateoff','off-'+args.after)]}
        assert all(d['completed']==300 and d['jobs']==2 and d['seed']==seed for d in data.values())
        changes=[];transitions=Counter();preserved=0
        for b,a,z,g in zip(*(data[k]['cases'] for k in ('before','after','sanitized','gateoff'))):
            assert b['input_sha256']==a['input_sha256']==z['input_sha256']==g['input_sha256']
            assert b['result']['oracles']==a['result']['oracles']==z['result']['oracles']==g['result']['oracles']
            assert a['result']==z['result'],(seed,a['index'],'sanitizer drift')
            assert b['result']['routes']['classic']==a['result']['routes']['classic']
            br=b['result']['routes']['smart'];ar=a['result']['routes']['smart'];transitions[br['status']+' -> '+ar['status']]+=1
            assert ar['status'] in ('exact','mismatch','refusal')
            if br['status']=='exact':assert br==ar;preserved+=1
            if br!=ar:
                assert br['status'] in ('refusal','mismatch'),(seed,a['index'],br,ar)
                assert ar['status']=='exact',(seed,a['index'],br,ar)
                assert ar==g['result']['routes']['smart']
                changes.append({k:a[k] for k in ('index','geometry','depth','parameters','input_sha256')}|{'before':br,'after':ar,'oracle':a['result']['oracles']['smart']})
        report['seeds'][str(seed)]={'counts':{k:d['summary'] for k,d in data.items()},'provenance':{k:d['provenance'] for k,d in data.items()},'transitions':dict(transitions),'base_exact_preserved':preserved,'changed_cases':changes,'sanitized_routes':600}
    b=load(s/f'{args.before}-replay.json');a=load(s/f'{args.after}-replay.json');assert b['completed']==a['completed']==39
    assert b['provenance']['worker_sha256']==a['provenance']['worker_sha256']
    report['replay_provenance']={'before':b['provenance'],'after':a['provenance']}
    corpus=[];updates=[]
    for old,new in zip(b['replays'],a['replays']):
        assert old['path']==new['path'];path=Path(new['path']).resolve();assert path.is_relative_to(ROOT/'tests/fuzz_corpus/olmblur')
        saved=load(path);previous=next((h['previous_result'] for h in saved.get('C15_updates',[]) if h['stage']==args.after),saved['result'])
        assert old['result']==previous,path
        assert old['result']['oracles']==new['result']['oracles']
        assert old['result']['routes']['classic']==new['result']['routes']['classic']
        br=old['result']['routes']['smart'];ar=new['result']['routes']['smart']
        if br!=ar:
            assert br['status'] in ('mismatch','refusal') and ar['status']=='exact',path
            updates.append((path,saved,new['result']))
        corpus.append({'path':str(path.relative_to(ROOT)),'before':old['result'],'after':new['result']})
    report['corpus']=corpus;report['corpus_transitions']=dict(Counter(r['before']['routes']['smart']['status']+' -> '+r['after']['routes']['smart']['status'] for r in corpus))
    matrix=load(s/f'matrix-{args.after}.json');assert matrix['depth']==args.depth
    assert matrix['provenance']['after']['compiled_source_sha256']==report['source_sha256']
    assert all(r['after']['status']=='exact' for r in matrix['rows'])
    report['matrix']=matrix
    # Original trace evidence includes full output binding before stage interpretation.
    report['trace_before']=load(s/f'stages-before-{args.after}.json')
    report['trace_after']=load(s/f'stages-{args.after}.json')
    assert all(r['cached_binding'] for r in report['trace_before']['rows']+report['trace_after']['rows'])
    assert all(r['output_exact'] for r in report['trace_after']['rows'])
    report['retained']=retained(s)
    from verify_blur_retained_C12 import verify
    report['extended_retained']=verify(s)
    assert report['extended_retained']['status']['status']=='ok'
    assert len(report['extended_retained']['lines'])==80
    assert all('exact=1' in line for line in report['extended_retained']['lines'])
    for name in ('matrix-off-'+args.after,'coeff-'+args.after):
        path=s/(name+'.json')
        if path.exists():report[name]=load(path)
    report['corpus_updates']=[str(v[0].relative_to(ROOT)) for v in updates]
    if args.rebaseline:
        for path,saved,result in updates:
            if saved['result']==result:continue
            saved.setdefault('C15_updates',[]).append({'stage':args.after,'previous_result':saved['result'],'report':'orchestra/reports/C15-olmblur-smart-r4.md'})
            saved['result']=result;path.write_text(json.dumps(saved,indent=2,sort_keys=True)+'\n')
    args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print({k:v['transitions'] for k,v in report['seeds'].items()});print('corpus',report['corpus_transitions'],'retained',len(report['retained']['lines']))

if __name__=='__main__':main()
