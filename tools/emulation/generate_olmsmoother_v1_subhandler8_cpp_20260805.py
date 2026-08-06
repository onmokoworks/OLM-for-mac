#!/usr/bin/env python3
"""Generate the portable, direct-threaded C++ translation of SubHandler8."""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'refs/conformance/olmsmoother_v1_subhandler8_cfg_20260805.json'
OUT=ROOT/'mac/OLMSmoother/Mac/OLMSmoother_subhandler8.generated.inc'
EXPECTED_LINEAR=1135
EXPECTED_UNIQUE=1115
RET_STMT='return;'
COLOR_COMPARE_TARGET=0x180002430
COLOR_COMPARE_EXPR='ColorCompare8((const uint8_t*)R.rcx,(const uint8_t*)R.rdx)'
EDGE_WALKER_TARGET=0x180009e30
EDGE_WALKER_EXPR='EdgeWalker8((RenderState*)R.rcx,(int)R.rdx,(int)R.r8,(int)R.r9,(uint32_t)M.read64(R.rsp+0x20),(int*)M.ptr(M.read64(R.rsp+0x28)),(int*)M.ptr(M.read64(R.rsp+0x30)),(int)M.read64(R.rsp+0x38))'
alias={}
for b in ('rax','rbx','rcx','rdx','rsi','rdi','rbp','rsp'):
 n=b[1]; alias[b]=(b,64);alias['e'+n+'x' if b in ('rax','rbx','rcx','rdx') else 'e'+b[1:]]=(b,32)
alias.update({'ax':('rax',16),'al':('rax',8),'bx':('rbx',16),'bl':('rbx',8),'cx':('rcx',16),'cl':('rcx',8),'dx':('rdx',16),'dl':('rdx',8),'si':('rsi',16),'sil':('rsi',8),'di':('rdi',16),'dil':('rdi',8),'bp':('rbp',16),'bpl':('rbp',8),'sp':('rsp',16),'spl':('rsp',8)})
for n in range(8,16):
 b=f'r{n}';alias[b]=(b,64);alias[b+'d']=(b,32);alias[b+'w']=(b,16);alias[b+'b']=(b,8)
def ops(s):
 d=0
 for i,c in enumerate(s):
  d+=c=='[';d-=c==']'
  if c==',' and d==0:return s[:i].strip(),s[i+1:].strip()
 return (s.strip(),)
def addr(x,pc,size):
 e=x[x.index('[')+1:x.rindex(']')].replace(' ',''); terms=[]
 if e.startswith('rip'):terms.append(hex(pc+size));e=e[3:]
 for sign,t in re.findall(r'(^|[+-])([^+-]+)',e):
  if '*' in t:
   a,m=t.split('*');v=f'(R.{a}*{int(m,0)}ull)'
  elif t in alias:v=f'R.{alias[t][0]}'
  else:v=hex(int(t,0))+'ull'
  terms.append(('-' if sign=='-' else '+')+v)
 return '('+''.join(terms).lstrip('+')+')'
def read(x,pc,size,force=None):
 mm=re.match(r'(?:(byte|word|dword|qword) ptr )?(\[.*\])$',x)
 if mm:
  w={'byte':8,'word':16,'dword':32,'qword':64}[mm.group(1)] if mm.group(1) else force
  return f'M.read{w}({addr(mm.group(2),pc,size)})',w
 if x in alias:
  b,w=alias[x];return (f'uint{w}_t(R.{b})' if w<64 else f'R.{b}'),w
 return x+'ull',force
def write(dst,val,pc,size,force=None):
 mm=re.match(r'(?:(byte|word|dword|qword) ptr )?(\[.*\])$',dst)
 if mm:
  w={'byte':8,'word':16,'dword':32,'qword':64}[mm.group(1)] if mm.group(1) else force
  return f'M.write{w}({addr(mm.group(2),pc,size)}, {val});'
 b,w=alias[dst]
 if w==64:return f'R.{b}=uint64_t({val});'
 if w==32:return f'R.{b}=uint32_t({val});'
 mask=(1<<w)-1
 return f'R.{b}=(R.{b}&~0x{mask:x}ull)|(uint{w}_t({val}));'
