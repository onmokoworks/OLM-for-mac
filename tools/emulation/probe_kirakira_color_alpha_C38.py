#!/usr/bin/env python3
"""Import-free original color aggregator witnesses for ordered alpha admission."""
import argparse
import hashlib
import json
import struct
from pathlib import Path

from aex_loader import AexLoader
from capstone import Cs, CS_ARCH_X86, CS_MODE_64


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--aex', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    loader = AexLoader(str(args.aex), verbose=False, fast=False)

    def alloc(data):
        address = loader.host_alloc(len(data))
        loader.write_bytes(address, data)
        return address

    # FUN_18114f020's Win64 ABI: this, rays, colors, flags, ramps, normalizers,
    # output, width, height, gain. Colors/flags/ramps are unused by this owner.
    ray = alloc(bytes(16))
    zero = alloc(bytes(16))
    rays = alloc(struct.pack('<5Q', ray, zero, zero, zero, zero))
    norms = alloc(bytes(20))
    output = alloc(bytes(16))
    threshold = struct.unpack('<I', struct.pack('<f', 0.001))[0]
    words = (0, 0x80000000, 1, 0x80000001, threshold-1, threshold, threshold+1,
             0x3f000000, 0x3f800000, 0xbf800000, 0x7f7fffff, 0xff7fffff,
             0x7f800000, 0xff800000, 0x7fc00000, 0xffc00000,
             0x7fc12345, 0xffc12346, 0x7f812345, 0xff812346)
    rows = []
    for word in words:
        loader.write_bytes(ray, struct.pack('<3fI', 0.25, 0.5, 0.75, word))
        loader.write_bytes(norms, struct.pack('<5f', 1, 1, 1, 1, 1))
        loader.write_bytes(output, bytes.fromhex('deadbeef') * 4)
        loader.call_function(0x18114f020,
            int_args=[0, rays, 0, 0, 0, norms, output, 1, 1, 0x3f800000],
            max_instructions=2000)
        raw = loader.read_bytes(output, 16)
        value = struct.unpack('<f', struct.pack('<I', word))[0]
        skipped = not (value > 0.001)
        if skipped:
            assert raw == bytes(16), (hex(word), raw.hex())
        if word == 0x3f800000:
            assert raw == struct.pack('<4f', 0.25, 0.5, 0.75, 1)
        rows.append(dict(alpha_bits=f'{word:08x}', output_rgba_hex=raw.hex(),
                         ordered_threshold_skips=skipped))
    instructions = [dict(address=hex(i.address), operation=i.mnemonic,
                         operands=i.op_str, bytes=i.bytes.hex())
                    for i in Cs(CS_ARCH_X86, CS_MODE_64).disasm(
                        loader.read_bytes(0x18114f14a, 14), 0x18114f14a)]
    assert instructions[-1]['operation'] == 'jbe'
    report = dict(aex_sha256=hashlib.sha256(args.aex.read_bytes()).hexdigest(),
                  instructions=instructions, rows=rows, count=len(rows))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    print('PASS', len(rows), 'original alpha witnesses')


if __name__ == '__main__':
    main()
