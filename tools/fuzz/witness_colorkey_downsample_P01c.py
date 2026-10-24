#!/usr/bin/env python3
"""Independent ColorKey downsample witnesses through PreRender + SmartRender."""
import itertools
import json
import os
from pathlib import Path
import struct
import time
from types import SimpleNamespace
from adapters.olmcolorkey import Adapter
from core import raw_diff, sha
from run import main_checkout

ROOT = Path(__file__).resolve().parents[2]
S = ROOT/'orchestra/state/P01c-colorkey-downsample/witnesses'

def main():
    S.mkdir(parents=True, exist_ok=True)
    os.environ.update(TMPDIR=str(S), TMP=str(S), TEMP=str(S))
    adapter = Adapter(SimpleNamespace(max_size=256, case_timeout=10, main=main_checkout(),
        worker=Path.home()/'.cache/olm-emu/worker-F52-geom/aex-guest-worker'))
    deadline = time.monotonic()+1800
    provenance = adapter.prepare(S, deadline)
    scales = [((1,2),(1,2)), ((1,4),(1,4)), ((1,2),(1,3)), ((1,3),(1,2)), ((2,3),(2,3))]
    modes = [(0,5,2), (-3,2.5,1), (3,4,3), (0,4000,2), (-3,0,2), (3,0,2)]
    failures = []; count = 0
    with (S/'results.jsonl').open('w') as out:
        for depth, shape, ds, metric, mode in itertools.product(
                (8,16,32), ((7,5),(1,7),(7,1)), scales, (1,2,3), modes):
            w,h=shape
            case=adapter.generate(20261024,0)
            case.update(geometry=[w,h],full_geometry=[w*ds[0][1]//ds[0][0],h*ds[1][1]//ds[1][0]],
                depth=depth,downsample=ds,parameters=adapter.defaults(w,h),input_padding=8,output_padding=8)
            # Choose full sizes whose ceil-scaled allocation is exactly the witness.
            case['full_geometry']=[(n-1)*r[1]//r[0]+1 for n,r in zip(shape,ds)]
            settings={1:0,2:0,4:0,5:1,6:1,7:0,8:0,9:0,10:0,11:0,
                14:mode[0],15:metric,18:mode[1],19:metric,20:mode[2],22:1,23:0,
                24:1,25:0,26:[255,0,0,0]}
            for p in case['parameters']:
                if p['slot'] in settings:p['value']=settings[p['slot']]
            pixels=[]
            for y in range(h):
                for x in range(w):
                    color = 0 if (x+2*y)%5 in (0,1) else 255
                    rgba=[(255,128,63)[(x+y)%3],color,color,color]
                    pixels.append(bytes(rgba) if depth==8 else struct.pack('<4H',*((v*32768+127)//255 for v in rgba))
                                  if depth==16 else struct.pack('<4f',*(v/255 for v in rgba)))
            case['pixels']=b''.join(pixels)
            oracle,ref=adapter.oracle(case,S,deadline,'smart')
            candidate,raw,*_=adapter.candidate(case,S,'smart',deadline)
            exact=oracle['status']=='ok' and candidate['status']=='ok' and ref==raw
            row=dict(depth=depth,geometry=shape,full_geometry=case['full_geometry'],downsample=ds,
                metric=metric,mode=mode,input_sha256=sha(case['pixels']),reference_sha256=sha(ref),
                candidate_sha256=sha(raw),exact=exact)
            if not exact:
                row.update(oracle=oracle,candidate=candidate,diff=raw_diff(ref,raw,depth))
                failures.append(row)
            out.write(json.dumps(row)+'\n');out.flush();count+=1
            if count%90==0:print(count,'failures',len(failures),flush=True)
    report=dict(count=count,exact=count-len(failures),failures=failures,provenance=provenance)
    (S/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
    print(count,'exact',count-len(failures),'mismatches',len(failures))
    assert not failures

if __name__=='__main__':main()
