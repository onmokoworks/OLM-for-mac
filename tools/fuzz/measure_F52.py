#!/usr/bin/env python3
"""F52 bounded downsample qualification; serial, no corpus or plugin writes."""
import argparse, importlib, json, random, time
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from core import case_seed, evaluate, sha
from run import main_checkout
ROOT=Path(__file__).resolve().parents[2]
S=ROOT/'orchestra/state/F52-oracle-downsample-geometry'
def sampled(case):
    rng=random.Random(case_seed(case['seed'],case['index'])^0xF52)
    ds=rng.choice([((1,1),(1,1)),((1,2),(1,2)),((1,3),(1,3)),((1,4),(1,4)),((1,8),(1,8)),((1,2),(1,3))])
    full=case['geometry']; shape=[(n*r[0]+r[1]-1)//r[1] for n,r in zip(full,ds)]
    ps=case['depth']//8*4; w,h=shape
    pixels=b''.join(case['pixels'][y*full[0]*ps:(y*full[0]+w)*ps] for y in range(h))
    case.update(full_geometry=full,geometry=shape,downsample=ds,pixels=pixels)
    for p in case['parameters']:
        if p['kind']=='p': p['value']=[round(v*r[0]/r[1]*65536)/65536 for v,r in zip(p['value'],ds)]
    return case

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--plugin',choices=['olmblur','olmcolorkey','olmdirectionalblur'],required=True)
    ap.add_argument('--n',type=int,default=100)
    ap.add_argument('--build-only',action='store_true')
    a=ap.parse_args(); s=S/a.plugin;s.mkdir(parents=True,exist_ok=True)
    worker=Path.home()/'.cache/olm-emu/worker-F52-geom/aex-guest-worker'
    options=SimpleNamespace(max_size=256,case_timeout=10,main=main_checkout(),worker=worker)
    adapter=importlib.import_module('adapters.'+a.plugin).Adapter(options)
    adapter.env.update(TMPDIR=str(s),TMP=str(s),TEMP=str(s))
    deadline=time.monotonic()+3600
    binary=s/'mac'
    adapter.binary,dependencies=adapter.build(s,deadline)
    if a.build_only: print('Built',binary,flush=True);return
    counts=Counter(); originals=Counter();tags=Counter()
    with (s/'results.jsonl').open('w') as f:
        for i in range(a.n):
            case=sampled(adapter.generate(1,i)); attr={}; start=time.monotonic()
            result=evaluate(adapter,case,s,deadline,attr)
            row={k:v for k,v in case.items() if k!='pixels'}
            row.update(input_sha256=sha(case['pixels']),result=result,refusals=attr,seconds=time.monotonic()-start)
            f.write(json.dumps(row)+'\n');f.flush()
            for route,r in result['routes'].items(): counts[(route,r['status'])]+=1
            for route,r in result.get('oracles',{'smart':result['oracle']}).items(): originals[(route,r['status'])]+=1
            for route,values in attr.items():
                for v in values: tags[(route,v)]+=1
            print(i,{k:v['status'] for k,v in result['routes'].items()},flush=True)
    report=dict(n=a.n,seed=1,aex_sha256=sha(adapter.aex.read_bytes()),dependencies={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in [*dependencies,ROOT/'tools/fuzz/harnesses/geometry.hpp',ROOT/'tools/fuzz/adapters/public.py']},worker_sha256=sha(worker.read_bytes()),candidate_sha256=sha(binary.read_bytes()),routes={str(k):v for k,v in counts.items()},originals={str(k):v for k,v in originals.items()},tags={str(k):v for k,v in tags.items()})
    (s/'summary.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
if __name__=='__main__':main()
