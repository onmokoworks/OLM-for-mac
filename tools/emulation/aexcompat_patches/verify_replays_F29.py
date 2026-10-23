#!/usr/bin/env python3
"""Compare every saved corpus and seed-1 result, then recapture changed raw words.
No expected outputs are modified. Raw recapture verifies hashes from both runs.
"""
import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import time
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[3]
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT/'tools/fuzz'))
from core import load_corpus
CACHE=Path.home()/'.cache/olm-emu'
WORKERS=[Path('/Users/onmk/Documents/Codex/2026-10-05/task-3/AEXCompat-containment/guest/target/release/aex-guest-worker'),CACHE/'worker-F29-ssenan/aex-guest-worker']

def sha(data):return hashlib.sha256(data).hexdigest()
def nan(x):return x&0x7f800000==0x7f800000 and x&0x7fffff!=0

def adapter(plugin,worker,max_size=256,timeout=10):
    cls=importlib.import_module('adapters.'+plugin).Adapter
    return cls(SimpleNamespace(max_size=max_size,case_timeout=timeout,main=ROOT.parents[1],worker=worker))

def capture(case,plugin,old,new,directory):
    changed=[]
    before=old.get('oracles',{'smart':old['oracle']});after=new.get('oracles',{'smart':new['oracle']})
    for route in before:
        if before[route]==after[route]:continue
        assert before[route]['status']==after[route]['status']=='ok',(plugin,route,before[route],after[route])
        raws=[]
        for worker,expected in zip(WORKERS,[before[route],after[route]]):
            a=adapter(plugin,worker);a.env.update(TMPDIR=str(directory),TMP=str(directory),TEMP=str(directory))
            status,raw=a.oracle(case,directory,time.monotonic()+120,route)
            assert status['status']=='ok' and sha(raw)==expected['raw_sha256'],(status,sha(raw),expected)
            raws.append(raw)
        assert case['depth']==32 and len(raws[0])==len(raws[1])
        words=[dict(index=i,before=f'{a:08x}',after=f'{b:08x}') for i,((a,),(b,)) in enumerate(zip(struct.iter_unpack('<I',raws[0]),struct.iter_unpack('<I',raws[1]))) if a!=b]
        assert words and all(nan(int(r['before'],16)) and nan(int(r['after'],16)) for r in words),words
        changed.append(dict(route=route,before_sha256=sha(raws[0]),after_sha256=sha(raws[1]),
            different_bytes=sum(a!=b for a,b in zip(*raws)),different_words=len(words),first_word=words[0],words=words))
    assert changed,'Unexpected non-oracle result change'
    return dict(input_nan_words=sum(nan(x) for x, in struct.iter_unpack('<I',case['pixels'])),routes=changed)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--scratch',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args();s=args.scratch.resolve();assert s.is_relative_to(ROOT/'orchestra/state')
    os.environ.update(TMPDIR=str(s),TMP=str(s),TEMP=str(s))
    summaries=[];changes=[];finite_cases=0;total=0;hashes={}
    for corpus in sorted((ROOT/'tests/fuzz_corpus').iterdir()):
        if not corpus.is_dir() or not list(corpus.glob('*.json')):continue
        reports=[]
        for variant in ('baseline','patched'):
            p=s/f'{variant}-{corpus.name}-replay.json';hashes[p.name]=sha(p.read_bytes());r=json.loads(p.read_text());reports.append(r)
            assert r['status']=='replay_complete' and r['completed']==len(list(corpus.glob('*.json')))
            expected_worker=sha(WORKERS[0 if variant=='baseline' else 1].read_bytes())
            assert all(g['provenance']['worker_sha256']==expected_worker for g in r['replay_groups'])
        old,new=reports;assert len(old['replays'])==len(new['replays']);moved=0
        for a,b in zip(old['replays'],new['replays']):
            assert a['path']==b['path']; path=ROOT/a['path']; saved=json.loads(path.read_text()); plugin=saved['plugin']
            case,_=load_corpus(path,adapter(plugin,WORKERS[0],saved['max_size']))
            isnan=case['depth']==32 and any(nan(x) for x, in struct.iter_unpack('<I',case['pixels']))
            finite_cases+=not isnan;total+=1
            if a['result']==b['result']:continue
            moved+=1;assert isnan,'Changed corpus case without NaN input'
            with tempfile.TemporaryDirectory(dir=s,prefix='raw-change-') as d:detail=capture(case,plugin,a['result'],b['result'],Path(d))
            changes.append(dict(kind='corpus',case=a['path'],detail=detail,before=a['result'],after=b['result']))
        summaries.append(dict(corpus=corpus.name,rows=old['completed'],changed=moved,
            baseline_matches_saved=sum(r['matches_saved'] for r in old['replays']),patched_matches_saved=sum(r['matches_saved'] for r in new['replays'])))
    campaigns=[]
    for variant in ('baseline','patched'):
        p=s/f'{variant}-olmblur-seed1.json';hashes[p.name]=sha(p.read_bytes());r=json.loads(p.read_text());assert r['status']=='complete' and r['completed']==300
        assert r['provenance']['worker_sha256']==sha(WORKERS[0 if variant=='baseline' else 1].read_bytes())
        campaigns.append(r)
    a,b=campaigns;candidate_changes=[]
    for x,y in zip(a['cases'],b['cases']):
        assert x['index']==y['index'] and x['input_sha256']==y['input_sha256']
        for route in x['result']['routes']:
            oldroute=x['result']['routes'][route];newroute=y['result']['routes'][route]
            assert oldroute.get('raw_sha256')==newroute.get('raw_sha256')
            if oldroute['status']!=newroute['status']:candidate_changes.append(dict(index=x['index'],route=route,before=oldroute['status'],after=newroute['status']))
        if x['result']==y['result']:continue
        case=adapter('olmblur',WORKERS[0]).generate(1,x['index']);assert sha(case['pixels'])==x['input_sha256']
        with tempfile.TemporaryDirectory(dir=s,prefix='raw-change-') as d:detail=capture(case,'olmblur',x['result'],y['result'],Path(d))
        changes.append(dict(kind='seed1',case=x['index'],detail=detail,before=x['result'],after=y['result']))
    out=dict(corpus_rows=total,corpus_without_input_nan=finite_cases,corpora=summaries,
        seed1_before=a['summary'],seed1_after=b['summary'],candidate_status_changes=candidate_changes,
        changed_cases=changes,report_sha256=hashes,worker_sha256=[sha(w.read_bytes()) for w in WORKERS])
    args.output.write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k not in ('changed_cases','report_sha256')},sort_keys=True))
    print('Changed cases',[(c['kind'],c['case']) for c in changes])

if __name__=='__main__':main()
