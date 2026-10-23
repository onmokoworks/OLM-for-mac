#!/usr/bin/env python3
"""Import-free AEX source-sampler boundary controls; no public-path claim."""
import argparse
import json
import os
from pathlib import Path
import struct
import subprocess
import shutil
import sys
sys.dont_write_bytecode=True
from adapters.radialblur import public
from verify_radialblur_smart_C06 import ROOT,MAIN
from aex_loader import AexLoader
from core import sha,raw_diff
from probe_radialblur_C35 import candidate_source

HARNESS=r'''#include "production_under_test.cpp"
#include <iostream>
int main() {
  unsigned bits[18];
  while(std::cin.read(reinterpret_cast<char*>(bits),sizeof(bits))) {
    float values[18];std::memcpy(values,bits,sizeof(bits));
    FloatImage image;image.width=2;image.height=2;
    image.rgba.assign(values+2,values+18);
    const auto sample=SampleRGBAAEXAlpha(image,values[0],values[1],true);
    std::cout.write(reinterpret_cast<const char*>(sample.rgba),16);
  }
}
'''

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    out=args.output.resolve();assert out.is_relative_to(ROOT/'orchestra/state/C35-radial-smart-r6')
    out.mkdir(parents=True,exist_ok=False)
    os.environ.update(TMPDIR=str(out),TMP=str(out),TEMP=str(out))
    # First control verifies stack ABI; the two others isolate independent skips.
    cases=[('abi',[.25,.5],[.25,.5,.75,1.]*4),
           ('zero_weight',[0.,0.],[.25,.5,.75,1.]+[float('inf'),.5,.75,1.]+[.25,.5,.75,1.]*2),
           ('cancelled_alpha',[.5,0.],[.25,.5,.75,1.]+[.75,.25,.5,-1.]+[.25,.5,.75,1.]*2)]
    aex=MAIN/'aex/OLMRadialBlur/Plugins/64/2025/OLMRadialBlur.aex'
    loader=AexLoader(str(aex),verbose=False,fast=False)
    src=loader.bump_alloc(64);dst=loader.bump_alloc(16)
    expected=[];encoded=[]
    for name,coords,values in cases:
        plane=struct.pack('<16f',*values);coord=struct.pack('<2f',*coords)
        loader.write_bytes(src,plane)
        x,y=struct.unpack('<2I',coord)
        loader.call_function(0x180001520,int_args=[src,dst,2,2,8,x,y],max_instructions=2000)
        assert not loader.import_log and loader.read_bytes(src,64)==plane
        raw=loader.read_bytes(dst,16);expected.append(raw);encoded.append(coord+plane)
    assert expected[0]==struct.pack('<4f',.25,.5,.75,1.)
    public.initial.ROOT=MAIN;public.initial.AEX=aex
    hp=out/'sampler.cpp';hp.write_text(HARNESS);public.initial.HARNESS=hp
    source=public.SOURCE.read_text();report=dict(aex_sha256=sha(aex.read_bytes()),source_sha256=sha(source.encode()),rows=[])
    outputs={}
    for name in ['production','nonfinite-zero-taps','nonfinite-cancelled-rgb','nonfinite-x86-generated']:
        code=candidate_source(name,source)
        binary=public.build(out/name,code,sanitize=True)
        run=subprocess.run([str(binary)],input=b''.join(encoded),capture_output=True,check=True)
        assert not run.stderr and len(run.stdout)==48
        outputs[name]=run.stdout
        shutil.rmtree(out/name)
    for i,(name,coords,values) in enumerate(cases):
        report['rows'].append(dict(name=name,input_hex=encoded[i].hex(),original_hex=expected[i].hex(),
            candidates={n:dict(raw_hex=raw[i*16:i*16+16].hex(),diff=raw_diff(expected[i],raw[i*16:i*16+16],32)) for n,raw in outputs.items()}))
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('SOURCE_SAMPLER',[(r['name'],{k:v['diff']['different_words'] for k,v in r['candidates'].items()}) for r in report['rows']],flush=True)

if __name__=='__main__':main()
