#!/usr/bin/env python3
"""Compare original AEX SSE instructions in Unicorn with macOS x86_64 execution.

This diagnoses an oracle boundary, not a portable renderer implementation or
a Windows AE reference. On the Apple Silicon workstation x86_64 uses Rosetta.
"""
import argparse
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
sys.dont_write_bytecode=True
from aex_loader import AexLoader
from unicorn.x86_const import UC_X86_REG_XMM1, UC_X86_REG_XMM3, UC_X86_REG_XMM5, UC_X86_REG_XMM6, UC_X86_REG_XMM7
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from hashlib import sha256

ROOT=Path(__file__).resolve().parents[2]
CPP='''#include <cstdio>
int main(){
 unsigned in[3];
 while(std::fread(in,4,3,stdin)==3){
  float a,b,r; __builtin_memcpy(&a,in+1,4); __builtin_memcpy(&b,in+2,4);
  switch(in[0]){case 0:asm("addss %1,%0":"+x"(a):"x"(b));break;
   case 1:asm("subss %1,%0":"+x"(a):"x"(b));break;
   case 2:asm("mulss %1,%0":"+x"(a):"x"(b));break;
   case 3:asm("divss %1,%0":"+x"(a):"x"(b));break;
   default:asm("minss %1,%0":"+x"(a):"x"(b));}
  __builtin_memcpy(&r,&a,4);
  std::fwrite(&r,4,1,stdout);
 }
}
'''

def main():
    p=argparse.ArgumentParser();p.add_argument('--report',type=Path,required=True);args=p.parse_args()
    scratch=ROOT/'orchestra/state/C02-dblur-smart';scratch.mkdir(parents=True,exist_ok=True)
    os.environ.update(TMPDIR=str(scratch),TMP=str(scratch),TEMP=str(scratch),
        ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1')
    aex=ROOT.parent.parent/'plugins_2025/OLMDirectionalBlur.aex'
    loader=AexLoader(str(aex),verbose=False,fast=False)
    values=[0,0x80000000,0x3f800000,0xbf800000,1,0x7f7fffff,0x7f800000,0xff800000,
            0x7fc12345,0xffc12346,0x7f812345,0xff812346]
    specs=[('add',0x1800020f0,UC_X86_REG_XMM3,UC_X86_REG_XMM6),
           ('sub',0x180002055,UC_X86_REG_XMM5,UC_X86_REG_XMM3),
           ('mul',0x180002113,UC_X86_REG_XMM7,UC_X86_REG_XMM6),
           ('div',0x180002103,UC_X86_REG_XMM6,UC_X86_REG_XMM3),
           ('min',0x180006c21,UC_X86_REG_XMM3,UC_X86_REG_XMM1)]
    rows=[];payload=bytearray();instructions=[]
    for op,(name,address,left,right) in enumerate(specs):
        instruction=next(Cs(CS_ARCH_X86,CS_MODE_64).disasm(loader.read_bytes(address,8),address))
        instructions.append({'address':hex(address),'bytes':bytes(instruction.bytes).hex(),
            'mnemonic':instruction.mnemonic,'operands':instruction.op_str})
        for a in values:
            for b in values:
                loader.uc.reg_write(left,a);loader.uc.reg_write(right,b)
                loader.uc.emu_start(address,address+instruction.size,count=1)
                word=loader.uc.reg_read(left)&0xffffffff
                payload+=struct.pack('<III',op,a,b)
                rows.append({'operation':name,'left':f'{a:08x}','right':f'{b:08x}','aex':f'{word:08x}'})
    commands=[]
    with tempfile.TemporaryDirectory(prefix='sse_',dir=scratch) as tmp:
        tmp=Path(tmp);source=tmp/'probe.cpp';source.write_text(CPP)
        binary=tmp/'x86'
        cmd=['clang++','-arch','x86_64','-std=c++17','-O2','-fno-fast-math','-ffp-contract=off',str(source),'-o',str(binary)]
        commands.append(cmd);subprocess.run(cmd,check=True,capture_output=True)
        command=['/usr/bin/arch','-x86_64',str(binary)];commands.append(command)
        raw=subprocess.run(command,input=bytes(payload),check=True,capture_output=True).stdout
        assert len(raw)==len(rows)*4
        for row,(word,) in zip(rows,struct.iter_unpack('<I',raw)):
            row['macos_x86_64']=f'{word:08x}'
            row['exact']=row['aex']==row['macos_x86_64']
    args.report.write_text(json.dumps({'cases':rows,'instructions':instructions,'commands':commands,
        'aex_sha256':sha256(aex.read_bytes()).hexdigest(),
        'source_sha256':sha256(CPP.encode()).hexdigest(),
        'scope':'Original AEX instructions in Python Unicorn vs macOS x86_64 execution on Apple Silicon (Rosetta); no native Windows claim',
        'probe_sha256':sha256(Path(__file__).read_bytes()).hexdigest()},indent=2,sort_keys=True)+'\n')
    print('COMPLETE',len(rows),'EXACT',sum(r['exact'] for r in rows),'DIFFERENT',sum(not r['exact'] for r in rows))

if __name__=='__main__':main()
