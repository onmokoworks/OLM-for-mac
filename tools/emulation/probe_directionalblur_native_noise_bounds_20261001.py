#!/usr/bin/env python3
"""Observe actual AEX noise-table allocation bounds before each indexed read."""
import argparse,json,struct
from pathlib import Path
from aex_loader import AexLoader
from unicorn.x86_const import UC_X86_REG_RAX,UC_X86_REG_RCX
import probe_directionalblur_fixed_getter_20261001 as fixed
ROOT=fixed.ROOT
sha=fixed.sha

def witness(offset,seed,width,height):
    normalized=fixed.build_native(19,offset)['normalized_bits']
    loader=AexLoader(str(fixed.owner.AEX),verbose=False,fast=False)
    loader.register_libm_impls()
    allocations=[];suite_calls=[];observed=[];outside=[]
    def allocate(ld,args):
        count=args[0];storage=ld.host_alloc(count+4096);pointer=storage+2048
        ld.write_bytes(storage,b'\xa5'*(count+4096));allocations.append((pointer,count));return pointer
    suite=loader.host_alloc(32)
    callbacks=[loader.install_callback('memory.allocate',allocate),loader.install_callback('memory.lock',lambda ld,a:a[0]),loader.install_callback('memory.unlock',lambda ld,a:0),loader.install_callback('memory.dispose',lambda ld,a:0)]
    loader.write_bytes(suite,struct.pack('<4Q',*callbacks))
    def acquire(ld,args):
        name=ld.read_bytes(args[0],64).split(b'\0',1)[0].decode();suite_calls.append({'name':name,'version':args[1]})
        if name!='PF Handle Suite' or args[1]!=2:raise RuntimeError('unexpected host suite')
        ld.write_bytes(args[2],struct.pack('<Q',suite));return 0
    basic=loader.host_alloc(32)
    loader.write_bytes(basic,struct.pack('<4Q',loader.install_callback('suite.acquire',acquire),loader.install_callback('suite.release',lambda ld,a:0),0,0))
    in_data=loader.host_alloc(0x200);loader.write_bytes(in_data,bytes(0x200));loader.write_bytes(in_data+0x180,struct.pack('<Q',basic))
    context=loader.host_alloc(0x48);loader.write_bytes(context,bytes(0x48))
    def watch(ld,address,size):
        pointer,count=allocations[1]
        base=ld.uc.reg_read(UC_X86_REG_RAX)
        index=ld.uc.reg_read(UC_X86_REG_RCX);index=index if index<1<<63 else index-(1<<64)
        byte_offset=index*4+(4 if address==0x1800037f8 else 0)
        if base!=pointer:raise RuntimeError('indexed read base differs from allocated table')
        observed.append(byte_offset)
        if byte_offset<0 or byte_offset+4>count:
            outside.append({'instruction_rva':hex(address-0x180000000),'signed_base_index':index,'byte_offset':byte_offset,'read_size':4,'allocation_size':count})
            ld.uc.emu_stop() # Observe before reading arbitrary allocator contents.
    for address in (0x1800037f3,0x1800037f8):loader.add_code_hook(address,watch)
    bits=lambda value:struct.unpack('<I',struct.pack('<f',value))[0]
    result=loader.call_function(0x1800034e0,int_args=[context,in_data,width,height,bits(3),normalized,seed],max_instructions=2000000)
    imports=sorted({c.name for c in loader.import_log})
    if imports!=['memset','powf']:raise RuntimeError('unexpected imports')
    if len(allocations)!=2 or allocations[1][1]!=404:raise RuntimeError('allocation contract changed')
    if not outside and (result['rax']!=0 or len(observed)!=2*(width//3+3)*(height//3+3)):raise RuntimeError('generator did not finish')
    return {'offset':offset,'seed':seed,'work_geometry':[width,height],'offset_normalized_bits':normalized,'allocation_sizes':[n for _,n in allocations],'table_read_count':len(observed),'minimum_read_offset':min(observed),'maximum_read_offset':max(observed),'out_of_bounds':bool(outside),'first_out_of_bounds':outside[0] if outside else None,'completed':not outside,'executed_imports':imports,'suite_requests':suite_calls,'instructions_executed':result['instructions']}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    cases=[witness(offset,seed,w,h) for w,h in ((15,15),(51,51)) for seed in (1,7,1000) for offset in (-32768,-720,-36,-35,-18,32767)]
    r={'schema':'directionalblur.native-noise-bounds/1','aex_sha256':sha(fixed.owner.AEX.read_bytes()),'probe_sha256':sha(Path(__file__).read_bytes()),'loader_sha256':sha((ROOT/'tools/emulation/aex_loader.py').read_bytes()),'fixed_builder_probe_sha256':sha(Path(fixed.__file__).read_bytes()),'generator_rva':'0x34e0','read_rvas':['0x37f3','0x37f8'],'case_count':len(cases),'out_of_bounds_count':sum(c['out_of_bounds'] for c in cases),'cases':cases,'scope':'Actual builder Offset and unchanged AEX generator; mocked host handle allocation/lock/acquire/release; stop immediately before invalid read','math_boundary':'powf uses registered host math, not native UCRT; index arithmetic does not depend on its return value','claims_not_made':['No Windows AE/native allocator output claim','No numeric output equivalence after invalid read','No source recovery or full compatibility completion']}
    assert r['out_of_bounds_count']==12
    args.output.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print('NATIVE OUT OF BOUNDS',r['out_of_bounds_count'],'/',len(cases))
if __name__=='__main__':main()
