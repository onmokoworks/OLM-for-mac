#!/usr/bin/env python3
"""Compare the recovered C++ float sine/cosine against original AEX leaf calls."""

from pathlib import Path as _HarnessPath
_UCRT_CXX = str(_HarnessPath(__file__).resolve().parents[2] / "tools/ucrt_cxx.py")
import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import struct
import subprocess
import sys

sys.dont_write_bytecode = True
from aex_loader import AexLoader
from unicorn.x86_const import (UC_X86_REG_XMM3, UC_X86_REG_XMM13,
    UC_X86_REG_XMM6, UC_X86_REG_XMM7, UC_X86_REG_XMM8,
    UC_X86_REG_RBP, UC_X86_REG_R15, UC_X86_REG_ESI, UC_X86_REG_EBX)
ROOT = Path(__file__).resolve().parents[2]
MAIN = ROOT.parent.parent if ROOT.parent.name == 'worktrees' else ROOT


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--scratch', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    args = p.parse_args()
    scratch = args.scratch.resolve()
    assert scratch.is_relative_to(ROOT / 'orchestra/state')
    scratch.mkdir(parents=True, exist_ok=True)
    os.environ.update(TMPDIR=str(scratch), TMP=str(scratch), TEMP=str(scratch))
    aex = MAIN / 'plugins_2025/OLMKiraKira.aex'
    ld = AexLoader(str(aex), verbose=False, fast=True)
    # A known-answer import-free reader also checks the fifth stack argument.
    src = ld.host_alloc(16); dst = ld.host_alloc(16)
    ld.write_bytes(src, bytes([255,255,0,0]))
    ld.call_function(0x181230a80, int_args=[dst,dst+4,dst+8,dst+12,src], max_instructions=1000)
    assert ld.read_bytes(dst,16) == struct.pack('<4f',1,0,0,1)
    cpp = scratch / 'leaf.cpp'
    cpp.write_text('#include "'+str(ROOT/'core/kirakira_sincos.h')+'"\n'+r'''
#include <cstdio>
int main(int argc, char **) {
    using namespace olm::kirakira;
    if (argc > 1) {
        int32_t row[3];
        while (std::fread(row,12,1,stdin)==1) {
            const float radians = static_cast<float>(static_cast<double>(row[0]) * 0x1.1df46a2529d39p-6);
            const auto pair = extent_sincos(row[0]);
            const float ac = std::abs(pair.cosine), as = std::abs(pair.sine);
            const int32_t sizes[] = {rotated_extent(row[1],row[2],ac,as), rotated_extent(row[2],row[1],ac,as)};
            std::fwrite(&radians,4,1,stdout); std::fwrite(&pair,8,1,stdout); std::fwrite(sizes,8,1,stdout);
        }
        return 0;
    }
    if (std::fwrite(embedded_trig::reduction, 1, 3072, stdout) != 3072) return 1;
    if (std::fwrite(embedded_trig::reconstruction, 1, 4096, stdout) != 4096) return 1;
    float x;
    while (std::fread(&x,4,1,stdin)==1) {
        const auto pair = embedded_sincos(x);
        if (std::fwrite(&pair,8,1,stdout)!=1) return 1;
        using namespace embedded_trig;
        const float shifted = std::abs(x) + word(0x3fc90fdb);
        const uint64_t products[] = {reduction_product(bits(x)), reduction_product(bits(shifted))};
        if (std::fwrite(products,16,1,stdout)!=1) return 1;
    }
}
''')
    exe = scratch/'leaf'
    subprocess.run([_UCRT_CXX,'-std=c++17','-O2','-fno-fast-math','-ffp-contract=off',str(cpp),'-o',str(exe)],check=True)
    bits = lambda x: struct.unpack('<I', struct.pack('<f',x))[0]
    inputs = set()
    # Dense degrees, dense direct radians crossing both reduction branches,
    # and adjacent float words at the small branch and range-reduction boundary.
    inputs.update(bits(i/100 * float.fromhex('0x1.1df46a2529d39p-6')) for i in range(-72000,72001))
    inputs.update(bits(i*0.5) for i in range(-24000,24001))
    for x in [0.0,2**-13,10000.0,10000.0-struct.unpack('<f',bytes.fromhex('db0fc93f'))[0],
              1.5707963267948966,3.141592653589793]:
        u = bits(x)
        for delta in range(-8,9):
            if u+delta >= 0:
                inputs.add(u+delta); inputs.add((u+delta)|0x80000000)
    rng = random.Random(11)
    inputs.update(rng.randrange(0,0x7f800000) | (rng.randrange(2)<<31) for _ in range(12000))
    inputs.update([0x7f7fffff,0xff7fffff,0x7f800000,0xff800000,
                   0x7fc00000,0xffc01234,0x7f800001,0xff800123])
    inputs = sorted(inputs)
    raw = b''.join(struct.pack('<I',u) for u in inputs)
    output = subprocess.run([str(exe)],input=raw,stdout=subprocess.PIPE,check=True).stdout
    assert output[:7168] == ld.read_bytes(0x18191b100,7168), 'binary coefficient tables differ'
    records = output[7168:]
    output = b''.join(records[i:i+8] for i in range(0,len(records),24))
    assert len(output) == len(inputs)*8
    report = dict(aex_sha256=hashlib.sha256(aex.read_bytes()).hexdigest(),
                  cases=len(inputs),input_sha256=hashlib.sha256(raw).hexdigest(),
                  candidate_sha256=hashlib.sha256(output).hexdigest(),abi_leaf_exact=True,routes=[])
    observed_product = []
    def product_boundary(ld, _addr, _size):
        hi = ld.uc.reg_read(UC_X86_REG_XMM3)
        lo = ld.uc.reg_read(UC_X86_REG_XMM13)
        observed_product[:] = [(((hi >> (i*32)) & 0xffffffff) << 32) |
                              ((lo >> (i*32)) & 0xffffffff) for i in [0,1]]
    ld.add_code_hook(0x18132c7cb,product_boundary)
    for dispatch in [1,2]:
        ld.write_bytes(0x181827ee8,struct.pack('<I',dispatch))
        mismatches = []; oracle = bytearray(); products_checked = 0
        for i,u in enumerate(inputs):
            observed_product.clear()
            result = ld.call_function(0x18132b2e0,float_args={0:struct.pack('<I',u)},max_instructions=10000)['xmm0'][:8]
            oracle.extend(result)
            actual = output[i*8:i*8+8]
            if result != actual:
                if len(mismatches)<8:
                    mismatches.append(dict(input_hex=f'{u:08x}',aex=result.hex(),mac=actual.hex()))
            if observed_product and u & 0x7f800000 != 0x7f800000:
                expected_products = struct.unpack('<2Q',records[i*24+8:i*24+24])
                assert tuple(observed_product) == expected_products, (hex(u), observed_product, expected_products)
                products_checked += 2
        count = sum(oracle[i:i+8]!=output[i:i+8] for i in range(0,len(output),8))
        report['routes'].append(dict(dispatch=dispatch,mismatches=count,first=mismatches,products_checked=products_checked,
                                    oracle_sha256=hashlib.sha256(oracle).hexdigest()))
        args.report.write_text(json.dumps(report,indent=2)+'\n')
        print(dispatch,len(inputs),'cases',count,'mismatches',mismatches[:1],flush=True)
    assert all(r['mismatches']==0 for r in report['routes'])
    # Execute the original conversion, sincos call, and MULSS/ADDSS/CVTTSS2SI
    # extent block, stopping before workspace allocation at 18114f7f8.
    rows = [(a,w,h) for a in range(-720,721) for w,h in [(1,9),(9,1),(31,27)]]
    rows += [(rng.randrange(-2147483648,2147483648),rng.randrange(1,4097),rng.randrange(1,4097)) for _ in range(2000)]
    raw = b''.join(struct.pack('<3i',*r) for r in rows)
    expected = subprocess.run([str(exe),'geometry'],input=raw,stdout=subprocess.PIPE,check=True).stdout
    frame = ld.host_alloc(0x700); angle = ld.host_alloc(8)
    captured = {}
    from unicorn.x86_const import UC_X86_REG_XMM0
    def radians_boundary(ld, _addr, _size):
        captured['radians'] = struct.pack('<I',ld.uc.reg_read(UC_X86_REG_XMM0)&0xffffffff)
    def trig_boundary(ld, _addr, _size):
        captured['trig'] = (ld.uc.reg_read(UC_X86_REG_XMM0)&((1<<64)-1)).to_bytes(8,'little')
    ld.add_code_hook(0x18114f78b,radians_boundary)
    ld.add_code_hook(0x18114f790,trig_boundary)
    ld.add_code_hook(0x18114f7f8,lambda ld,a,s: ld.uc.emu_stop())
    actual = bytearray()
    for a,w,h in rows:
        ld.write_bytes(angle,struct.pack('<i',a))
        ld.write_bytes(frame+0x5e0,struct.pack('<i',w)); ld.write_bytes(frame+0x5e8,struct.pack('<i',h))
        for reg,value in [(UC_X86_REG_RBP,frame),(UC_X86_REG_R15,angle),
                          (UC_X86_REG_XMM6,0x7fffffff),(UC_X86_REG_XMM7,bits(4.0)),
                          (UC_X86_REG_XMM8,0x3f91df46a2529d39)]:
            ld.uc.reg_write(reg,value)
        ld.call_function(0x18114f779,max_instructions=10000)
        actual.extend(captured['radians']+captured['trig']+struct.pack('<2I',
            ld.uc.reg_read(UC_X86_REG_ESI),ld.uc.reg_read(UC_X86_REG_EBX)))
    report['geometry'] = dict(cases=len(rows),mismatches=sum(actual[i:i+20]!=expected[i:i+20] for i in range(0,len(expected),20)),
        input_sha256=hashlib.sha256(raw).hexdigest(),oracle_sha256=hashlib.sha256(actual).hexdigest(),
        candidate_sha256=hashlib.sha256(expected).hexdigest())
    args.report.write_text(json.dumps(report,indent=2)+'\n')
    assert actual == expected, report['geometry']
    print('geometry',len(rows),'exact',flush=True)


if __name__ == '__main__':
    main()
