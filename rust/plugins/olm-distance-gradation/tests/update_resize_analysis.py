"""Localize recorded cvResize arithmetic; variants are diagnostic, not fitted output."""
import json
from pathlib import Path
import struct
import sys
import numpy as np
cap=Path(sys.argv[1])
for path in sorted(cap.glob('calls/*/record.json')):
    r=json.loads(path.read_text())
    if r['name']!='resize' or r['buffers'][0]['image']['depth']!=32: continue
    def plane(b,phase):
        w,h=struct.unpack_from('<ii',bytes.fromhex(b['image']['header']),40)
        raw=(cap/b[phase]['file']).read_bytes()
        return np.frombuffer(b''.join(raw[y*b['stride']:y*b['stride']+w*4] for y in range(h)),dtype='<f4').reshape(h,w)
    src=plane(r['buffers'][0],'before'); expected=plane(r['buffers'][1],'after')
    h,w=expected.shape; rh,rw=src.shape
    def blend(a,b,t,mode):
        one=np.float32(1-t); t=np.float32(t)
        if mode==0: return np.float32(a*one+b*t)
        if mode==1: return np.float32(np.float64(a)*np.float64(one)+np.float64(np.float32(b*t)))
        if mode==2: return np.float32(np.float64(b)*np.float64(t)+np.float64(np.float32(a*one)))
        if mode==3: return np.float32(a+np.float32(np.float32(b-a)*t))
        return np.float32(np.float64(np.float32(b-a))*np.float64(t)+np.float64(a))
    for hf in range(5):
        for vf in range(5):
            out=np.zeros_like(expected)
            for y in range(h):
                fy=(y+.5)*(rh/h)-.5; iy=int(np.floor(fy)); fy=fy-iy
                y0=max(0,min(rh-1,iy)); y1=max(0,min(rh-1,iy+1))
                for x in range(w):
                    fx=(x+.5)*(rw/w)-.5; ix=int(np.floor(fx)); fx=fx-ix
                    if ix<0:ix=0;fx=np.float32(0)
                    if ix>=rw-1:ix=rw-1;fx=np.float32(0)
                    a=blend(src[y0,ix],src[y0,min(ix+1,rw-1)],fx,hf)
                    b=blend(src[y1,ix],src[y1,min(ix+1,rw-1)],fx,hf)
                    out[y,x]=blend(a,b,fy,vf)
            bad=out.view('u4')!=expected.view('u4')
            print(r['sequence'],hf,vf,int(bad.sum()))
            if hf==4 and vf==4:
                for y,x in zip(*np.where(bad)):
                    print('difference',x,y,float(out[y,x]),float(expected[y,x]))
