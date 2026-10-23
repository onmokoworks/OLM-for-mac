#!/usr/bin/env python3
"""Compare scalar helpers to individual original-AEX SSE instructions, bitwise."""

from pathlib import Path as _HarnessPath
_UCRT_CXX = str(_HarnessPath(__file__).resolve().parents[2] / "tools/ucrt_cxx.py")
import json, os, struct, subprocess, sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
MAIN=ROOT.parent.parent if ROOT.parent.name=='worktrees' else ROOT
SCRATCH=ROOT/'orchestra/state/C01-smoother2-smart/sse'
from aex_loader import AexLoader
from unicorn.x86_const import UC_X86_REG_XMM0, UC_X86_REG_XMM5, UC_X86_REG_XMM8, UC_X86_REG_R10

def main():
    SCRATCH.mkdir(parents=True,exist_ok=True)
    os.environ.update(TMPDIR=str(SCRATCH),TMP=str(SCRATCH),TEMP=str(SCRATCH))
    source=ROOT/'mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp'
    host=SCRATCH/'host.cpp'
    host.write_text('#include "'+str(source)+'"\n'+'''int main() {
 unsigned d,s; while(scanf("%x %x",&d,&s)==2) {
 float a=sm2_float_word(d), b=sm2_float_word(s);
 printf("%08x %08x %08x\\n",sm2_float_bits(sm2_sse_mul(a,b)),sm2_float_bits(sm2_sse_add(a,b)),sm2_float_bits(sm2_sse_div(a,b)));
 } }
''')
    binary=SCRATCH/'test'
    subprocess.run([_UCRT_CXX,'-std=c++17','-O2','-fno-fast-math','-ffp-contract=off','-Wno-deprecated-declarations',
        '-I',str(ROOT/'cli/OLMSmoother2/shim'),str(host),'-o',str(binary)],check=True)
    values=[0,0x80000000,0x3f800000,0xbf800000,0x3f000000,0xbf000000,0x7f800000,0xff800000,
        0x7fc00000,0xffc00000,0x7fc12345,0xffc54321,0x7f812345,0xff812346,0x7f7fffff,0xff7fffff,1,0x80000001,0x00800000,0x80800000]
    pairs=[(a,b) for a in values for b in values]
    data=''.join(f'{a:x} {b:x}\n' for a,b in pairs)
    mac=[list(map(lambda x:int(x,16),line.split())) for line in subprocess.check_output([str(binary)],input=data,text=True).splitlines()]
    l=AexLoader(str(MAIN/'plugins_2025/OLMSmoother2.aex'),verbose=False,fast=False)
    mem=l.bump_alloc(16,align=16); rows=[]
    for (a,b),actual in zip(pairs,mac):
        expected=[]
        # MULSS XMM5,[R10] / ADDSS XMM0,XMM5 / DIVSS XMM0,XMM8.
        for pc,end,dst,src in [(0x18000ab64,0x18000ab69,UC_X86_REG_XMM5,None),
                              (0x18000ab9c,0x18000aba0,UC_X86_REG_XMM0,UC_X86_REG_XMM5),
                              (0x18000b17c,0x18000b181,UC_X86_REG_XMM0,UC_X86_REG_XMM8)]:
            l.uc.reg_write(dst,a)
            if src: l.uc.reg_write(src,b)
            else: l.uc.reg_write(UC_X86_REG_R10,mem); l.write_bytes(mem,struct.pack('<I',b))
            l.uc.emu_start(pc,end,count=1)
            expected.append(l.uc.reg_read(dst)&0xffffffff)
        if expected!=actual: rows.append({'dst':hex(a),'src':hex(b),'aex':[hex(v) for v in expected],'mac':[hex(v) for v in actual]})
    single_nan_mismatches=[r for r in rows if not all((int(r[k],16)&0x7fffffff)>0x7f800000 for k in ('dst','src'))]
    report={'pairs':len(pairs),'operations':len(pairs)*3,'single_or_no_nan_mismatches':single_nan_mismatches,'two_nan_payload_open_boundary':rows}
    (SCRATCH/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'pairs':len(pairs),'operations':len(pairs)*3,'single_or_no_nan_mismatches':len(single_nan_mismatches),'two_nan_payload_open_pairs':len(rows)}))
    assert not single_nan_mismatches
if __name__=='__main__':main()
