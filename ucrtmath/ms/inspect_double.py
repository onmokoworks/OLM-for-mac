#!/usr/bin/env python3
"""Read-only reproduction of F43b algorithm/constant evidence.

Use MAIN's pefile/Capstone environment. Redirect output to ticket scratch;
never retain Microsoft instruction listings in the repository.
"""
import argparse
import hashlib
import pathlib
import struct
import capstone
import pefile
p=argparse.ArgumentParser()
p.add_argument('region',choices=['sin','cos','exp','reduce','constants'])
a=p.parse_args()
path=pathlib.Path.home()/'.cache/olm-emu/ucrt/10.0.28000.2705/ucrtbase.dll'
assert hashlib.sha256(path.read_bytes()).hexdigest()=='385a6d73a50063a4c760bdb2ee59e575de7ff350a2e3b214ea491d08358484f3'
pe=pefile.PE(str(path))
if a.region=='constants':
    for base,count,stride in [(0x10f930,12,16),(0x110c00,192,8),(0x110450,6,8),(0x110610,5,16),(0x110720,5,16)]:
        for i in range(count):
            r=base+i*stride
            print(f'{r:06x}',struct.unpack('<d',pe.get_data(r,8))[0].hex())
else:
    start,end={'sin':(0xbb6e0,0xbbc4a),'cos':(0xb7370,0xb78ea),'exp':(0xb7de0,0xb81f5),'reduce':(0xbb160,0xbb5f7)}[a.region]
    dis=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64)
    dis.detail=True
    for ins in dis.disasm(pe.get_data(start,end-start),start):
        notes=[]
        for op in ins.operands:
            if op.type==capstone.x86.X86_OP_MEM and op.mem.base==capstone.x86.X86_REG_RIP:
                r=ins.address+ins.size+op.mem.disp
                notes.append(f'RVA {r:x}: {struct.unpack("<d",pe.get_data(r,8))[0].hex()}')
        print(f'{ins.address:x}: {ins.mnemonic} {ins.op_str}', '; '.join(notes))
