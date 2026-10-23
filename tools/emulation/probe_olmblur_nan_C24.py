#!/usr/bin/env python3
"""Replay observed Legacy SSE operands on arm64 and macOS x86_64 (Rosetta).

The original AEX instruction matrix is independent of the public trace.
This diagnoses an oracle boundary; neither Rosetta nor Unicorn is Windows AE.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile

from aex_loader import AexLoader
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from unicorn.x86_const import UC_X86_REG_XMM0, UC_X86_REG_XMM2, UC_X86_REG_XMM9

ROOT = Path(__file__).resolve().parents[2]
CPP = r'''
#include <cstdio>
#include <cstring>
int main() {
    unsigned in[3];
    while (std::fread(in, 4, 3, stdin) == 3) {
        float a,b,r;
        std::memcpy(&a,in+1,4); std::memcpy(&b,in+2,4);
#if defined(__x86_64__)
        switch(in[0]) {
        case 0: asm("addss %1,%0":"+x"(a):"x"(b)); break;
        case 1: asm("mulss %1,%0":"+x"(a):"x"(b)); break;
        default: asm("divss %1,%0":"+x"(a):"x"(b));
        }
        r=a;
#else
        switch(in[0]) {
        case 0: asm("fadd %s0,%s1,%s2":"=w"(r):"w"(a),"w"(b)); break;
        case 1: asm("fmul %s0,%s1,%s2":"=w"(r):"w"(a),"w"(b)); break;
        default: asm("fdiv %s0,%s1,%s2":"=w"(r):"w"(a),"w"(b));
        }
#endif
        std::fwrite(&r,4,1,stdout);
    }
}
'''


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--scratch', type=Path, required=True)
    p.add_argument('--trace', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    args = p.parse_args()
    scratch = args.scratch.resolve()
    assert scratch.is_relative_to(ROOT/'orchestra/state')
    scratch.mkdir(parents=True, exist_ok=True)
    os.environ.update(TMPDIR=str(scratch), TMP=str(scratch), TEMP=str(scratch),
                      ASAN_OPTIONS='detect_leaks=0:halt_on_error=1', UBSAN_OPTIONS='halt_on_error=1')
    trace = json.loads(args.trace.read_text())
    assert all(r['cached_binding'] for r in trace['rows'])
    rows = [dict(r, case=case['index'], kind='public-trace')
            for case in trace['rows'] for r in case['nonfinite_ops']]
    aex = ROOT.parent.parent/'plugins_2025/OLMBlur.aex'
    loader = AexLoader(str(aex), verbose=False, fast=False)
    values = [0,0x80000000,0x3f800000,0xbf800000,1,0x7f7fffff,
              0x7f800000,0xff800000,0x7fc12345,0xffc12346,0x7f812345,0xff812346]
    specs = [('addss',0x1800016c0,UC_X86_REG_XMM9,UC_X86_REG_XMM2),
             ('mulss',0x1800016df,UC_X86_REG_XMM0,UC_X86_REG_XMM2),
             ('divss',0x180001803,UC_X86_REG_XMM2,UC_X86_REG_XMM9)]
    instructions = []
    for name,address,left,right in specs:
        ins = next(Cs(CS_ARCH_X86,CS_MODE_64).disasm(loader.read_bytes(address,8),address))
        assert ins.mnemonic == name
        instructions.append(dict(address=hex(address),bytes=bytes(ins.bytes).hex(),operation=name,operands=ins.op_str))
        for a in values:
            for b in values:
                loader.uc.reg_write(left,a); loader.uc.reg_write(right,b)
                loader.uc.emu_start(address,address+ins.size,count=1)
                rows.append(dict(kind='instruction-matrix',operation=name,address=hex(address),
                                 left=a,right=b,result=loader.uc.reg_read(left)&0xffffffff))
    codes = dict(addss=0,mulss=1,divss=2)
    commands = []
    with tempfile.TemporaryDirectory(prefix='nan_',dir=scratch) as tmp:
        tmp = Path(tmp)
        src = tmp/'probe.cpp'; src.write_text(CPP)
        inp = tmp/'input.bin'
        with inp.open('wb') as f:
            for row in rows:f.write(struct.pack('<III',codes[row['operation']],row['left'],row['right']))
        for arch in ('arm64','x86_64'):
            binary = tmp/arch
            cmd = ['clang++','-arch',arch,'-std=c++17','-O2','-fno-fast-math','-ffp-contract=off',str(src),'-o',str(binary)]
            if arch == 'arm64':cmd += ['-fsanitize=address,undefined','-fno-sanitize-recover=all']
            commands.append(cmd)
            subprocess.run(cmd,check=True,capture_output=True)
            cmd = ['/usr/bin/arch','-'+arch,str(binary)]; commands.append(cmd)
            out = tmp/(arch+'.bin')
            with inp.open('rb') as i, out.open('wb') as o:
                result = subprocess.run(cmd,stdin=i,stdout=o,stderr=subprocess.PIPE,check=True)
            assert not result.stderr, result.stderr.decode()
            assert out.stat().st_size == len(rows)*4
            with out.open('rb') as f:
                for row in rows:row[arch]=struct.unpack('<I',f.read(4))[0]
    summary = {}
    for kind in ('public-trace','instruction-matrix'):
        group = [r for r in rows if r['kind']==kind]
        summary[kind] = dict(count=len(group), **{
            arch+'_different':sum(r[arch]!=r['result'] for r in group) for arch in ('arm64','x86_64')})
    report = dict(summary=summary,rows=rows,instructions=instructions,commands=commands,
                  aex_sha256=hashlib.sha256(aex.read_bytes()).hexdigest(),
                  trace_sha256=hashlib.sha256(args.trace.read_bytes()).hexdigest(),
                  scope='Original AEX in Unicorn vs macOS arm64 and x86_64/Rosetta; no native Windows claim')
    args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps(summary,sort_keys=True))
    for row in rows:
        if row['kind']=='public-trace' and row['result']!=row['arm64']:
            print('first native boundary',json.dumps(row,sort_keys=True)); break


if __name__ == '__main__':main()
