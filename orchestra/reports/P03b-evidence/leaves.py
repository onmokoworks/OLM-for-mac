"""Execute unchanged original mask and clamp instructions, without detours."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R/'tools/emulation'))
from aex_loader import AexLoader
from unicorn.x86_const import UC_X86_REG_RCX,UC_X86_REG_RAX,UC_X86_REG_XMM0,UC_X86_REG_XMM6
M=Path('/Users/onmk/Documents/Projects/Personal/OLM as/plugins_2025')
words=[0,0x80000000,1,0x3f000000,0x3f800000,0xbf800000,0x7f7fffff,0xff7fffff,0x7f800000,0xff800000,0x7fc12345,0xffc54321,0x7f812345]
result={}
ld=AexLoader(str(M/'OLMRadialBlur.aex'),verbose=False,fast=True)
ptr=ld.bump_alloc(16);rows=[]
for word in words:
 ld.write_bytes(ptr,word.to_bytes(4,'little'));ld.uc.reg_write(UC_X86_REG_RCX,ptr);ld.uc.reg_write(UC_X86_REG_XMM6,0)
 ld.uc.emu_start(0x1800081d0,0x1800081d6,count=2)
 actual=ld.uc.reg_read(UC_X86_REG_RAX)&255
 import struct
 value=struct.unpack('<f',word.to_bytes(4,'little'))[0]
 expected=int(not(value<=0))
 assert actual==expected
 rows.append(dict(input=f'{word:08x}',mask=actual))
result['radial_COMISS_SETB']=rows
ld=AexLoader(str(M/'OLMKiraKira.aex'),verbose=False,fast=True);rows=[]
for word in words:
 ld.uc.reg_write(UC_X86_REG_XMM0,word)
 ld.call_function(0x181156740,max_instructions=100)
 actual=ld.uc.reg_read(UC_X86_REG_XMM0)&0xffffffff
 value=struct.unpack('<f',word.to_bytes(4,'little'))[0]
 expected=0 if word&0x7fffffff>0x7f800000 or value<=0 else 0x3f800000 if value>=1 else word
 assert actual==expected
 rows.append(dict(input=f'{word:08x}',clamped=f'{actual:08x}'))
result['kira_clamp']=rows
print(json.dumps(result,indent=2))
