#!/usr/bin/env python3
import hashlib,json,struct,sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_R8,UC_X86_REG_R9,UC_X86_REG_R10,UC_X86_REG_R11,UC_X86_REG_R12,UC_X86_REG_R13,UC_X86_REG_R15,UC_X86_REG_RBX,UC_X86_REG_RSI
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/emulation'));from aex_loader import AexLoader
AEX=ROOT/'plugins_2025/OLMSmoother.aex';SHA='6206f601b645dc915b78269ae403e5cbee642ac2812e320d85838ec72135fe82';FAMILIES=ROOT/'refs/conformance/olmsmoother_v1_classifier8_binary_families_20260805.json';OUT=ROOT/'refs/conformance/olmsmoother_v1_classifier8_family_registers_20260805.json';ENTRY=0x180008060;POINTS=(0x1800087f0,0x1800088d4,0x1800088f9,0x180008aac,0x180008c4f,0x180008dcc,0x180008eb4,0x1800091d2,0x18000924d,0x180009293,0x1800092f4,0x180009455);REGS={'rbx':UC_X86_REG_RBX,'r8':UC_X86_REG_R8,'r9':UC_X86_REG_R9,'r10':UC_X86_REG_R10,'r11':UC_X86_REG_R11,'r12':UC_X86_REG_R12,'r13':UC_X86_REG_R13,'r15':UC_X86_REG_R15,'rsi':UC_X86_REG_RSI}
def main():
 assert hashlib.sha256(AEX.read_bytes()).hexdigest()==SHA;families=json.loads(FAMILIES.read_text())['families'];l=AexLoader(str(AEX),verbose=False,fast=True);s=l.host_alloc(64,align=16);l.write_bytes(s,b'\0'*64);l.write_bytes(s+8,struct.pack('<i',6));ps=[l.host_alloc(4,align=4) for _ in range(9)];n=l.host_alloc(72,align=16);l.write_bytes(n,struct.pack('<9Q',*ps));current=[]
 def hook(uc,address,size,user):
  vals={k:uc.reg_read(v) for k,v in REGS.items()};current.append({'address':hex(address),'pointer_indices':{k:(ps.index(v) if v in ps else None) for k,v in vals.items()},'raw':{k:hex(v) for k,v in vals.items()}})
 for p in POINTS:l.uc.hook_add(UC_HOOK_CODE,hook,begin=p,end=p)
 reports=[]
 for f in families:
  rep=f['members'][0];mask=rep['mask'];direction=rep['direction']
  for i,p in enumerate(ps):l.write_bytes(p,bytes((255,255 if mask>>i&1 else 0,0,0)))
  current.clear();result=l.call_function(ENTRY,[s,0,0,n,direction],max_instructions=100000)['rax'];reports.append({'signature':f['signature'],'family_count':f['count'],'representative':rep,'actual_result':result,'checkpoints':list(current)})
 report={'schema_version':1,'status':'captured','actual_aex_sha256':SHA,'families':reports};OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report,indent=2,sort_keys=True))
if __name__=='__main__':main()
