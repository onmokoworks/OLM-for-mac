#!/usr/bin/env python3
"""Independent whole-function interpreter for FUN_1800033d0."""
import hashlib,json,re,struct,sys
from pathlib import Path
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/emulation'));from aex_loader import AexLoader
AEX=ROOT/'plugins_2025/OLMSmoother.aex';SHA='6206f601b645dc915b78269ae403e5cbee642ac2812e320d85838ec72135fe82';CFG=ROOT/'refs/conformance/olmsmoother_v1_subhandler8_cfg_20260805.json';ENTRY=0x1800033d0;MOD=0x180000000;STK=0x700000000000;DIRS=(5,3,1,7)
BASES=('rax','rbx','rcx','rdx','rsi','rdi','rbp','rsp','r8','r9','r10','r11','r12','r13','r14','r15');A={}
for b in BASES:
 if b[1:].isdigit():A.update({b:(b,64),b+'d':(b,32),b+'w':(b,16),b+'b':(b,8)})
A.update({'rax':('rax',64),'eax':('rax',32),'ax':('rax',16),'al':('rax',8),'rbx':('rbx',64),'ebx':('rbx',32),'bx':('rbx',16),'bl':('rbx',8),'rcx':('rcx',64),'ecx':('rcx',32),'cx':('rcx',16),'cl':('rcx',8),'rdx':('rdx',64),'edx':('rdx',32),'dx':('rdx',16),'dl':('rdx',8),'rsi':('rsi',64),'esi':('rsi',32),'si':('rsi',16),'sil':('rsi',8),'rdi':('rdi',64),'edi':('rdi',32),'di':('rdi',16),'dil':('rdi',8),'rbp':('rbp',64),'ebp':('rbp',32),'bp':('rbp',16),'bpl':('rbp',8),'rsp':('rsp',64),'esp':('rsp',32),'sp':('rsp',16),'spl':('rsp',8)})
def split(s):
 d=0
 for i,c in enumerate(s):
  d+=c=='[';d-=c==']'
  if c==',' and d==0:return s[:i].strip(),s[i+1:].strip()
 return (s.strip(),)
