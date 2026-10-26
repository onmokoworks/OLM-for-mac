#!/usr/bin/env python3
"""Replay saved Mac routes, comparing raw hashes, errors and output rectangles.

This deliberately does not rerun or relabel the recorded AEX oracle verdicts.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time
import native_diff as nd

ROOT=Path(__file__).resolve().parents[2]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--plugin',required=True,choices=nd.PLUGINS)
    p.add_argument('--scratch',type=Path,required=True)
    args=p.parse_args();out=args.scratch.resolve()
    if not out.is_relative_to(ROOT/'orchestra/state'):p.error('scratch must be in orchestra/state')
    out.mkdir(parents=True,exist_ok=True)
    a=nd.adapter_at(ROOT,args.plugin,ROOT.parent.parent,180)
    a.env.update(TMPDIR=str(out),TMP=str(out),TEMP=str(out),MallocScribble='1',OLM_PARALLEL_MAX='1')
    a.binary,_=a.build(out,time.monotonic()+600)
    from core import load_corpus
    paths=sorted((ROOT/'tests/fuzz_corpus'/args.plugin).rglob('*.json'))
    counts={'cases':0,'routes':0,'matching':0};differences=[]
    with (out/'replay.jsonl').open('w') as log:
        for path in paths:
            saved=json.loads(path.read_text());a.max_size=saved['max_size']
            case,saved=load_corpus(path,a)
            for route,expected in saved['result']['routes'].items():
                result,raw,*_=a.candidate(case,out,route,time.monotonic()+180)
                if result['status']=='ok':result['raw_sha256']=hashlib.sha256(raw).hexdigest()
                fields=('error','raw_sha256','output_rect')
                expected_subset={k:expected.get(k) for k in fields}
                actual_subset={k:result.get(k) for k in fields}
                successful={'exact','mismatch','uncompared','no_write','no_write_violation'}
                expected_subset['status']='ok' if expected['status'] in successful else expected['status']
                actual_subset['status']=result['status']
                if 'COUNTS' in expected.get('metadata',{}):
                    expected_subset['callback_counts']=expected['metadata']['COUNTS']
                    actual_subset['callback_counts']=result.get('metadata',{}).get('COUNTS')
                same=expected_subset==actual_subset
                counts['routes']+=1;counts['matching']+=same
                record=dict(path=str(path.relative_to(ROOT)),route=route,matches_saved=same,expected=expected_subset,actual=actual_subset,status=result['status'])
                log.write(json.dumps(record)+'\n');log.flush()
                if not same:differences.append(record)
            counts['cases']+=1
    summary=dict(counts=counts,differences=differences)
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))
    return int(bool(differences))

if __name__=='__main__':raise SystemExit(main())
