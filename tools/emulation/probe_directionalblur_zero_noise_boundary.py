#!/usr/bin/env python3
"""F05 case 127: stop the original AEX before its first invalid table read.

Adapted from probe_directionalblur_native_noise_bounds_20261001.witness, with
the case's actual Thickness and padded work geometry, not its source geometry.
"""
import argparse
import json
from pathlib import Path
import struct

from aex_loader import AexLoader
from aex_witness import leaf_check
import probe_directionalblur_fixed_getter_20261001 as fixed
from unicorn.x86_const import UC_X86_REG_RAX, UC_X86_REG_RCX

ROOT = Path(__file__).resolve().parents[2]
MAIN = ROOT.parent.parent if ROOT.parent.name == 'worktrees' else ROOT


def witness():
    fixed.owner.AEX = MAIN/'plugins_2025/OLMDirectionalBlur.aex'
    offset, seed, thickness = -399.5963134765625, 518, 10.0
    width, height = 65, 65
    builder = fixed.build_native(19, offset)
    loader = AexLoader(str(fixed.owner.AEX), verbose=False, fast=False)
    loader.register_libm_impls()
    # Transparent prepass is import-free and writes through arguments 5/6,
    # so it checks the Win64 stack argument ABI before the generator witness.
    source, destination, denominator, valid = [loader.host_alloc(16) for _ in range(4)]
    loader.write_bytes(source,bytes(16))
    for pointer in (destination,denominator,valid):
        loader.write_bytes(pointer,b'\xa5'*16)
    leaf = leaf_check(loader,0x180001000,
                     [0,0,source,destination,denominator,valid,0,0,0,0,1,0])
    assert loader.read_bytes(destination,16)==bytes(16)
    assert loader.read_bytes(denominator,16)==bytes(4)+b'\xa5'*12
    assert loader.read_bytes(valid,16)==bytes(4)+b'\xa5'*12
    allocations, reads, outside = [], [], []

    def allocate(ld, args):
        count = args[0]
        storage = ld.host_alloc(count+4096)
        pointer = storage+2048
        ld.write_bytes(storage, b'\xa5'*(count+4096))
        allocations.append((pointer,count))
        return pointer

    suite = loader.host_alloc(32)
    callbacks = [loader.install_callback('memory.allocate',allocate),
                 loader.install_callback('memory.lock',lambda ld,a:a[0]),
                 loader.install_callback('memory.unlock',lambda ld,a:0),
                 loader.install_callback('memory.dispose',lambda ld,a:0)]
    loader.write_bytes(suite,struct.pack('<4Q',*callbacks))

    def acquire(ld,args):
        assert ld.read_bytes(args[0],64).split(b'\0',1)[0] == b'PF Handle Suite'
        assert args[1] == 2
        ld.write_bytes(args[2],struct.pack('<Q',suite))
        return 0

    basic = loader.host_alloc(32)
    loader.write_bytes(basic,struct.pack('<4Q',loader.install_callback('suite.acquire',acquire),
                      loader.install_callback('suite.release',lambda ld,a:0),0,0))
    in_data = loader.host_alloc(0x200)
    loader.write_bytes(in_data,bytes(0x200))
    loader.write_bytes(in_data+0x180,struct.pack('<Q',basic))
    context = loader.host_alloc(0x48)
    loader.write_bytes(context,bytes(0x48))

    def watch(ld,address,size):
        pointer,count = allocations[1]
        assert ld.uc.reg_read(UC_X86_REG_RAX) == pointer
        index = ld.uc.reg_read(UC_X86_REG_RCX)
        if index >= 1<<63:
            index -= 1<<64
        byte_offset = index*4+(4 if address==0x1800037f8 else 0)
        reads.append(byte_offset)
        if byte_offset < 0 or byte_offset+4 > count:
            outside.append(dict(instruction_rva=hex(address-0x180000000),
                                signed_index=index,byte_offset=byte_offset,allocation_size=count))
            ld.uc.emu_stop()

    for address in (0x1800037f3,0x1800037f8):
        loader.add_code_hook(address,watch)
    thickness_bits = struct.unpack('<I',struct.pack('<f',thickness))[0]
    result = loader.call_function(0x1800034e0,
        int_args=[context,in_data,width,height,thickness_bits,builder['normalized_bits'],seed],
        max_instructions=2000000)
    assert len(allocations)==2 and allocations[1][1]==404 and len(outside)==1
    return dict(schema='directionalblur.zero-noise-boundary/1',index=127,
        aex_sha256=fixed.sha(fixed.owner.AEX.read_bytes()),
        loader_sha256=fixed.sha((ROOT/'tools/emulation/aex_loader.py').read_bytes()),
        source_geometry=[3,61],work_geometry=[width,height],offset=offset,seed=seed,
        thickness=thickness,builder=builder,allocation_sizes=[n for _,n in allocations],
        abi_leaf=dict(rva='0x1000',transparent_prepass_exact=True,instructions=leaf['instructions']),
        table_read_count=len(reads),first_invalid_read=outside[0],
        instructions=result['instructions'],stopped_before_invalid_read=True,
        math_boundary='Host powf substitute; the signed index is computed before powf and is independent of its result.',
        inference='The completed session oracle for this input consumes allocator-adjacent memory outside the AEX-owned table. Its final hash is not a portable noise-generator contract.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    report = witness()
    args.output.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    print(json.dumps(report['first_invalid_read'],sort_keys=True))
