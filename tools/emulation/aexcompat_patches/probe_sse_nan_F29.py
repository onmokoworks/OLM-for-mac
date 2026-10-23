#!/usr/bin/env python3
"""Bit-pattern SSE probe. Run using MAIN/tools/emulation/.venv/bin/python.
All compiler temporary files are confined to --scratch. Output is JSONL.
--library selects an existing worker's libunicorn through the Python binding.
"""
import argparse
import collections
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess


def specs():
    out = []
    for suffix, prefix, bits in [('ss','f3',32),('ps','',32),('sd','f2',64),('pd','66',64)]:
        for name, opcode in [('add','58'),('sub','5c'),('mul','59'),('div','5e'),('min','5d'),('max','5f'),('sqrt','51')]:
            out.append((name+suffix, bytes.fromhex(prefix+'0f'+opcode+'c1'),bits))
    out += [('cvtss2sd',bytes.fromhex('f30f5ac1'),32),('cvtsd2ss',bytes.fromhex('f20f5ac1'),64),
            ('cvtps2pd',bytes.fromhex('0f5ac1'),32),('cvtpd2ps',bytes.fromhex('660f5ac1'),64)]
    return out


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--scratch',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--library',type=Path)
    args=ap.parse_args()
    scratch=args.scratch.resolve(); scratch.mkdir(parents=True,exist_ok=True)
    os.environ['TMPDIR']=str(scratch)
    if args.library: os.environ['LIBUNICORN_PATH']=str(args.library.resolve())
    import unicorn
    from unicorn.x86_const import UC_X86_REG_XMM0, UC_X86_REG_XMM1, UC_X86_REG_MXCSR
    from unicorn.unicorn_py3.unicorn import uclib
    loaded=Path(uclib._name).resolve()
    if args.library: assert loaded.parent==args.library.resolve(), loaded
    vals={32:[0,0x80000000,0x3f800000,0xbf800000,0x7f800000,0xff800000,0x7fc12345,0xffc12346,0x7f812347,0xff812348],
          64:[0,0x8000000000000000,0x3ff0000000000000,0xbff0000000000000,0x7ff0000000000000,0xfff0000000000000,0x7ff8123456789abc,0xfff8123456789abd,0x7ff0123456789abe,0xfff0123456789abf]}
    operations=specs()
    source='#include <stdio.h>\n#include <stdint.h>\n#include <cpuid.h>\nint main(){ unsigned op; unsigned char a[16],b[16],r[16]; unsigned mx=0x1f80;\nwhile(fread(&op,4,1,stdin)==1 && fread(a,16,1,stdin)==1 && fread(b,16,1,stdin)==1){ switch(op){\n'
    for i,(_,code,_) in enumerate(operations):
        literal=','.join('0x%02x'%b for b in code)
        source+=f'case {i}: asm volatile("ldmxcsr (%3); movdqu (%0),%%xmm0; movdqu (%1),%%xmm1; .byte {literal}; movdqu %%xmm0,(%2)" :: "r"(a),"r"(b),"r"(r),"r"(&mx):"xmm0","xmm1","memory"); break;\n'
    source+='} fwrite(r,16,1,stdout); } unsigned a0,b0,c0,d0; __cpuid(1,a0,b0,c0,d0); fprintf(stderr,"CPUID.1:ECX=%08x FMA=%u AVX=%u\\n",c0,(c0>>12)&1,(c0>>28)&1); }\n'
    (scratch/'probe.c').write_text(source)
    subprocess.run(['clang','-arch','x86_64','-O2',str(scratch/'probe.c'),'-o',str(scratch/'probe')],check=True)
    rows=[]
    with (scratch/'inputs.bin').open('wb') as f:
        for i,(name,code,bits) in enumerate(operations):
            for a in vals[bits]:
                for b in vals[bits]:
                    # Rotate lanes so every packed instruction sees distinct simultaneous inputs.
                    av=[vals[bits][(vals[bits].index(a)+lane)%10] for lane in range(128//bits)]
                    bv=[vals[bits][(vals[bits].index(b)+lane*3)%10] for lane in range(128//bits)]
                    ab=b''.join(x.to_bytes(bits//8,'little') for x in av)
                    bb=b''.join(x.to_bytes(bits//8,'little') for x in bv)
                    f.write(struct.pack('<I',i)+ab+bb)
                    rows.append((name,code,bits,ab,bb))
    with (scratch/'inputs.bin').open('rb') as inp,(scratch/'native.bin').open('wb') as out,(scratch/'native.log').open('w') as err:
        subprocess.run(['/usr/bin/arch','-x86_64',str(scratch/'probe')],stdin=inp,stdout=out,stderr=err,check=True)
    uc=unicorn.Uc(unicorn.UC_ARCH_X86,unicorn.UC_MODE_64)
    uc.mem_map(0x1000,0x10000)
    addresses={}
    for i,(name,code,bits) in enumerate(operations):
        addresses[name]=0x1000+i*16; uc.mem_write(addresses[name],code)
    counts=collections.Counter()
    with (scratch/'native.bin').open('rb') as native,args.output.open('w') as out:
        for name,code,bits,ab,bb in rows:
            uc.reg_write(UC_X86_REG_XMM0,int.from_bytes(ab,'little'))
            uc.reg_write(UC_X86_REG_XMM1,int.from_bytes(bb,'little'))
            uc.reg_write(UC_X86_REG_MXCSR,0x1f80)
            uc.emu_start(addresses[name],addresses[name]+len(code),count=1)
            result=uc.reg_read(UC_X86_REG_XMM0).to_bytes(16,'little')
            ref=native.read(16); assert len(ref)==16
            row=dict(op=name,code=code.hex(),bits=bits,a=ab.hex(),b=bb.hex(),rosetta=ref.hex(),unicorn=result.hex(),equal=ref==result)
            out.write(json.dumps(row,sort_keys=True)+'\n')
            if result!=ref: counts[name]+=1
        assert not native.read(1)
    print(json.dumps(dict(rows=len(rows),differences=sum(counts.values()),by_op=counts,python_binding=unicorn.__version__,uc_version=unicorn.uc_version(),library=str(loaded),library_sha256=hashlib.sha256(loaded.read_bytes()).hexdigest(),native_features=(scratch/'native.log').read_text().strip(),sha256=hashlib.sha256(args.output.read_bytes()).hexdigest()),sort_keys=True))

if __name__=='__main__': main()
