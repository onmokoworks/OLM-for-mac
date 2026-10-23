#!/usr/bin/env python3
"""Compact C31 evidence without changing verdicts or corpus expectations."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--scratch',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--phase',choices=['power','mask','writer'],default='power')
    args=p.parse_args()
    result={'schema':'olm.dg-C31-evidence/1','measurements':{}}
    names = {'power':('base','fresh','gate','power-bilateral-rejected','power','power-final','verify-timeout','verify','replay'),
             'mask':('after-power','mask','mask-trace','mask-trace-after','mask-verify','mask-hdr-residual'),
             'writer':('writer','writer-trace','writer-trace-after','writer-verify','final','final-fresh','final-replay')}
    for name in names[args.phase]:
        path=args.scratch/(name+'.json')
        data=json.loads(path.read_text())
        out={'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
        for key in ('schema','status','summary','completed','seed','source_sha256','candidate_sha256','source_sha256','before_ref','provenance','replay_matches_saved','requested','reference_sha256'):
            if key in data:out[key]=data[key]
        if 'trace' in name:out['trace']=data
        if 'cases' in data:
            out['cases']=[{'index':r['index'],'input_sha256':r['input_sha256'],'smart':r['result']['routes']['smart'],'oracle':r['result']['oracles']['smart']} for r in data['cases']]
        if 'rows' in data:
            out['rows']=[{k:v for k,v in row.items() if k in ('index','label','geometry','profile','input_sha256','before','candidate','sanitized_equal','exact','oracle_sha256','before_sha256','candidate_sha256','sanitized_sha256','sha256','after','diff')} for row in data['rows']]
            out['exact_count']=sum(bool(r.get('exact')) for r in data['rows'])
        for key in ('campaigns','corpus','negative'):
            if key in data:out[key]=data[key]
        result['measurements'][name]=out
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')


if __name__=='__main__':main()
