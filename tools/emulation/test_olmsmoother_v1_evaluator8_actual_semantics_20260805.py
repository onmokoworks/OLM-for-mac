#!/usr/bin/env python3
"""Pin all five PF8 interpolation evaluators to float32 object semantics."""
import hashlib,json,math,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/emulation'));from aex_loader import AexLoader
AEX=ROOT/'plugins_2025/OLMSmoother.aex';SHA='6206f601b645dc915b78269ae403e5cbee642ac2812e320d85838ec72135fe82'
FUNCS=(0x1800010c0,0x1800010e0,0x180001110,0x180001150,0x180001180);TS=(-.25,0.,.125,.5,1.,1.25)
def f(x):return struct.unpack('<f',struct.pack('<f',x))[0]
def add(a,b):return f(f(a)+f(b))
def sub(a,b):return f(f(a)-f(b))
def mul(a,b):return f(f(a)*f(b))
def div(a,b):return f(f(a)/f(b))
def eval_sem(kind,t,o,p0,p1,p2):
 t,o,p0,p1,p2=map(f,(t,o,p0,p1,p2))
 linear=lambda:add(mul(sub(p0,o),t),o)
 if kind==0:return linear()
 if kind==1:return p1 if t==f(1) else linear()
 if kind==2:return p2 if t==f(1) else (p1 if t==f(0) else linear())
 if kind==3:return p1 if t==f(0) else linear()
 if t<=p1:return add(mul(div(sub(p0,o),p1),t),o)
 slope=div(sub(p2,p0),sub(f(1),p1));return sub(add(mul(slope,t),p2),slope)
def main():
 assert hashlib.sha256(AEX.read_bytes()).hexdigest()==SHA;l=AexLoader(str(AEX),verbose=False,fast=True);mis=[];vals=(.17,.83,.31,.94)
 for k,fn in enumerate(FUNCS):
  obj=l.host_alloc(0x20,align=16);raw=bytearray(0x20);struct.pack_into('<ffff',raw,8,*vals);struct.pack_into('<f',raw,0x18,vals[3]);l.write_bytes(obj,bytes(raw))
  for t in TS:
   a=l.call_function(fn,[obj,0],float_args={1:t},max_instructions=1000)['xmm0'][:4];g=struct.pack('<f',eval_sem(k,t,*vals))
   if a!=g:mis.append((hex(fn),t,a.hex(),g.hex()))
 print(json.dumps({'status':'exact' if not mis else 'fail','calls':len(FUNCS)*len(TS),'mismatch_count':len(mis),'first':mis[:3]},indent=2));assert not mis
if __name__=='__main__':main()
