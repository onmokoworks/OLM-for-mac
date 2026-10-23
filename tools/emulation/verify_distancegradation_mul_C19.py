#!/usr/bin/env python3
"""Compare weighted samples to the original callback's single MULSS instruction.

No arithmetic detour: execute 181170f8b with original bytes and stop before
the following instruction. The second operand is a finite field weight.
"""

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
import tempfile
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/fuzz'))
from aex_loader import AexLoader
from run import main_checkout
from core import raw_diff
from unicorn.x86_const import UC_X86_REG_XMM6, UC_X86_REG_XMM2


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--scratch', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    args=p.parse_args();args.scratch=args.scratch.resolve()
    assert args.scratch.is_relative_to(ROOT/'orchestra/state/C19-dg-smart-r4')
    args.scratch.mkdir(parents=True,exist_ok=True)
    os.environ.update(TMPDIR=str(args.scratch),TMP=str(args.scratch),TEMP=str(args.scratch),
                      ASAN_OPTIONS='detect_leaks=0',UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
    tempfile.tempdir=str(args.scratch)
    ld=AexLoader(str(main_checkout()/'plugins_2025/DistanceGradation.aex'),verbose=False,fast=True)
    instruction=ld.read_bytes(0x181170f8b,4)
    assert instruction.hex()=='f30f59f2'
    samples=[0,0x80000000,1,0x80000001,0x3f000000,0x3f800000,0xbf800000,
             0x7f7fffff,0xff7fffff,0x7f800000,0xff800000,0x7fc12345,0xff812346,
             0x7f812346,0xffc12345]
    weights=[0,0x80000000,1,0x00800000,0x3e800000,0x3f000000,0x3f7fffff,0x3f800000]
    rng=random.Random(19)
    pairs=[(s,w) for s in samples for w in weights]
    pairs += [(rng.getrandbits(32),rng.randrange(0x3f800001)) for _ in range(1024)]
    expected=bytearray()
    for sample,weight in pairs:
        ld.uc.reg_write(UC_X86_REG_XMM6,sample)
        ld.uc.reg_write(UC_X86_REG_XMM2,weight)
        ld.uc.emu_start(0x181170f8b,0x181170f8f,count=1)
        expected += struct.pack('<I',ld.uc.reg_read(UC_X86_REG_XMM6)&0xffffffff)
    source=args.source.resolve()
    report=dict(schema='olm.dg-C19-mul/1',instruction_hex=instruction.hex(),count=len(pairs),
                source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                expected_sha256=hashlib.sha256(expected).hexdigest(),builds=[])
    with tempfile.TemporaryDirectory(dir=args.scratch) as td:
        td=Path(td);inp=td/'pairs.bin';inp.write_bytes(b''.join(struct.pack('<II',*pair) for pair in pairs))
        # Resolve relative includes for scratch candidate translation units.
        text=source.read_text().replace('#include "OLMDistanceGradation.h"',
            '#include "'+str(ROOT/'mac/OLMDistanceGradation/OLMDistanceGradation.h')+'"').replace('"../../core/','"'+str(ROOT/'core')+'/')
        local=td/'candidate.cpp';local.write_text(text)
        cpp=td/'probe.cpp';cpp.write_text('#include "dg_renderbits_real_harness_20260716_sdk_shim.h"\n#include '+json.dumps(str(local))+'''
#include <fstream>
int main(int argc,char **argv) {
  std::ifstream in(argv[1],std::ios::binary);std::ofstream out(argv[2],std::ios::binary);
  float pair[2];while(in.read((char*)pair,8)) {
    float v=smart_weighted_sample(pair[0],pair[1]);out.write((char*)&v,4);
  }return 0;
}
''')
        for name,flags in [('o2',['-O2','-ffp-contract=off']),('o3',['-O3','-ffp-contract=fast']),
                           ('san',['-O2','-fsanitize=address,undefined','-fno-sanitize-recover=all'])]:
            exe=td/name;output=td/(name+'.bin')
            subprocess.run([_UCRT_CXX,'-std=c++17',*flags,'-I',str(ROOT/'tools/emulation'),
                            '-I',str(ROOT/'tools/emulation/dg_renderbits_real_harness_20260716'),
                            str(cpp),str(ROOT/'core/olmdistancegradation_fieldgen.cpp'),'-o',str(exe)],check=True)
            subprocess.run([str(exe),str(inp),str(output)],check=True)
            actual=output.read_bytes();diff=raw_diff(expected,actual,32)
            report['builds'].append(dict(name=name,diff=diff,exact=actual==expected))
            print(name,len(pairs),actual==expected,diff,flush=True)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    assert all(b['exact'] for b in report['builds'])


if __name__=='__main__':main()
