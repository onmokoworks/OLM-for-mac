#!/usr/bin/env python3
"""Bind original scalar/vector IPP bodies to public planes and the candidate.

No numerical detours/imports. Original IPP init/filter executes with its own
dispatch table. The selected exp interval is tested independently in three builds.
"""
import argparse
from collections import Counter
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
from core import raw_diff, sha
from run import main_checkout
from unicorn.x86_const import UC_X86_REG_XMM0, UC_X86_REG_RSP


def main():
    p=argparse.ArgumentParser()
    for name in ('scratch','trace','source','report'):p.add_argument('--'+name,type=Path,required=True)
    for name in ('width','height','radius'):p.add_argument('--'+name,type=int,required=True)
    p.add_argument('--allow-mismatch',action='store_true')
    p.add_argument('--vector-exp',action='store_true')
    p.add_argument('--generic',action='store_true',help='Compare the mixed scalar/vector circular kernel')
    args=p.parse_args();args.scratch=args.scratch.resolve()
    assert args.scratch.is_relative_to(ROOT/'orchestra/state')
    args.scratch.mkdir(parents=True,exist_ok=True)
    os.environ.update(TMPDIR=str(args.scratch),TMP=str(args.scratch),TEMP=str(args.scratch))
    tempfile.tempdir=str(args.scratch)
    aex=main_checkout()/'plugins_2025/DistanceGradation.aex'
    ld=AexLoader(str(aex),verbose=False,fast=True)
    row=json.loads(args.trace.read_text())['rows'][0]
    pre=bytes.fromhex(row['aex_pre_hex']);post=bytes.fromhex(row['aex_post_hex'])
    w,h,r=args.width,args.height,args.radius
    assert 0<w*h<=4096 and 1<=r<=32 and len(pre)==len(post)==w*h*4
    allocation=ld.bump_alloc(len(pre)+128,align=64);src=allocation+64
    ld.write_bytes(allocation,b'\xa5'*(len(pre)+128));ld.write_bytes(src,pre)
    output=ld.bump_alloc(len(pre)+128,align=64);dst=output+64
    ld.write_bytes(output,b'\xa5'*(len(pre)+128))
    spec=ld.bump_alloc(1024*1024,align=64);scratch=ld.bump_alloc(8*1024*1024,align=64)
    exponent_inputs=set();dispatch=Counter()
    def expin(loader,rip,size):exponent_inputs.add(loader.uc.reg_read(UC_X86_REG_XMM0)&0xffffffff)
    ld.add_code_hook(0x1802997a0,expin)
    vector_calls=[]
    vector_returns=set()
    def vector_in(loader,rip,size):
        vector_calls.append({'input':loader.uc.reg_read(UC_X86_REG_XMM0).to_bytes(16,'little').hex()})
        ret=struct.unpack('<Q',loader.read_bytes(loader.uc.reg_read(UC_X86_REG_RSP),8))[0]
        if ret not in vector_returns:
            vector_returns.add(ret)
            loader.add_code_hook(ret,lambda loader,rip,size:vector_calls[-1].update(output=loader.uc.reg_read(UC_X86_REG_XMM0).to_bytes(16,'little').hex()))
    ld.add_code_hook(0x180ba5780,vector_in)
    for address in (0x1806be1e0,0x1806b7d40,0x1806b6b40,0x1806bd600):
        ld.add_code_hook(address,lambda loader,rip,size:dispatch.update([hex(rip)]))
    init=ld.call_function(0x18000c280,[100,w|(h<<32),r,13,1,2,0x3f800000,0x3f800000,spec])
    assert init['rax']==0 and not ld.import_log
    offset=ld.read_bytes(spec,1)[0]
    count=1 if r==1 else sum(x*x+y*y<=r*r for y in range(-r,r+1) for x in range(-r,r+1))
    spatial=ld.read_bytes(spec+offset+0x24,count*4)
    result=ld.call_function(0x18000c2f0,[src,w*4,dst,w*4,w|(h<<32),1,0,spec,scratch],max_instructions=200_000_000)
    actual=ld.read_bytes(dst,len(post))
    assert result['rax']==0 and not ld.import_log
    assert ld.read_bytes(output,64)==ld.read_bytes(dst+len(post),64)==b'\xa5'*64
    assert ld.read_bytes(src,len(pre))==pre
    assert actual==post,raw_diff(post,actual,32)
    report=dict(schema='olm.dg-C19-bilateral/1',kernel='generic' if args.generic else 'radius-one' if r==1 else 'scalar',aex_sha256=sha(aex.read_bytes()),
                source_sha256=sha(args.source.read_bytes()),geometry=[w,h],radius=r,
                public_output_sha256=row.get('oracle_sha256',row.get('public_callback_sha256')),
                original_post_sha256=sha(post),original_body_sha256=sha(actual),dispatch=dict(dispatch),
                original_imports=[],spatial_count=count,spatial_hex=spatial.hex(),builds=[])
    report['vector_exp_calls']=list(vector_calls)
    report['vector_exp_coefficients']={hex(a):ld.read_bytes(a,16).hex() for a in range(0x1815f0600,0x1815f0940,0x40)}
    rng=random.Random(19)
    u=lambda value:struct.unpack('<I',struct.pack('<f',value))[0]
    inputs=sorted(exponent_inputs|{0,0x80000000,u(-25.),u(-25.+2**-19),
        *(u(-25*i/4096) for i in range(4097)),
        *(0x80000000|rng.randrange(0x41c80001) for _ in range(4096))})
    if args.vector_exp:
        used={bits for call in vector_calls for bits in struct.unpack('<4I',bytes.fromhex(call['input']))}
        inputs=sorted(used|{0,0x80000000,u(-.5),u(-.5+2**-25),
            *(u(-i/8192) for i in range(4097)),
            *(0x80000000|rng.randrange(0x3f000001) for _ in range(4096))})
        differences=[]
        for call in report['vector_exp_calls']:
            for inp,out in zip(struct.unpack('<4I',bytes.fromhex(call['input'])),struct.unpack('<4I',bytes.fromhex(call['output']))):
                scalar=ld.call_function(0x18144ee30,float_args={0:struct.pack('<I',inp)})['xmm0'][:4]
                if scalar!=struct.pack('<I',out):
                    differences.append(dict(input=f'{inp:08x}',vector=f'{out:08x}',scalar=scalar.hex()))
        report['consumed_vector_vs_scalar']=differences
    expected=b''
    for bits in inputs:
        value=ld.call_function(0x180ba5780 if args.vector_exp else 0x18144ee30,
            float_args={0:struct.pack('<I',bits)*(4 if args.vector_exp else 1)})
        assert not ld.import_log
        expected+=value['xmm0'][:4]
    report.update(exp_count=len(inputs),used_exp_count=len(used) if args.vector_exp else len(exponent_inputs),
                  exp_backend='vector-180ba5780' if args.vector_exp else 'scalar-18144ee30',exp_output_sha256=sha(expected))
    source=args.source.read_text().replace('#include "OLMDistanceGradation.h"',
        '#include "'+str(ROOT/'mac/OLMDistanceGradation/OLMDistanceGradation.h')+'"').replace('"../../core/','"'+str(ROOT/'core')+'/').replace('"../../ucrtmath/','"'+str(ROOT/'ucrtmath')+'/')
    try:
      with tempfile.TemporaryDirectory(dir=args.scratch) as td:
        td=Path(td);local=td/'candidate.cpp';local.write_text(source)
        ip=td/'exp.bin';ip.write_bytes(b''.join(struct.pack('<I',v) for v in inputs))
        plane=td/'pre.bin';plane.write_bytes(pre)
        cpp=td/'probe.cpp';cpp.write_text('#include "dg_renderbits_real_harness_20260716_sdk_shim.h"\n#include '+json.dumps(str(local))+'''
#include <fstream>
int main(int argc,char **argv) {
  std::ifstream in(argv[1],std::ios::binary);std::ofstream out(argv[2],std::ios::binary);
  std::vector<float> data;float v;while(in.read((char*)&v,4))data.push_back(v);
  if(argc==6) {
    if(std::stoi(argv[5])==1)bilateral_blur_opencv455_f32x4(data.data(),std::stol(argv[3]),std::stol(argv[4]));
    else bilateral_blur_ipp_scalar(data.data(),std::stol(argv[3]),std::stol(argv[4]),std::stoi(argv[5]));
  }
  else for(float &x:data)x=bilateral_ipp_exp(x);
  out.write((char*)data.data(),data.size()*4);return 0;
}
'''.replace('else for(float &x:data)x=bilateral_ipp_exp(x);',
            'else for(float &x:data)x=bilateral_ipp_vector_exp(x);' if args.vector_exp else 'else for(float &x:data)x=bilateral_ipp_exp(x);'))
        if args.generic:
            cpp.write_text(cpp.read_text().replace('if(std::stoi(argv[5])==1)', 'if(false)').replace('else bilateral_blur_ipp_scalar(', 'else bilateral_blur_ipp_general('))
        for name,flags in [('o2',['-O2','-ffp-contract=off']),('o3',['-O3','-ffp-contract=fast']),
                           ('san',['-O2','-fsanitize=address,undefined','-fno-sanitize-recover=all'])]:
            exe=td/name;out=td/(name+'.bin');filtered=td/(name+'-plane.bin')
            subprocess.run(['clang++','-std=c++17',*flags,'-I',str(ROOT/'tools/emulation'),
                '-I',str(ROOT/'tools/emulation/dg_renderbits_real_harness_20260716'),str(cpp),
                str(ROOT/'core/olmdistancegradation_fieldgen.cpp'),'-o',str(exe)],check=True,capture_output=True)
            env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0',UBSAN_OPTIONS='halt_on_error=1')
            subprocess.run([str(exe),str(ip),str(out)],check=True,capture_output=True,env=env)
            subprocess.run([str(exe),str(plane),str(filtered),str(w),str(h),str(r)],check=True,capture_output=True,env=env)
            expdiff=raw_diff(expected,out.read_bytes(),32);diff=raw_diff(post,filtered.read_bytes(),32)
            report['builds'].append(dict(name=name,exp_diff=expdiff,post_diff=diff))
            print(name,'exp',expdiff,'post',diff,flush=True)
        assert all(not b['exp_diff']['different_words'] for b in report['builds'])
        if not args.allow_mismatch:
            assert all(not b['post_diff']['different_words'] for b in report['builds'])
    finally:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')


if __name__=='__main__':main()
