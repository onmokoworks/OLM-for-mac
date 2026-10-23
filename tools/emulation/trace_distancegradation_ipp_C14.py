#!/usr/bin/env python3
"""Pair the unmodified original IPP radius-one body and scalar exp with Mac.

Consumes a typed/public-bound C14 PF32 trace, reproduces its complete IPP output
through the lower original API, and checks the restored exp operation separately.
No code detours or imported exp implementations are installed for this body.
"""
from __future__ import annotations

from pathlib import Path as _HarnessPath
_UCRT_CXX = str(_HarnessPath(__file__).resolve().parents[2] / "tools/ucrt_cxx.py")
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import random
import struct
import subprocess
import sys
import tempfile
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/fuzz'))
from aex_loader import AexLoader
from core import raw_diff
from run import main_checkout
from unicorn.x86_const import UC_X86_REG_XMM0


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--scratch',type=Path,required=True)
    p.add_argument('--trace',type=Path,required=True)
    p.add_argument('--width',type=int,required=True)
    p.add_argument('--height',type=int,required=True)
    p.add_argument('--report',type=Path,required=True)
    args=p.parse_args();args.scratch=args.scratch.resolve()
    assert args.scratch.is_relative_to(ROOT/'orchestra/state/C14-dg-smart-r3')
    args.scratch.mkdir(parents=True,exist_ok=True)
    os.environ.update(TMPDIR=str(args.scratch),TMP=str(args.scratch),TEMP=str(args.scratch))
    tempfile.tempdir=str(args.scratch)
    aex=main_checkout()/'plugins_2025/DistanceGradation.aex'
    ld=AexLoader(str(aex),verbose=False,fast=True)
    row=json.loads(args.trace.read_text())['rows'][0]
    pre=bytes.fromhex(row['aex_pre_hex']);post=bytes.fromhex(row['aex_post_hex'])
    w,h=args.width,args.height;assert 0<w*h<=256 and w>0 and h>0 and len(pre)==w*h*4
    src=ld.bump_alloc(len(pre),align=64);ld.write_bytes(src,pre)
    dst=ld.bump_alloc(len(pre),align=64)
    spec=ld.bump_alloc(65536,align=64);scratch=ld.bump_alloc(65536,align=64)
    init=ld.call_function(0x18000c280,[100,w|(h<<32),1,13,1,2,0x3f800000,0x3f800000,spec])
    assert init['rax']==0 and not ld.import_log
    weights=[]
    def expin(loader,rip,size):weights.append([loader.uc.reg_read(UC_X86_REG_XMM0)&0xffffffff])
    def expout(loader,rip,size):weights[-1].append(loader.uc.reg_read(UC_X86_REG_XMM0)&0xffffffff)
    ld.add_code_hook(0x1802997a0,expin)
    for addr in (0x1806bd7d0,0x1806bd7f8,0x1806bd816,0x1806bd83e):ld.add_code_hook(addr,expout)
    result=ld.call_function(0x18000c2f0,[src,w*4,dst,w*4,w|(h<<32),1,0,spec,scratch])
    actual=ld.read_bytes(dst,len(post))
    assert result['rax']==0 and not ld.import_log and actual==post
    u=lambda f:struct.unpack('<I',struct.pack('<f',f))[0]
    f=lambda u:struct.unpack('<f',struct.pack('<I',u))[0]
    assert len(weights)==w*h*4 and all(len(x)==2 for x in weights)
    used=sorted(set(tuple(x) for x in weights))
    lib=ctypes.CDLL(None);lib.expf.argtypes=[ctypes.c_float];lib.expf.restype=ctypes.c_float
    host_diff=[dict(input_bits=f'{i:08x}',original_bits=f'{o:08x}',host_bits=f'{u(lib.expf(f(i))):08x}')
               for i,o in used if o!=u(lib.expf(f(i)))]
    rng=random.Random(14)
    inputs=sorted({0,0x80000000,0xbf000000,0xbd4ccccc,0xbd4ccccd,0xbd4cccce,
                   *(i for i,o in used),*(u(-i/8192) for i in range(4097)),
                   *(0x80000000|rng.randrange(0x3f000001) for _ in range(4096))})
    expected=[]
    for bits in inputs:
        result=ld.call_function(0x18144ee30,float_args={0:struct.pack('<I',bits)})
        assert not ld.import_log
        expected.append(result['xmm0'][:4])
    expected=b''.join(expected)
    source=ROOT/'mac/OLMDistanceGradation/OLMDistanceGradation.cpp'
    with tempfile.TemporaryDirectory(dir=args.scratch) as tmp:
        tmp=Path(tmp);ip=tmp/'input';ip.write_bytes(b''.join(struct.pack('<I',i) for i in inputs))
        cpp=tmp/'probe.cpp';cpp.write_text('#include "dg_renderbits_real_harness_20260716_sdk_shim.h"\n#include '+json.dumps(str(source))+'''
#include <fstream>
int main(int argc,char **argv) {
  std::ifstream in(argv[1],std::ios::binary);std::ofstream out(argv[2],std::ios::binary);
  float v;while(in.read((char*)&v,4)){v=bilateral_ipp_exp(v);out.write((char*)&v,4);}return 0;
}
''')
        builds=[]
        for name,flags in [('o2',['-O2','-ffp-contract=off']),('o3_contract',['-O3','-ffp-contract=fast']),
                           ('san',['-O2','-fsanitize=address,undefined','-fno-sanitize-recover=all'])]:
            exe=tmp/name;out=tmp/(name+'.bin')
            subprocess.run([_UCRT_CXX,'-std=c++17',*flags,'-I',str(ROOT/'tools/emulation'),
                            '-I',str(ROOT/'tools/emulation/dg_renderbits_real_harness_20260716'),str(cpp),
                            str(ROOT/'core/olmdistancegradation_fieldgen.cpp'),'-o',str(exe)],check=True,capture_output=True)
            env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0',UBSAN_OPTIONS='halt_on_error=1')
            subprocess.run([str(exe),str(ip),str(out)],check=True,capture_output=True,env=env)
            diff=raw_diff(expected,out.read_bytes(),32);assert expected==out.read_bytes(),(name,diff)
            builds.append(dict(name=name,flags=flags,exact_words=len(inputs),sha256=hashlib.sha256(expected).hexdigest()))
    report=dict(schema='olm.dg-ipp-C14/1',aex_sha256=hashlib.sha256(aex.read_bytes()).hexdigest(),
        source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),trace_label=row['label'],geometry=[w,h],
        public_callback_sha256=row['public_callback_sha256'],original_body_exact_words=w*h,
        original_body_imports=[],original_body_sha256=hashlib.sha256(actual).hexdigest(),
        original_dispatch_index=struct.unpack('<i',ld.read_bytes(0x1818a2ae0,4))[0],
        original_body_addresses=['18000c280','18000c2f0','1806bd740','1802997a0','18144ee30'],
        weight_calls=len(weights),distinct_weight_inputs=len(used),host_expf_differences=host_diff,
        coefficient_bytes_sha256=hashlib.sha256(ld.read_bytes(0x18144f000,0x818)).hexdigest(),
        exp_input_sha256=hashlib.sha256(b''.join(struct.pack('<I',i) for i in inputs)).hexdigest(),builds=builds)
    args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('original body exact',w*h,'exp exact',len(inputs),'host differences',len(host_diff),flush=True)

if __name__=='__main__':main()
