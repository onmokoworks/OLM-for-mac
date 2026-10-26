#!/usr/bin/env python3
"""Compare two guest workers directly; never build or execute an OLM candidate."""
import argparse, hashlib, importlib, json, os, re, shlex, sys, time
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools/fuzz'))
from core import load_corpus
from geometry import sample
MAIN=Path('/Users/onmk/Documents/Projects/Personal/OLM as')
def digest(b): return hashlib.sha256(b).hexdigest()
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--scratch-root',type=Path,default=ROOT/'orchestra/state/F54b-aexcompat-numeric-patches-upstream')
    ap.add_argument('--worker',type=Path,required=True)
    ap.add_argument('--baseline',type=Path,default=Path.home()/'.cache/olm-emu/worker-F53-geom/aex-guest-worker')
    ap.add_argument('--plugin',required=True)
    ap.add_argument('--mode',choices=['corpus','survey','witness','4k','hd32'],default='corpus')
    ap.add_argument('--n',type=int,default=100)
    ap.add_argument('--route', choices=['classic','smart','both'], default='both')
    ap.add_argument('--case-filter', default='')
    ap.add_argument('--tag', default='')
    ap.add_argument('--jobs',type=int,choices=(1,),default=1)
    args=ap.parse_args()
    scratch=args.scratch_root/f'{args.mode}-{args.plugin}{args.tag}'
    scratch.mkdir(parents=True,exist_ok=True)
    os.environ.update(TMPDIR=str(scratch),TMP=str(scratch),TEMP=str(scratch),PYTHONDONTWRITEBYTECODE='1')
    cls=importlib.import_module('adapters.'+args.plugin).Adapter
    adapters=[cls(SimpleNamespace(main=MAIN,worker=w,max_size=256,case_timeout=180)) for w in [args.baseline,args.worker]]
    if args.mode in ('4k','hd32'):
        wrapper=scratch/'timed-worker'
        wrapper.write_text('#!/bin/sh\nexec /usr/bin/time -l '+shlex.quote(str(args.worker.resolve()))+' "$@"\n')
        wrapper.chmod(0o755)
        adapters[1].worker=wrapper
    def cases():
        if args.mode=='corpus':
            for path in sorted((ROOT/'tests/fuzz_corpus').glob(args.plugin+'*/**/*.json')):
                if args.case_filter and args.case_filter not in str(path): continue
                if json.loads(path.read_text()).get('plugin') != args.plugin: continue
                for a in adapters:a.max_size=json.loads(path.read_text())['max_size']
                yield str(path.relative_to(ROOT/'tests/fuzz_corpus')),load_corpus(path,adapters[0])[0]
        elif args.mode=='survey':
            for i in range(args.n):yield str(i),sample(adapters[0].generate(1,i),'realistic-v2')
        elif args.mode in ('4k','hd32'):
            for depth in ([32] if args.mode=='hd32' else [8,16,32]):
                # Deterministic constant finite ARGB, ordinary declared defaults.
                import struct
                pixel={8:bytes([255,71,29,103]),16:struct.pack('<4H',32768,9000,4000,12000),32:struct.pack('<4f',1.,.25,.125,.375)}[depth]
                c=adapters[0].generate(1,0)
                w,h=(1920,1080) if args.mode=='hd32' else (3840,2160)
                c.update(geometry=[w,h],depth=depth,pixels=pixel*(w*h),parameters=adapters[0].defaults(w,h))
                yield str(depth),c
        else:
            for i in range(4):
                c=sample(adapters[0].generate(1,i),'realistic-v2')
                rect=[0,0,20,15] if i<2 else [3,4,23,19]
                c.update(geometry=[20,15],full_geometry=[40,30],downsample=[[1,1],[1,1]],checkout_rect=rect,request_rect=rect,extent_hint=[0,0,20,15],depth=8,pixels=bytes((j*17+31)%256 for j in range(1200)),parameters=adapters[0].defaults(20,15),pixel_aspect=[1,1],rowbytes_padding=0,input_padding=0,output_padding=0)
                if args.plugin=='olmdirectionalblur':
                    for p in c['parameters']:
                        if p['slot']==5:p['value']=5
                if i%2:
                    del c['checkout_rect'];c['geometry']=[40,30];c['pixels']=bytes((j*17+31)%256 for j in range(4800));c['extent_hint']=[0,0,40,30]
                yield str(i),c
    base_cases=cases
    def routed_cases():
        for name,c in base_cases():
            routes=['classic'] if args.plugin=='olmsmoother' else (['classic','smart'] if args.route=='both' else [args.route])
            for route in routes:
                yield name+'/'+route,c,route
    counts={'cases':0,'equal':0,'different':0,'both_ok':0,'exact_ok':0,'matching_non_success':0,'byte_difference':0,'status_difference':0}
    with (scratch/'results.jsonl').open('w') as log:
        for name,c,route in routed_cases():
            result=[];raws=[]
            for a in (adapters[1:] if args.mode in ('4k','hd32') else adapters):
                observed=[]
                a.session_observed=lambda out,err:observed.append(err.decode(errors='replace'))
                start=time.monotonic()
                status,raw=a.oracle(c,scratch,start+190,route)
                result.append(dict(status=status,sha256=digest(raw),bytes=len(raw),seconds=time.monotonic()-start))
                if observed:
                    match=re.search(r"(\d+)\s+maximum resident set size",observed[-1])
                    if match:result[-1]['maximum_rss_bytes']=int(match[1])
                raws.append(raw)
            equal=len(result)==2 and result[0]['status']['status']==result[1]['status']['status'] and raws[0]==raws[1] and result[0]['status'].get('output_rect')==result[1]['status'].get('output_rect')
            row=dict(case=name,input_sha256=digest(c['pixels']),results=result,equal=equal)
            if len(result)==2:
                statuses=[r['status']['status'] for r in result]
                category=('exact_ok' if equal else 'byte_difference') if statuses==['ok','ok'] else ('matching_non_success' if statuses[0]==statuses[1] else 'status_difference')
                counts[category]+=1
                row['category']=category
            if len(raws)==2 and raws[0]!=raws[1]:
                offset=next((i for i,(x,y) in enumerate(zip(*raws)) if x!=y),min(map(len,raws)))
                row.update(first_mismatch=offset,expected_hex=raws[0][offset:offset+8].hex(),actual_hex=raws[1][offset:offset+8].hex())
            counts['cases']+=1;counts['equal' if equal else 'different']+=1;counts['both_ok']+=all(r['status']['status']=='ok' for r in result)
            log.write(json.dumps(row).replace(str(Path.home()),'<HOME>')+'\n');log.flush()
            print(name,[r['status']['status'] for r in result],equal,flush=True)
    summary=dict(counts,aex_sha256=digest(adapters[0].aex.read_bytes()),worker_sha256=digest(args.worker.read_bytes()),baseline_sha256=digest(args.baseline.read_bytes()))
    (scratch/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(summary)
    if counts['byte_difference'] or counts['status_difference']: raise SystemExit(1)
if __name__=='__main__':main()
