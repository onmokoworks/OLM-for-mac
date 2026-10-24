#!/usr/bin/env python3
"""Write deterministic fuzz-adapter SDR inputs; keep source ARGB for I/O checks.
Requires numpy, tifffile and OpenEXR in a scratch virtual environment.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import numpy as np
import tifffile
import OpenEXR

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/fuzz'))
from adapters.olmblur import Adapter


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path)
    args=p.parse_args();out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    a=Adapter(SimpleNamespace(max_size=32,case_timeout=10,main=ROOT,worker=Path.home()/'.cache/olm-emu/worker-F51-x86host/plugin-host'))
    rows=[]
    for depth in (8,16,32):
        for index in range(10000):
            c=a.generate(1,index)
            if c['depth']==depth and c['profile']=='sdr' and min(c['geometry'])>=4:break
        else: raise RuntimeError('no suitable deterministic input')
        w,h=c['geometry'];raw=out/f'input-{depth}.argb';raw.write_bytes(c['pixels'])
        pix=np.frombuffer(c['pixels'],dtype={8:'u1',16:'<u2',32:'<f4'}[depth]).reshape(h,w,4)
        rgba=pix[:,:,[1,2,3,0]]
        if depth<32:
            # Full-range file encoding, not a claim about AE import rounding.
            encoded=(rgba.astype(np.uint64)*65535//(255 if depth==8 else 32768)).astype(np.uint16)
            file=out/f'input-{depth}.tif'
            tifffile.imwrite(file,encoded,photometric='rgb',extrasamples=['unassalpha'],metadata=None)
        else:
            file=out/'input-32.exr'
            OpenEXR.File({'compression':OpenEXR.NO_COMPRESSION,'type':OpenEXR.scanlineimage},
                        {k:np.ascontiguousarray(rgba[:,:,i]) for i,k in enumerate('RGBA')}).write(str(file))
        rows.append(dict(depth=depth,width=w,height=h,path=str(file),raw=str(raw),
                         seed=1,index=index,generator='adapters.olmblur.Adapter.generate',
                         source_sha256=hashlib.sha256(c['pixels']).hexdigest(),
                         file_sha256=hashlib.sha256(file.read_bytes()).hexdigest()))
    (out/'inputs.json').write_text(json.dumps(rows,indent=2)+'\n')
    print(json.dumps(rows,indent=2))

if __name__=='__main__': main()