class M:
 def __init__(self,l,I,args):
  self.l,self.I=l,I;self.r={x:0 for x in BASES};self.mem={};self.zf=self.sf=self.of=0;self.r['rsp']=STK+0x800
  self.r.update(zip(('rcx','rdx','r8','r9'),args[:4]));sp=self.r['rsp'];self.w(sp,0xdeadbeefdeadbeef,8)
  for j,v in enumerate(args[4:]):self.w(sp+0x28+j*8,v,8)
 def rg(self,n):b,w=A[n];return self.r[b]&((1<<w)-1)
 def sr(self,n,v):b,w=A[n];m=(1<<w)-1;self.r[b]=(v&m) if w>=32 else ((self.r[b]&~m)|(v&m))
 def addr(self,e,pc,sz):
  e=e[1:-1].replace(' ','');v=pc+sz if e.startswith('rip') else 0;e=e[3:] if e.startswith('rip') else e
  for sg,t in re.findall(r'(^|[+-])([^+-]+)',e):
   if '*' in t:q,k=t.split('*');x=self.rg(q)*int(k,0)
   else:x=self.rg(t) if t in A else int(t,0)
   v=v-x if sg=='-' else v+x
  return v&0xffffffffffffffff
 def rmem(self,a,w):
  bs=bytes(self.mem.get(a+i,0) if STK<=a+i<STK+0x1000 else self.l.read_bytes(a+i,1)[0] for i in range(w));return int.from_bytes(bs,'little')
 def w(self,a,v,w):
  bs=int(v&((1<<(w*8))-1)).to_bytes(w,'little')
  if STK<=a<STK+0x1000:
   for i,b in enumerate(bs):self.mem[a+i]=b
  else:self.l.write_bytes(a,bs)
 def op(self,x,pc,sz,fw=None):
  mm=re.match(r'(?:(byte|dword|qword) ptr )?(\[.*\])$',x)
  if mm:w={'byte':1,'dword':4,'qword':8}[mm.group(1)] if mm.group(1) else fw;a=self.addr(mm.group(2),pc,sz);return self.rmem(a,w),w,a
  if x in A:return self.rg(x),A[x][1]//8,None
  return int(x,0),fw,None
 def put(self,x,v,pc,sz,fw=None):
  _,w,a=self.op(x,pc,sz,fw);self.sr(x,v) if a is None else self.w(a,v,w)
 def fs(self,a,b,w):
  n=w*8;m=(1<<n)-1;r=(a-b)&m;self.zf=r==0;self.sf=(r>>(n-1))&1;self.of=(((a^b)&(a^r))>>(n-1))&1;return r
 def fa(self,a,b,w):
  n=w*8;m=(1<<n)-1;r=(a+b)&m;self.zf=r==0;self.sf=(r>>(n-1))&1;self.of=((~(a^b)&(a^r))>>(n-1))&1;return r
 def run(self):
  pc=ENTRY
  for step in range(20000):
   i=self.I[pc];m=i['mnemonic'];o=split(i['operands']);sz=len(bytes.fromhex(i['bytes']));nx=pc+sz
   if m in ('mov','movzx','movsxd'):
    v,w,_=self.op(o[1],pc,sz);v=v-(1<<(w*8)) if m=='movsxd' and v>>(w*8-1) else v;self.put(o[0],v,pc,sz);pc=nx
   elif m=='lea':self.sr(o[0],self.addr(o[1],pc,sz));pc=nx
   elif m in ('sub','cmp','add'):
    a,w,_=self.op(o[0],pc,sz);b,_,_=self.op(o[1],pc,sz,w);v=self.fa(a,b,w) if m=='add' else self.fs(a,b,w)
    if m!='cmp':self.put(o[0],v,pc,sz,w)
    pc=nx
   elif m in ('xor','test'):
    a,w,_=self.op(o[0],pc,sz);b,_,_=self.op(o[1],pc,sz,w);v=a^b if m=='xor' else a&b;self.zf=v==0;self.sf=(v>>(w*8-1))&1;self.of=0
    if m=='xor':self.put(o[0],v,pc,sz,w)
    pc=nx
   elif m=='cdq':self.sr('edx',0xffffffff if self.rg('eax')&0x80000000 else 0);pc=nx
   elif m in ('je','jne','jg','jge','jle','js','jmp'):
    c=m=='jmp' or (m=='je' and self.zf) or (m=='jne' and not self.zf) or (m=='jg' and not self.zf and self.sf==self.of) or (m=='jge' and self.sf==self.of) or (m=='jle' and (self.zf or self.sf!=self.of)) or (m=='js' and self.sf);pc=int(o[0],0) if c else nx
   elif m.startswith('cmov'):
    c=(m=='cmove' and self.zf) or (m=='cmovne' and not self.zf) or (m=='cmovg' and not self.zf and self.sf==self.of) or (m=='cmovle' and (self.zf or self.sf!=self.of)) or (m=='cmovl' and self.sf!=self.of)
    if c:v,w,_=self.op(o[1],pc,sz);self.put(o[0],v,pc,sz,w)
    pc=nx
   elif m in ('setne','setns'):
    self.put(o[0],int((not self.zf) if m=='setne' else (not self.sf)),pc,sz);pc=nx
   elif m=='push':self.r['rsp']-=8;self.w(self.r['rsp'],self.rg(o[0]),8);pc=nx
   elif m=='pop':v=self.rmem(self.r['rsp'],8);self.r['rsp']+=8;self.sr(o[0],v);pc=nx
   elif m=='imul':
    a,w,_=self.op(o[0],pc,sz);b,_,_=self.op(o[1],pc,sz,w);n=w*8;sa=a-(1<<n) if a>>(n-1) else a;sb=b-(1<<n) if b>>(n-1) else b;self.put(o[0],sa*sb,pc,sz,w);pc=nx
   elif m=='neg':a,w,_=self.op(o[0],pc,sz);v=self.fs(0,a,w);self.put(o[0],v,pc,sz,w);pc=nx
   elif m=='inc':a,w,_=self.op(o[0],pc,sz);self.put(o[0],self.fa(a,1,w),pc,sz,w);pc=nx
   elif m=='call':
    target=int(o[0],0)
    if target==0x180002430:rv=self.l.call_function(target,[self.r['rcx'],self.r['rdx']],max_instructions=10000)['rax']
    elif target==0x180009e30:
     ox=self.l.host_alloc(4,align=4);oy=self.l.host_alloc(4,align=4);px=self.rmem(self.r['rsp']+0x28,8);py=self.rmem(self.r['rsp']+0x30,8);thr=self.rmem(self.r['rsp']+0x38,8);self.l.write_bytes(ox,struct.pack('<I',self.rmem(px,4)));self.l.write_bytes(oy,struct.pack('<I',self.rmem(py,4)));rv=self.l.call_function(target,[self.r['rcx'],self.r['rdx'],self.r['r8'],self.r['r9'],self.rmem(self.r['rsp']+0x20,8),ox,oy,thr],max_instructions=500000)['rax'];self.w(px,struct.unpack('<I',self.l.read_bytes(ox,4))[0],4);self.w(py,struct.unpack('<I',self.l.read_bytes(oy,4))[0],4)
    else:raise AssertionError(hex(target))
    self.r['rax']=rv;pc=nx
   elif m=='ret':return step+1
   else:raise AssertionError((hex(pc),m,o))
  raise AssertionError('no ret')
