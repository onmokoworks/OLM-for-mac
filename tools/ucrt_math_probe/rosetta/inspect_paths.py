#!/usr/bin/env python3
"""Reproduce disassembly evidence without committing Microsoft binary data."""
import pathlib,struct,sys
import capstone,pefile
p=pefile.PE(str(pathlib.Path.home()/'.cache/olm-emu/ucrt/10.0.28000.2705/ucrtbase.dll'))
c=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);c.detail=True
for name,start,end in [('sinf-sse',0xbbc60,0xbbfd0),('sinf-fma',0xbbfd0,0xbc340),('cosf-sse',0xb7900,0xb7bb0),('cosf-fma',0xb7bb0,0xb7e00),('powf',0xb9b90,0xba940),('errno',0x46070,0x461a6),('state-index',0x48bfc,0x48c67),('matherr',0x3b1a4,0x3b1d5)]:
 print('\nPATH',name)
 for i in c.disasm(p.get_data(start,end-start),start):
  note=[]
  for o in i.operands:
   if o.type==capstone.x86.X86_OP_MEM and o.mem.base==capstone.x86.X86_REG_RIP:
    r=i.address+i.size+o.mem.disp;b=p.get_data(r,8)
    note.append(f'RVA={r:x} bytes={b.hex()} double={struct.unpack("<d",b)[0].hex()}')
  print(f'{i.address:x}: {i.mnemonic} {i.op_str}'+(' ; '+'; '.join(note) if note else ''))
