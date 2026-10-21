#!/usr/bin/env python3
"""Execute original bounded Offset/span prefixes and test the render helper.

The sparse context fields are the leaf ABI read set established from 24c0 and
1c90. No import stubs are called. Full scalar tables stay in the private output.
"""
import argparse
import json
import struct
import subprocess
from pathlib import Path

import probe_radialblur_offset_20261002 as offset
from aex_loader import AexLoader
from unicorn.x86_const import UC_X86_REG_RAX, UC_X86_REG_RCX, UC_X86_REG_R10, UC_X86_REG_R14, UC_X86_REG_RIP
n=offset.noop
p=offset.public


def dynamic_spans(out, source):
    out.mkdir(parents=True, exist_ok=False)
    old = """const A_long product = (radius_count / 2) * offset;
    const float reciprocal = RadialF32Div(1.0f, static_cast<float>(radius_index + 1));
    const A_long dynamic = RadialCVTTSS2SI(RadialF32Mul(static_cast<float>(product), reciprocal));"""
    assert source.count(old) == 1
    counterfactual = source.replace(old, 'const A_long dynamic = DynamicOffsetForRadius(radius_count, offset, radius_index);')
    loader=AexLoader(str(p.initial.AEX),verbose=False,fast=True);context=loader.bump_alloc(0x3aa00);loader.write_bytes(context,bytes(0x3aa00))
    base=loader.image_base;raw={}
    loader.add_code_hook(base+0x25e8,lambda l,a,s:l.uc.emu_stop())
    loader.add_code_hook(base+0x1cfb,lambda l,a,s:raw.update(span=l.uc.reg_read(UC_X86_REG_R10)&0xffffffff))
    loader.add_code_hook(base+0x1d1d,lambda l,a,s:l.uc.emu_stop())
    f32=lambda x:struct.unpack('<f',struct.pack('<f',x))[0]
    bits=lambda x:struct.unpack('<I',struct.pack('<f',x))[0]
    rows=[];lines=[];sequence=0
    for quality in [1,3.4,50]:
     scale=0.2/f32(1/f32(quality))
     for radius in [2,9,4096]:
      indices=sorted(set([0,min(17,radius-1),min(40,radius-1),radius-1]))
      for ri in indices:
       for ui in range(501):
        offset=int(ui*scale);other=int((500-ui)*scale)
        loader.write_bytes(context+0x28,struct.pack('<2i',offset,0));loader.write_bytes(context+0x30,struct.pack('<i',other))
        loader.call_function(base+0x24c0,int_args=[context,0,0,0,0,1,radius,ri,ri+1],max_instructions=1000)
        assert loader.uc.reg_read(UC_X86_REG_RIP)==base+0x25e8 and not loader.import_log
        dynamic=loader.uc.reg_read(UC_X86_REG_RCX)&0xffffffff;inner=loader.uc.reg_read(UC_X86_REG_RAX)&0xffffffff
        expected=lambda v:int(f32(f32((radius//2)*v)*f32(1/f32(ri+1))))
        assert (dynamic,inner)==(expected(offset),expected(other))
        for direction in [0,1]:
         value=offset if direction==0 else other;d=dynamic if direction==0 else inner
         strength=int(([0,4,2000][sequence%3])*scale)
         factor=[0.,0.5,1.][sequence%3];fb=bits(factor)
         for mode in [1,2,3]:
          loader.write_bytes(context+0x24+8*direction,struct.pack('<i',mode))
          loader.write_bytes(context+0x3a9e8+4*direction,struct.pack('<i',strength))
          loader.call_function(base+0x1c90,int_args=[context,direction,d,0,0,0,0,0,0,fb,0,0,0],max_instructions=1000)
          assert loader.uc.reg_read(UC_X86_REG_RIP)==base+0x1d1d and not loader.import_log
          effective=loader.uc.reg_read(UC_X86_REG_R14)&0xffffffff
          lines.append(f'{radius} {ri} {strength} {value} {mode} {fb}\n')
          rows.append(dict(quality=quality,offset_ui=ui if direction==0 else 500-ui,radius_count=radius,radius_index=ri,strength=strength,offset=value,mode=mode,direction=direction,factor_bits=fb,native_dynamic=d,native_raw_span=raw['span'],native_effective=effective))
         sequence+=1
       print('OFFSET_LEAF_NATIVE',quality,radius,ri,len(rows),flush=True)
    (out/'inputs.txt').write_text(''.join(lines))
    harness='''#include "production_under_test.cpp"
    #include <iostream>
    int main(){A_long radius,ri,strength,offset,mode;unsigned bits;
     while(std::cin>>radius>>ri>>strength>>offset>>mode>>bits){float factor;std::memcpy(&factor,&bits,4);
     const A_long span=RotationResolvedSpanForRadius(strength,offset,mode,radius,ri);
     const A_long effective=std::max<A_long>(0,(A_long)RadialF32Mul((float)std::min<A_long>(span,3000),factor));
     std::cout<<span<<" "<<effective<<"\\n";} }
    '''
    hp=out/'leaf.cpp';hp.write_text(harness);previous=p.initial.HARNESS;p.initial.HARNESS=hp;comparisons={}
    try:
     for name,text,sanitize in [('before',counterfactual,False),('o2',source,False),('san',source,True)]:
      binary=p.build(out/name,text,sanitize);run=subprocess.run([str(binary)],input=''.join(lines),capture_output=True,text=True,check=True,env=n.ENV);assert not run.stderr
      (out/(name+'_output.txt')).write_text(run.stdout);values=[list(map(int,line.split())) for line in run.stdout.splitlines()];assert len(values)==len(rows)
      different=[i for i,(v,row) in enumerate(zip(values,rows)) if v!=[row['native_raw_span'],row['native_effective']]]
      if name!='before':assert not different,(name,different[:3])
      comparisons[name]=dict(case_count=len(values),different_cases=len(different),output_sha256=p.sha(run.stdout.encode()),first_different_witnesses=[rows[i] for i in different[:8]])
      print('OFFSET_LEAF_SDK',name,len(values),len(different),flush=True)
    finally:p.initial.HARNESS=previous
    # Raw scalar case tables stay private in the output directory.
    (out/'native_cases.json').write_text(json.dumps(rows)+'\n')
    r=dict(schema='radialblur.offset-dynamic-leaf/1',source_sha256=p.sha(source.encode()),before_shared_source_sha256=p.sha(counterfactual.encode()),case_count=len(rows),comparisons=comparisons,original_aex_sha256=p.sha(p.initial.AEX.read_bytes()),original_prefixes=['24c0..25e8','1c90..1d1d'],integer_ui_offset_range=[0,500],qualities=[1,3.4,50],radius_counts=[2,9,4096],original_import_call_count=0,production_promoted=False,claims_not_made=['This directly executes bounded original prefixes in a disposable interpreter and tests the actual helper used by the private render candidate; it does not execute a native Windows AE frame.'])
    return r


def setup_cases():
    cases=[]
    for family in [1,2]:
        for quality in [3.4,50]:
            for mode in [1,2,3]:
                for value in [0,1,499,500]:
                    params=p.initial.settings(family,1,1)
                    changes={5:mode,6:value,11:mode,12:500-value,20:quality,10:7}
                    for param in params:
                        if param['slot'] in changes:param['value']=changes[param['slot']]
                    cases.append(dict(family=family,geometry=[1,1],depth=8,pattern='opaque',
                        state='offset_fields',parameters=params))
    return cases


def native_fields(worker,directory):
    quality=n.strength.gain.quality
    previous=quality.field_cases
    try:
        quality.field_cases=setup_cases
        return quality.native_fields(worker,directory)
    finally:quality.field_cases=previous


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--source',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--report',type=Path,required=True)
    args=ap.parse_args()
    result=dynamic_spans(args.output,args.source.read_text())
    args.report.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print('OFFSET_DYNAMIC_LEAF_DONE',result['case_count'],flush=True)


if __name__=='__main__':main()