def fixture(l,mask,d):
 w=h=7;raw=bytearray()
 for y in range(h):
  for x in range(w):i=(y%3)*3+(x%3);raw+=bytes((255,255 if mask>>i&1 else 0,0,0))
 pix=l.host_alloc(len(raw),align=16);l.write_bytes(pix,bytes(raw));world=l.host_alloc(0x40,align=16);l.write_bytes(world,b'\0'*0x40);l.write_bytes(world+4,struct.pack('<iii',w,h,w*4));l.write_bytes(world+0x10,struct.pack('<Q',pix));l.write_bytes(world+0x18,struct.pack('<Qiii',pix,w*4,w,h));state=l.host_alloc(0x80,align=16);l.write_bytes(state,b'\0'*0x80);l.write_bytes(state+8,struct.pack('<ii',6,6));l.write_bytes(state+0x10,struct.pack('<Q',world));l.write_bytes(state+0x24,struct.pack('<i',6));x=y=3;ps=[pix+((y+dy)*w+x+dx)*4 for dy in(-1,0,1) for dx in(-1,0,1)];n=l.host_alloc(72,align=16);l.write_bytes(n,struct.pack('<9Q',*ps));outs=[l.host_alloc(4,align=4) for _ in range(9)];return state,n,x,y,outs
def main():
 assert hashlib.sha256(AEX.read_bytes()).hexdigest()==SHA;D=json.loads(CFG.read_text());I={int(i['address'],0):i for b in D['blocks'] for i in b['instructions']};l=AexLoader(str(AEX),verbose=False,fast=True);mis=[]
 for mask in range(512):
  for d in DIRS:
   state,n,x,y,outs=fixture(l,mask,d);args=[state,n,x,y,d,*outs];[l.write_bytes(p,b'\xcc'*4) for p in outs];l.call_function(ENTRY,args,max_instructions=500000);actual=[l.read_bytes(p,4) for p in outs];[l.write_bytes(p,b'\xcc'*4) for p in outs];M(l,I,args).run();got=[l.read_bytes(p,4) for p in outs]
   if actual!=got:mis.append((mask,d,[x.hex() for x in actual],[x.hex() for x in got]))
 print(json.dumps({'status':'exact' if not mis else 'fail','calls':2048,'mismatch_count':len(mis),'first':mis[:3]},indent=2));assert not mis
if __name__=='__main__':main()
