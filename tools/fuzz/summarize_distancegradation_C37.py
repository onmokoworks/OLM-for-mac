#!/usr/bin/env python3
"""Retain C37 Smart identities and measured results without large Classic data."""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--scratch',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--name',action='append',required=True)
    args=p.parse_args()
    result={'schema':'olm.dg-C37-evidence/1','measurements':{}}
    for name in args.name:
        path=args.scratch/(name+'.json');data=json.loads(path.read_text())
        entry={'report_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
        for key,value in data.items():
            if key in ('clusters','cases'):continue
            entry[key]=value
        if 'cases' in data:
            entry['cases']=[{k:r[k] for k in ('index','input_sha256','geometry','depth','profile','parameters','refusal_guards') if k in r} |
                {'smart':r['result']['routes']['smart'],'oracle':r['result']['oracles']['smart']} for r in data['cases']]
        result['measurements'][name]=entry
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')

if __name__=='__main__':main()
