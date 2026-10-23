#!/usr/bin/env python3
"""Observe original IPP dispatch on both sides of the small-image boundary."""
import argparse
from collections import Counter
import json
from pathlib import Path
import struct
import sys
sys.dont_write_bytecode = True
from aex_loader import AexLoader

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/fuzz'))
from run import main_checkout
from core import sha


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--report', type=Path, required=True)
    args = p.parse_args()
    assert args.report.resolve().is_relative_to(ROOT/'orchestra/state')
    aex = main_checkout()/'plugins_2025/DistanceGradation.aex'
    report = dict(aex_sha256=sha(aex.read_bytes()), rows=[])
    try:
        for r in (3, 4, 7):
            for w, h in ((1, 2*r+3), (2*r+3, 1), (2*r, 2*r+1),
                         (2*r+1, 2*r), (2*r+1, 2*r+1), (2*r+2, 2*r+2)):
                ld = AexLoader(str(aex), verbose=False, fast=True)
                dispatch = Counter()
                for address in (0x1806be1e0, 0x1806b7d40):
                    ld.add_code_hook(address, lambda loader, rip, size: dispatch.update([hex(rip)]))
                data = b''.join(struct.pack('<f', ((i*17)%31)/31) for i in range(w*h))
                src = ld.bump_alloc(len(data), align=64)
                dst = ld.bump_alloc(len(data), align=64)
                ld.write_bytes(src, data)
                spec = ld.bump_alloc(1024*1024, align=64)
                scratch = ld.bump_alloc(8*1024*1024, align=64)
                init = ld.call_function(0x18000c280, [100,w|(h<<32),r,13,1,2,0x3f800000,0x3f800000,spec])
                result = ld.call_function(0x18000c2f0, [src,w*4,dst,w*4,w|(h<<32),1,0,spec,scratch], max_instructions=200_000_000)
                assert init['rax'] == result['rax'] == 0 and not ld.import_log
                row = dict(radius=r, geometry=[w,h], dispatch=dict(dispatch), imports=[],
                           input_sha256=sha(data), output_sha256=sha(ld.read_bytes(dst,len(data))))
                report['rows'].append(row)
                print(row, flush=True)
    finally:
        args.report.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')


if __name__ == '__main__':
    main()
