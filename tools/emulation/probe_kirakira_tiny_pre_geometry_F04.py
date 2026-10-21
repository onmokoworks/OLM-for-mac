#!/usr/bin/env python3
"""Trace the original KiraKira pre-render owner with host checkout callbacks.

No numerical detours or worker rebuild. Offsets are grounded in disassembly of
18114c8c0 / 181151710. Full renders are independently exercised by the F04 fuzzer.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

sys.dont_write_bytecode = True
from aex_loader import AexLoader
from aex_witness import leaf_check
from unicorn.x86_const import UC_X86_REG_RSP


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--aex', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    loader = AexLoader(str(args.aex), verbose=False, fast=True)
    # A known scalar address leaf checks all four integer argument positions.
    world, address = loader.host_alloc(128), loader.host_alloc(8)
    loader.write_bytes(world + 0x18, struct.pack('<Qi', 0x12340000, 19))
    leaf_check(loader, 0x1812309f0, [world, 2, 3, address])
    assert struct.unpack('<Q', loader.read_bytes(address, 8))[0] == 0x12340000 + 3*19 + 2*4

    in_data = loader.host_alloc(512)
    pre_input, pre_output = loader.host_alloc(128), loader.host_alloc(128)
    callbacks, extra = loader.host_alloc(8), loader.host_alloc(24)
    loader.write_bytes(extra, struct.pack('<QQQ', pre_input, pre_output, callbacks))
    loader.write_bytes(in_data + 0xb8, struct.pack('<Q', 0x12345678))
    loader.write_bytes(in_data + 0xe0, struct.pack('<ii', 0, 1))
    loader.write_bytes(in_data + 0xf0, struct.pack('<i', 24))
    captures = []

    def checkout(ld, regs):
        # Win64 stack args 5..8: time, step, scale, result*. The originals
        # are copied by the binary, not synthesized by this callback.
        rsp = ld.uc.reg_read(UC_X86_REG_RSP)
        time, step, scale, result = struct.unpack('<4Q', ld.read_bytes(rsp + 0x28, 32))
        rect = list(struct.unpack('<4i', ld.read_bytes(regs[3], 16)))
        request = ld.read_bytes(regs[3], 44)
        assert regs[:3] == [0x12345678, 0, 0]
        assert (time & 0xffffffff, step & 0xffffffff, scale & 0xffffffff) == (0, 1, 24)
        # Full storage and content are the same in this bounded host probe.
        ld.write_bytes(result, struct.pack('<4i', *rect)*2 + bytes(48))
        ld.write_bytes(result + 0x20, struct.pack('<ii', 1, 1))
        ld.write_bytes(result + 0x2c, struct.pack('<ii', rect[2], rect[3]))
        captures.append(dict(request=rect, request_hex=request.hex(),
                             time=[time & 0xffffffff, step & 0xffffffff, scale & 0xffffffff]))
        return 0

    callback = loader.install_callback('F04 checkout_layer', checkout)
    loader.write_bytes(callbacks, struct.pack('<Q', callback))
    rows = []
    for w, h in ((1,1), (1,9), (9,1), (3,3), (4,5), (5,3), (8,7), (9,6), (9,7), (32,18)):
        for depth in (8,16,32):
            loader.write_bytes(pre_input, bytes(128))
            loader.write_bytes(pre_output, bytes(128))
            loader.write_bytes(pre_input, struct.pack('<4i', 0,0,w,h))
            loader.write_bytes(pre_input + 0x2c, struct.pack('<h', depth))
            requested = loader.read_bytes(pre_input,44)
            old_count = len(captures)
            loader.call_function(0x18114c8c0, int_args=[0,in_data,0,extra], max_instructions=10000)
            assert len(captures) == old_count + 1
            assert bytes.fromhex(captures[-1]['request_hex']) == requested
            result = list(struct.unpack('<4i',loader.read_bytes(pre_output,16)))
            maximum = list(struct.unpack('<4i',loader.read_bytes(pre_output+16,16)))
            assert result == maximum == [0,0,w,h]
            flag = struct.unpack('<H',loader.read_bytes(pre_output+0x22,2))[0]
            assert flag == 1
            rows.append(dict(geometry=[w,h],depth=depth,checkout=captures[-1],
                             result_rect=result,max_result_rect=maximum,flags=flag))
    report = dict(schema='olm-kira-F04-pre-geometry/1',
        aex_sha256=hashlib.sha256(args.aex.read_bytes()).hexdigest(),
        entry='0x18114c8c0', helper='0x181151710', rows=rows,
        limitation='Host callback supplies full content; not a native AE or numerical render test. No ROI/downsample claim.')
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(f'{len(rows)} original AEX pre-render owners: request bytes preserved; result/max rects equal checkout')


if __name__ == '__main__':
    main()
