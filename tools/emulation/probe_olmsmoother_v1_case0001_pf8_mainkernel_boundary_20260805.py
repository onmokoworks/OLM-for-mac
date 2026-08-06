#!/usr/bin/env python3
import hashlib, json, struct, sys
from pathlib import Path
from PIL import Image
from unicorn.x86_const import UC_X86_REG_RCX,UC_X86_REG_RDX,UC_X86_REG_R8,UC_X86_REG_R9,UC_X86_REG_RIP,UC_X86_REG_RSP
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/emulation'))
from aex_loader import AexLoader
AEX=ROOT/'plugins_2025/OLMSmoother.aex';SHA='6206f601b645dc915b78269ae403e5cbee642ac2812e320d85838ec72135fe82'
SOURCE=ROOT/'refs/win_references/20260604_olm/OLMSmoother/case_0001_before_effects.png'
OUT=ROOT/'refs/conformance/olmsmoother_v1_case0001_pf8_mainkernel_boundary_20260805.json'
MAIN=0x180005570;EXEC=0x180006270
ARGS=[0,0,464,170,5,2,0,0,494,170,460,170,464,170]
def i32(v):return struct.unpack('<i',struct.pack('<I',v&0xffffffff))[0]
def u64(l,a):return struct.unpack('<Q',l.read_bytes(a,8))[0]
def main():
 assert hashlib.sha256(AEX.read_bytes()).hexdigest()==SHA
 im=Image.open(SOURCE).convert('RGBA');l=AexLoader(str(AEX),verbose=False,fast=True)
 state=l.host_alloc(0x80,align=16);l.write_bytes(state,b'\0'*0x80);l.write_bytes(state+8,struct.pack('<i',6))
 ps=[];words=[]
 for dy in(-1,0,1):
  for dx in(-1,0,1):
   r,g,b,a=im.getpixel((464+dx,170+dy));w=[a,r,g,b];words.append(w);p=l.host_alloc(4,align=4);l.write_bytes(p,bytes(w));ps.append(p)
 neigh=l.host_alloc(72,align=16);l.write_bytes(neigh,struct.pack('<9Q',*ps));captures=[]
 def hook(ld,address,size):
  rsp=ld.uc.reg_read(UC_X86_REG_RSP)
  evaluator=u64(ld,rsp+0x48);vtable=u64(ld,evaluator)
  captures.append({'direction':i32(ld.uc.reg_read(UC_X86_REG_RDX)),'start':[i32(ld.uc.reg_read(UC_X86_REG_R8)),i32(ld.uc.reg_read(UC_X86_REG_R9))],'color_a_index':ps.index(u64(ld,rsp+0x28)) if u64(ld,rsp+0x28) in ps else None,'end':[i32(u64(ld,rsp+0x30)),i32(u64(ld,rsp+0x38))],'color_b_index':ps.index(u64(ld,rsp+0x40)) if u64(ld,rsp+0x40) in ps else None,'evaluator_bytes':ld.read_bytes(evaluator,0x20).hex(),'evaluator_vtable':hex(vtable),'evaluator_function':hex(u64(ld,vtable)),'use_source':u64(ld,rsp+0x50)&0xff,'leading_span':i32(u64(ld,rsp+0x58))})
  ld.uc.reg_write(UC_X86_REG_RIP,u64(ld,rsp));ld.uc.reg_write(UC_X86_REG_RSP,rsp+8)
 l.add_code_hook(EXEC,hook);args=list(ARGS);args[0]=state;args[1]=neigh
 result=l.call_function(MAIN,args,max_instructions=250000)
 report={'schema_version':1,'status':'captured','actual_aex_sha256':SHA,'input_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'center':[464,170],'neighborhood_argb':words,'main_args':ARGS[2:],'executor_captures':captures,'instructions':result['instructions']}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report,indent=2,sort_keys=True))
if __name__=='__main__':main()
