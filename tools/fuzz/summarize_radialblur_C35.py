#!/usr/bin/env python3
"""Compact C35 measurements without changing expectations or corpus files."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--state',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args(); root=args.state
    result={'campaigns':{},'comparisons':{},'matrices':{},'corpus':{}}
    campaigns={}
    for name,rel in {'base1':'base.json','base5':'base-seed5/campaign.json',
                     'negative1':'negative-seed1/campaign.json','negative5':'negative-seed5/campaign.json',
                     'rotation1':'rotation-seed1/campaign.json','rotation5':'rotation-seed5/campaign.json'}.items():
        path=root/rel
        if not path.exists(): continue
        data=json.loads(path.read_text());campaigns[name]=data
        rows=data['cases']
        result['campaigns'][name]=dict(report_sha256=sha(path),provenance=data['provenance'],
            counts=dict(Counter(r['result']['routes']['smart']['status'] for r in rows)),
            original_counts=dict(Counter(r['result']['oracles']['smart']['status'] for r in rows)),
            failures=data.get('failures',[]),refusal_error_changes=data.get('refusal_error_changes',[]),
            uncompared=[dict(index=r['index'],oracle=r['result']['oracles']['smart']) for r in rows if r['result']['routes']['smart']['status']=='uncompared'])
    for before,after in [('base1','negative1'),('base5','negative5'),('negative1','rotation1'),('negative5','rotation5')]:
        if before not in campaigns or after not in campaigns:continue
        old=campaigns[before]['cases'];new=campaigns[after]['cases'];assert len(old)==len(new)
        preserved=[];admitted=[];lost=[]
        for x,y in zip(old,new):
            assert x['index']==y['index'] and x['input_sha256']==y['input_sha256']
            a=x['result']['routes']['smart'];b=y['result']['routes']['smart']
            if a['status']=='exact':
                (preserved if b['status']=='exact' and a['raw_sha256']==b['raw_sha256'] else lost).append(x['index'])
            if a['status']=='refusal' and b['status']=='exact':admitted.append(dict(index=x['index'],input_sha256=x['input_sha256'],after=b,oracle=y['result']['oracles']['smart']))
        result['comparisons'][before+'->'+after]=dict(preserved_exact=len(preserved),lost_exact=lost,admitted=admitted)
        assert not lost
    for name,rel in [('negative','negative-matrix-final/matrix/report.json'),('rotation','rotation-matrix/report.json')]:
        path=root/rel
        if not path.exists():continue
        d=json.loads(path.read_text()); rows=d.get('rows',d.get('independent',[])); layouts=[l for r in rows for l in r['layouts']]
        result['matrices'][name]=dict(report_sha256=sha(path),provenance=d['provenance'],references=len(rows),layouts=len(layouts),
            exact=sum(l['exact'] for l in layouts),clean=sum(l['clean'] for l in layouts),failures=d['failures'],
            undefined_clean_refusals=sum(not r.get('domain',{'defined':True})['defined'] and l['passed'] for r in rows for l in r['layouts']))
    for name in ['before','negative','rotation']:
        path=root/('corpus-'+name)/'replay.json'
        if path.exists():
            d=json.loads(path.read_text());result['corpus'][name]=dict(report_sha256=sha(path),rows=len(d['replays']),matches_saved=d['replay_matches_saved'],
                result_sha256=hashlib.sha256(json.dumps([r['result'] for r in d['replays']],sort_keys=True).encode()).hexdigest())
    for name in ['inverse-before','inverse-after','inverse-production']:
        path=root/name/'report.json'
        if path.exists():result[name]=json.loads(path.read_text())
    result['rejected'] = {}
    for name in ['nonfinite-zero-taps','nonfinite-cancelled-rgb','nonfinite-x86-generated']:
        path=root/name/'campaign.json'
        if path.exists():
            d=json.loads(path.read_text())
            result['rejected'][name]=dict(report_sha256=sha(path),provenance=d['provenance'],failures=d['failures'],
                clean=sum(not r['result']['routes']['smart'].get('sanitizer') for r in d['cases']),
                mismatches=[dict(index=r['index'],diff=r['result']['routes']['smart']['diff']) for r in d['cases'] if r['result']['routes']['smart']['status']=='mismatch'])
    path=root/'source-leaf-final/report.json'
    if path.exists():result['source_leaf']=json.loads(path.read_text())
    path=root/'final.json'
    if path.exists():
        d=json.loads(path.read_text());qualified={r['index']:r for r in campaigns['rotation1']['cases']}
        baseline={r['index']:r for r in campaigns['base1']['cases']}
        preserved=[];drift=[]
        for r in d['cases']:
            i=r['index'];actual=r['result']['routes']['smart'];expected=qualified[i]['result']['routes']['smart']
            if baseline[i]['result']['routes']['smart']['status']=='exact' and actual.get('raw_sha256')==baseline[i]['result']['routes']['smart'].get('raw_sha256'):preserved.append(i)
            if actual.get('raw_sha256')!=expected.get('raw_sha256'):drift.append(i)
        result['final']=dict(report_sha256=sha(path),counts=dict(Counter(r['result']['routes']['smart']['status'] for r in d['cases'])),
            baseline_exact_hashes_preserved=len(preserved),qualified_hash_drift=drift,
            uncompared=[dict(index=r['index'],oracle=r['result']['oracles']['smart']) for r in d['cases'] if r['result']['routes']['smart']['status']=='uncompared'])
        assert not drift
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print('campaigns',[(n,d['counts']) for n,d in result['campaigns'].items()])
    print('corpus',result['corpus'])


if __name__=='__main__':main()