def main():
 d=json.loads(SRC.read_text());I={int(i['address'],0):i for b in d['blocks'] for i in b['instructions']}
 assert d['instruction_count']==EXPECTED_LINEAR and len(I)==EXPECTED_UNIQUE
 z=[]
 for pc in sorted(I):
  i=I[pc];m=i['mnemonic'];o=ops(i['operands']);sz=len(bytes.fromhex(i['bytes']));nxt=pc+sz;z.append(f'L_{pc:x}:')
  if m in ('mov','movzx','movsxd'):
   v,w=read(o[1],pc,sz);v=f'int64_t(int32_t({v}))' if m=='movsxd' else v;z.append('  '+write(o[0],v,pc,sz)+' goto L_%x;'%nxt)
  elif m=='lea':z.append('  '+write(o[0],addr(o[1],pc,sz),pc,sz)+' goto L_%x;'%nxt)
  elif m in ('sub','cmp'):
   a,w=read(o[0],pc,sz);b,_=read(o[1],pc,sz,w);z.append(f'  T=M.subflags({a},{b},{w});')
   if m=='sub':z.append('  '+write(o[0],'T',pc,sz,w))
   z.append('  goto L_%x;'%nxt)
  elif m in ('xor','test'):
   a,w=read(o[0],pc,sz);b,_=read(o[1],pc,sz,w);z.append(f'  T=({a}) {"^" if m=="xor" else "&"} ({b}); M.logicflags(T,{w});')
   if m=='xor':z.append('  '+write(o[0],'T',pc,sz,w))
   z.append('  goto L_%x;'%nxt)
  elif m=='cdq':z.append('  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_%x;'%nxt)
  elif m in ('je','jne','jg','jge','jle','js'):
   cond={'je':'M.zf','jne':'!M.zf','jg':'!M.zf&&(M.sf==M.of)','jge':'M.sf==M.of','jle':'M.zf||(M.sf!=M.of)','js':'M.sf'}[m]
   z.append(f'  if ({cond}) goto L_{int(o[0],0):x}; goto L_{nxt:x};')
  elif m=='jmp':z.append(f'  goto L_{int(o[0],0):x};')
  elif m=='call':
   target=int(o[0],0)
   if target==COLOR_COMPARE_TARGET:z.append(f'  R.rax=uint32_t({COLOR_COMPARE_EXPR}); goto L_{nxt:x};')
   elif target==EDGE_WALKER_TARGET:z.append(f'  R.rax=(uintptr_t){EDGE_WALKER_EXPR}; goto L_{nxt:x};')
   else:raise AssertionError(hex(target))
  elif m=='add':
   a,w=read(o[0],pc,sz);b,_=read(o[1],pc,sz,w);z.append(f'  T=M.addflags({a},{b},{w}); '+write(o[0],'T',pc,sz,w)+' goto L_%x;'%nxt)
  elif m=='push':z.append('  R.rsp-=8; M.write64(R.rsp,'+read(o[0],pc,sz)[0]+'); goto L_%x;'%nxt)
  elif m=='imul':
   a,w=read(o[0],pc,sz);b,_=read(o[1],pc,sz,w);z.append('  '+write(o[0],f'int64_t(int32_t({a}))*int64_t(int32_t({b}))',pc,sz,w)+' goto L_%x;'%nxt)
  elif m.startswith('cmov'):
   cond={'cmove':'M.zf','cmovne':'!M.zf','cmovg':'!M.zf&&(M.sf==M.of)','cmovle':'M.zf||(M.sf!=M.of)','cmovl':'M.sf!=M.of'}[m];v,w=read(o[1],pc,sz);z.append(f'  if({cond}){{'+write(o[0],v,pc,sz,w)+'} goto L_%x;'%nxt)
  elif m in ('setne','setns'):
   cond='!M.zf' if m=='setne' else '!M.sf';z.append('  '+write(o[0],f'uint8_t({cond})',pc,sz,8)+' goto L_%x;'%nxt)
  elif m=='neg':
   a,w=read(o[0],pc,sz);z.append(f'  T=M.subflags(0,{a},{w}); '+write(o[0],'T',pc,sz,w)+' goto L_%x;'%nxt)
  elif m=='inc':
   a,w=read(o[0],pc,sz);z.append(f'  T=M.addflags({a},1,{w}); '+write(o[0],'T',pc,sz,w)+' goto L_%x;'%nxt)
  elif m=='shl':
   a,w=read(o[0],pc,sz);b,_=read(o[1],pc,sz,w);z.append('  '+write(o[0],f'({a})<<(({b})&0x3f)',pc,sz,w)+' goto L_%x;'%nxt)
  elif m=='nop':z.append('  goto L_%x;'%nxt)
  elif m=='pop':z.append('  '+write(o[0],'M.read64(R.rsp)',pc,sz,64)+' R.rsp+=8; goto L_%x;'%nxt)
  elif m=='ret':z.append('  '+RET_STMT)
  else:raise AssertionError(m)
 OUT.write_text('// Generated from '+SRC.name+'; do not hand edit.\n'+'\n'.join(z)+'\n')
 print(OUT, len(I))
if __name__=='__main__':main()
