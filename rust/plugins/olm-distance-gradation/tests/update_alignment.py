"""Check IPP sqrt address alignment against captured integer EDT distances.

This isolates arithmetic, not a second independent EDT implementation: squared
integer distances are recovered from the recorded float roots and range checked.
"""
import json
from pathlib import Path
import re
import struct
import sys
import numpy as np

crate = Path(__file__).resolve().parents[1]
cap = Path(sys.argv[1])
table = np.array([int(x,16) for x in re.findall(r'0x([0-9a-fA-F]{8})',
    (crate/'src/rsqrt_table.rs').read_text())],dtype=np.uint32)
assert len(table)==8192
def fma(a,b,c):
    return (np.asarray(a,dtype='f8')*np.asarray(b,dtype='f8')+np.asarray(c,dtype='f8')).astype('f4')
rows=[]
for path in sorted(cap.glob('calls/*/record.json')):
    rec=json.loads(path.read_text())
    if rec['name']!='distance': continue
    b=rec['buffers'][1]
    w,h=struct.unpack_from('<ii',bytes.fromhex(b['image']['header']),40)
    raw=(cap/b['after']['file']).read_bytes()
    expected=np.frombuffer(b''.join(raw[y*b['stride']:y*b['stride']+w*4] for y in range(h)),dtype='<f4').reshape(h,w)
    assert np.isfinite(expected).all() and expected.max()<1024
    squared=np.rint(np.float64(expected)**2).astype('f4')
    errors={}
    for base in (0,4):
        out=squared.copy()
        for y in range(h):
            x=0;prefix=min((8-(base+y*w)%8)%8,w)
            while x<w:
                n=prefix if x==0 and prefix else min(16,w-x)
                v=squared[y,x:x+n]
                if np.any(v==0): out[y,x:x+n]=np.sqrt(v)
                else:
                    bits=v.view('u4');exp=((bits>>23)&255).astype('i4');parity=(exp-127)&1
                    ix=parity*4096+((bits&0x7fffff)>>11)
                    r=(table[ix].astype('i4')-(((exp-127-parity)//2)<<23)).astype('u4').view('f4')
                    residual=fma(-(r*v),r,np.float32(1))
                    scale=fma(np.float32(.375),residual,np.float32(.5))
                    out[y,x:x+n]=v*fma(scale,r*residual,r)
                x+=n
        errors[str(base*4)]=int(np.sum(out.view('u4')!=expected.view('u4')))
    rows.append(dict(call=rec['sequence'],shape=[w,h],
        captured_address_mod_32=int(b['address'],16)%32,
        mismatching_words_by_address_mod_32=errors))
(cap/'alignment-analysis.json').write_text(json.dumps(rows,indent=2))
print(json.dumps(rows,indent=2))
