#!/usr/bin/env python3
"""Execute original83ed-8429 PF32 gain/MINSS/17490 block and actual SDK trait."""
import argparse
import json
from pathlib import Path
import struct
import subprocess
import tempfile

from aex_loader import AexLoader
from unicorn.x86_const import UC_X86_REG_XMM6,UC_X86_REG_XMM7,UC_X86_REG_XMM8,UC_X86_REG_XMM9,UC_X86_REG_XMM10,UC_X86_REG_XMM11
import probe_radialblur_size_topology_20261002 as topology
public=topology.public
HARNESS=public.ROOT/'tools/emulation/radialblur_zoom_float_writer_sdk_harness_20261002.cpp'


def native_rows():
    words=[0,0x80000000,0x3f7fffff,0x3f800000,0x3f800001,0xbf800000,0x40000000,0xc0000000,0x7f7fffff,0xff7fffff,0x00800000,0x80800000,1,0x80000001,0x7f800000,0xff800000,0x7fc00000,0xffc00000]
    loader=AexLoader(str(public.initial.AEX),verbose=False,fast=False);output=loader.bump_alloc(32)
    loader.add_code_hook(loader.image_base+0x8429,lambda ld,_address,_size:ld.uc.emu_stop());rows=[]
    for word in words:
        loader.write_bytes(output,b'\xa5'*32)
        for reg,bits in [(UC_X86_REG_XMM6,0x3f800000),(UC_X86_REG_XMM7,0xbe000000),(UC_X86_REG_XMM8,word),(UC_X86_REG_XMM9,0x3e800000),(UC_X86_REG_XMM10,word),(UC_X86_REG_XMM11,0x3f800000)]:loader.uc.reg_write(reg,bits)
        # Enter the actual common caller block before gain/MINSS. Its saved
        # output pointer is [rsp+40h]; actual17490 gets it at stack5.
        loader.call_function(loader.image_base+0x83ed,int_args=[0,0,0,0,0,0,0,output],max_instructions=100)
        assert not loader.import_log and loader.read_bytes(output+16,16)==b'\xa5'*16
        rows.append({'input_word':f'{word:08x}','native_argb_f32_words':''.join(f'{n:08x}' for n in struct.unpack('<4I',loader.read_bytes(output,16))),'output_tail_guard_intact':True,'import_calls':0})
    return rows


def sdk_replay(directory,source,rows):
    previous=public.initial.HARNESS
    try:
        public.initial.HARNESS=HARNESS
        for sanitize in [False,True]:
            binary=public.build(directory/('san' if sanitize else 'o2'),source,sanitize)
            run=subprocess.run([str(binary)],input=''.join(r['input_word']+'\n' for r in rows),capture_output=True,text=True,check=True,env=topology.ENV)
            assert run.stderr=='' and run.stdout.splitlines()==[r['native_argb_f32_words'] for r in rows]
    finally:public.initial.HARNESS=previous
    return 2*len(rows)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--report',type=Path,required=True);args=ap.parse_args()
    source=topology.candidate_source(topology.before_source());rows=native_rows()
    with tempfile.TemporaryDirectory(prefix='radial_zoom_float_writer_') as name:count=sdk_replay(Path(name),source,rows)
    import pefile
    pe=pefile.PE(str(public.initial.AEX))
    report={'schema':'radialblur.zoom-float-writer/1','source_sha256':public.sha(source.encode()),'header_sha256':public.sha(public.SOURCE.with_suffix('.h').read_bytes()),'aex_sha256':public.sha(public.initial.AEX.read_bytes()),'summary':{'native_caller_block_cases':len(rows),'sdk_trait_replays':count},'rows':rows,'native_code_range':'83ed-8429','native_code_sha256':public.sha(pe.get_data(0x83ed,0x3c)),'abi':'XMM6 gain1, XMM7 alpha-.125, XMM8 blue, XMM9 green.25, XMM10 red, XMM11 bound1; output saved at rsp+40h. Stop at8429 after17490.','dependencies_sha256':{str(p.relative_to(public.ROOT)):public.sha(p.read_bytes()) for p in [Path(__file__),HARNESS,Path(topology.__file__)]},'claims_not_made':['A caller-block test does not prove arbitrary full renders, signaling-NaN exceptions/denormal controls, native Windows CPU/AE or all-ten completion.']}
    args.report.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');print('ZOOM_FLOAT_WRITER',report['summary'],flush=True)


if __name__=='__main__':main()
