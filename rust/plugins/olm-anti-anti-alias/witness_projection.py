"""Exact ABI witness of the production autoported projection; no expected-output tables."""
import argparse
import json
from pathlib import Path
import random
import struct
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'tools/autoport'))
import autoport as a
from vectors import blob,ptr,pack
from process import witness_module

def f32(x):return struct.unpack('<f',struct.pack('<f',x))[0]
def pixel(x):return blob(struct.pack('<4f',*x))
def run(candidate,out):
    out.mkdir(parents=True,exist_ok=False);w=witness_module()
    original=Path(json.loads((HERE/'scaffold.json').read_text())['original']['path'])
    rng=random.Random(20261113); reports=[]
    for batch in range(4):
        rows=[]
        for index in range(256):
            ca=[1.0]+[f32(rng.random()) for _ in range(3)]
            cb=[1.0]+[f32(rng.random()) for _ in range(3)]
            p=[1.0]+[f32(rng.random()) for _ in range(3)]
            if index%8==0:cb=ca.copy()
            if index%8==1:p=ca.copy()
            if index%8==2:p=cb.copy()
            if index%8==3:p=[f32((x+y)*0.5) for x,y in zip(ca,cb)]
            d=[0.0]+[f32(cb[k]-ca[k]) for k in range(1,4)]
            length=f32(f32(f32(d[2]*d[2])+f32(d[1]*d[1]))+f32(d[3]*d[3]))
            buffers=dict(p=pixel(p),a=pixel(ca),b=pixel(cb),d=pixel(d),t=blob(b'\xa5'*4),u=blob(b'\xa5'*16),v=blob(b'\xa5'*16),da=blob(b'\xa5'*4),db=blob(b'\xa5'*4))
            rows.append(dict(label=f'projection-{batch}-{index}',buffers=buffers,args=[ptr(n) for n in ['p','t','a','b','u','v','da','db','d']]+[dict(type='f32',value=length)],return_='f32'))
            rows[-1]['return']=rows[-1].pop('return_')
        root=out/f'batch-{batch}';root.mkdir()
        spec=pack(rows,original,0xa630,'fma')
        for side,module,rva in [('original',original,0xa630),('rust',candidate,a.exported_rva(candidate,'autoport_18000a630'))]:
            submitted=pack(rows,module,rva,'fma');m=w.run(submitted,root/side,timeout=60)
            if m['classification']!='success' or not m['process']['cleanup_verified']:raise RuntimeError(m)
        failure=a.compare_witness(root/'original',root/'rust',spec)
        reports.append(dict(cases=len(rows),failure=failure));print(reports[-1],flush=True)
    a.write(out/'summary.json',dict(original_sha256=a.digest(original),candidate_sha256=a.digest(candidate),batches=reports))
    return int(any(x['failure'] for x in reports))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--out',type=Path,required=True);x=p.parse_args()
    raise SystemExit(run(x.candidate.resolve(),x.out.resolve()))
