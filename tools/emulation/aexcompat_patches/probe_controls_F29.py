#!/usr/bin/env python3
"""SSE default-init and x87 negative controls on the selected Unicorn library."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--library',type=Path,required=True)
    ap.add_argument('--scratch',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args(); args.scratch.mkdir(parents=True,exist_ok=True)
    os.environ['LIBUNICORN_PATH']=str(args.library.resolve());os.environ['TMPDIR']=str(args.scratch.resolve())
    import unicorn
    from unicorn.x86_const import UC_X86_REG_XMM0,UC_X86_REG_XMM1,UC_X86_REG_RDI,UC_X86_REG_RSI,UC_X86_REG_RDX
    from unicorn.unicorn_py3.unicorn import uclib
    assert Path(uclib._name).resolve().parent==args.library.resolve()
    u=unicorn.Uc(unicorn.UC_ARCH_X86,unicorn.UC_MODE_64);u.mem_map(0x1000,0x10000)
    u.mem_write(0x1000,bytes.fromhex('f30f58c1'))
    u.reg_write(UC_X86_REG_XMM0,0x7fc12345);u.reg_write(UC_X86_REG_XMM1,0xffc12346)
    u.emu_start(0x1000,0x1004,count=1)
    default_result=u.reg_read(UC_X86_REG_XMM0)
    # 80-bit memory loads preserve signaling payloads (no f32/f64 conversion).
    vals=[bytes.fromhex(s) for s in ['bc9a7856341200c0ff7f','bd9a7856341200c0ffff','be9a785634120080ff7f','bf9a785634120080ffff','0000000000000080ff3f','00000000000000000000']]
    codes=[bytes.fromhex('db2fdb2edec1db3a'),bytes.fromhex('db2fdb2edee9db3a'),bytes.fromhex('db2fdb2edec9db3a'),bytes.fromhex('db2fdb2edef9db3a')]
    c='#include <stdio.h>\nint main(){unsigned op; unsigned char a[10],b[10],r[10];while(fread(&op,4,1,stdin)==1&&fread(a,10,1,stdin)==1&&fread(b,10,1,stdin)==1){switch(op){\n'
    for i,code in enumerate(codes):
        c+=f'case {i}:asm volatile("fninit; .byte '+','.join('0x%02x'%x for x in code)+'" ::"D"(a),"S"(b),"d"(r):"st","memory");break;\n'
    c+='}fwrite(r,10,1,stdout);}}\n'
    src=args.scratch/'x87.c';src.write_text(c)
    subprocess.run(['clang','-arch','x86_64','-O2',str(src),'-o',str(args.scratch/'x87')],check=True)
    rows=[]
    with (args.scratch/'x87-input.bin').open('wb') as out:
        for i,code in enumerate(codes):
            u.mem_write(0x1100+i*16,code)
            for a in vals:
                for b in vals:
                    out.write(i.to_bytes(4,'little')+a+b);rows.append((i,a,b))
    with (args.scratch/'x87-input.bin').open('rb') as inp,(args.scratch/'x87-native.bin').open('wb') as out:
        subprocess.run(['/usr/bin/arch','-x86_64',str(args.scratch/'x87')],stdin=inp,stdout=out,check=True)
    observed=[]
    with (args.scratch/'x87-native.bin').open('rb') as native:
        for i,a,b in rows:
            u.mem_write(0x2000,a);u.mem_write(0x2010,b);u.mem_write(0x2020,b'\0'*10)
            u.reg_write(UC_X86_REG_RDI,0x2000);u.reg_write(UC_X86_REG_RSI,0x2010);u.reg_write(UC_X86_REG_RDX,0x2020)
            # FNINIT before every operation, using a distinct cached block.
            u.mem_write(0x1200,bytes.fromhex('dbe3'));u.emu_start(0x1200,0x1202,count=1)
            addr=0x1100+i*16;u.emu_start(addr,addr+len(codes[i]),count=4)
            result=bytes(u.mem_read(0x2020,10));ref=native.read(10)
            observed.append(dict(op=i,a=a.hex(),b=b.hex(),rosetta=ref.hex(),unicorn=result.hex(),equal=result==ref))
    report=dict(default_sse_addss=f'{default_result:08x}',x87_rows=len(observed),x87_rosetta_differences=sum(not r['equal'] for r in observed),rows=observed,library_sha256=hashlib.sha256(Path(uclib._name).read_bytes()).hexdigest())
    args.output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='rows'}))

if __name__=='__main__':main()
