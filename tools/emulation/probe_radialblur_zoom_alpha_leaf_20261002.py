#!/usr/bin/env python3
"""Import-free original Zoom 9d80 ABI and real SDK nonzero-alpha boundaries."""
import argparse
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile

from aex_loader import AexLoader
import probe_radialblur_zoom_alpha_20261002 as zoom
public=zoom.public
HARNESS=public.ROOT/'tools/emulation/radialblur_zoom_alpha_sdk_harness_20261002.cpp'
ENV=dict(os.environ,ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')


def boundary_bits():
    bits={0,0x80000000,0x3f800000,0xbf800000,0x00800000,0x80800000}
    for value in [1e-8,1e-12,1e-20,2**-24,2**-46]:
        b=struct.unpack('<I',struct.pack('<f',value))[0]
        for n in [b-1,b,b+1]:bits.update([n,n|0x80000000])
    return sorted(bits)


def sampler_cases():
    cases=[]
    for bits in boundary_bits():
        raw=struct.pack('<3fI',.25,.5,.75,bits)*4
        cases.append({'name':'alpha_'+f'{bits:08x}','source_rgba_f32_words':[f'{n:08x}' for n in struct.unpack('<16I',raw)]})
    profiles={
        'alpha_cancellation':[(.25,.5,.75,1),(.5,.75,1,-1),(1,.25,.5,-1),(.75,1,.25,1)],
        'alpha_cancellation_reverse':[(.25,.5,.75,-1),(.5,.75,1,1),(1,.25,.5,1),(.75,1,.25,-1)],
        'negative_zero_rgb_positive_alpha':[(-0.,-0.,-0.,1)]*4,
        'positive_zero_rgb_negative_alpha':[(0.,0.,0.,-1)]*4,
        'negative_zero_rgb_negative_alpha':[(-0.,-0.,-0.,-1)]*4,
        'negative_zero_rgb_zero_alpha':[(-0.,-0.,-0.,0.)]*4,
        'unequal_signed_alpha':[(.125,-.25,.5,.75),(-.75,.25,.5,-.125),(.5,.375,-.125,.25),(.875,.25,.5,-.5)],
        'unequal_signed_alpha_small':[(.125,-.25,.5,2**-30),(-.75,.25,.5,-2**-31),(.5,.375,-.125,2**-35),(.875,.25,.5,-2**-32)],
    }
    for name,pixels in profiles.items():
        raw=b''.join(struct.pack('<4f',*pixel) for pixel in pixels)
        cases.append({'name':name,'source_rgba_f32_words':[f'{n:08x}' for n in struct.unpack('<16I',raw)]})
    return cases


def native_rows():
    loader=AexLoader(str(public.initial.AEX),verbose=False,fast=False)
    source=loader.bump_alloc(64);output=loader.bump_alloc(32);rows=[]
    for case in sampler_cases():
        loader.write_bytes(source,struct.pack('<16I',*[int(n,16) for n in case['source_rgba_f32_words']]))
        loader.write_bytes(output,b'\xa5'*32)
        # Original Zoom ABI: 2 radius cells, 2 angular rows, stride 8 float
        # words, followed by FLOAT32 radius .25 and angular .5 stack arguments.
        loader.call_function(loader.image_base+0x9d80,
            int_args=[source,output,2,2,8,0x3e800000,0x3f000000],max_instructions=1000)
        assert not loader.import_log and loader.read_bytes(output+16,16)==b'\xa5'*16
        raw=loader.read_bytes(output,16)
        rows.append({**case,'native_rgba_f32_words':''.join(f'{n:08x}' for n in struct.unpack('<4I',raw)),
                     'output_tail_guard_intact':True,'import_calls':0})
    return rows


def sdk_replay(directory,source,rows):
    previous=public.initial.HARNESS
    try:
        public.initial.HARNESS=HARNESS
        for sanitize in [False,True]:
            binary=public.build(directory/('san' if sanitize else 'o2'),source,sanitize)
            run=subprocess.run([str(binary)],input=''.join(' '.join(r['source_rgba_f32_words'])+'\n' for r in rows),capture_output=True,text=True,check=True,env=ENV)
            assert run.stderr=='' and run.stdout.splitlines()==[r['native_rgba_f32_words'] for r in rows]
    finally:public.initial.HARNESS=previous
    return 2*len(rows)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--report',type=Path,required=True);args=ap.parse_args()
    source=public.SOURCE.read_text();rows=native_rows()
    with tempfile.TemporaryDirectory(prefix='radial_zoom_alpha_leaf_') as name:count=sdk_replay(Path(name),source,rows)
    assert public.SOURCE.read_text()==source
    import pefile
    pe=pefile.PE(str(public.initial.AEX))
    report={'schema':'radialblur.zoom-nonzero-alpha-leaf/1','source_sha256':public.sha(source.encode()),
            'header_sha256':public.sha(public.SOURCE.with_suffix('.h').read_bytes()),'aex_sha256':public.sha(public.initial.AEX.read_bytes()),
            'summary':{'finite_alpha_boundaries':len(boundary_bits()),'finite_sampler_cases':len(rows),'native_import_free_calls':len(rows),'typed_sdk_replays':count},'rows':rows,
            'original_sampler_rva':'0x9d80','zero_compare_code_sha256':public.sha(pe.get_data(0x9f67,0x31)),
            'original_sampler_code_sha256':public.sha(pe.get_data(0x9d80,0x231)),
            'abi':'RCX RGBA source, RDX RGBA output, R8 radius width=2, R9 angular height=2, stack5 float-word row stride=8, stack6/7 FLOAT32 .25/.5 bits.',
            'dependencies_sha256':{str(p.relative_to(public.ROOT)):public.sha(p.read_bytes()) for p in [Path(__file__),Path(zoom.__file__),HARNESS]},
            'claims_not_made':['Finite arguments are not NaN/unordered/denormal control, native ISA or arbitrary-input/all-ten completion.']}
    args.report.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');print('ZOOM_ALPHA_LEAF',report['summary'],flush=True)


if __name__=='__main__':main()
