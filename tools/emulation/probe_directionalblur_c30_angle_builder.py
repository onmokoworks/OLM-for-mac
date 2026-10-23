#!/usr/bin/env python3
"""Execute the original angle-builder SSE slice for every signed-short angle.

This checks the scalar conversion boundary, not native AE or trig imports.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct

from aex_loader import AexLoader
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from unicorn.x86_const import UC_X86_REG_XMM0


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--aex', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    args = p.parse_args()
    loader = AexLoader(str(args.aex), verbose=False)
    begin, end = 0x180006cfd, 0x180006d24
    code = loader.read_bytes(begin, end-begin)
    constants = {}
    for address in (0x18000b360, 0x18000b370, 0x18000b378):
        raw = loader.read_bytes(address, 8)
        constants[hex(address)] = {'hex': raw.hex(), 'binary64': struct.unpack('<d', raw)[0]}
    assert constants['0x18000b360']['hex'] == 'f1d4c853fb210940'
    old_mismatches, mismatches = [], []
    digest = hashlib.sha256()
    for angle in range(-32768, 32768):
        loader.uc.reg_write(UC_X86_REG_XMM0, int.from_bytes(struct.pack('<f', angle), 'little'))
        loader.uc.emu_start(begin, end, count=7)
        actual = (loader.uc.reg_read(UC_X86_REG_XMM0) & 0xffffffff).to_bytes(4, 'little')
        digest.update(actual)
        old = struct.pack('<f', ((float(angle)+90.0)/180.0)*math.pi)
        candidate = struct.pack('<f', ((float(angle)+90.0)/180.0)*3.14159265)
        if actual != old:
            old_mismatches.append({'angle': angle, 'aex': actual.hex(), 'old': old.hex()})
        if actual != candidate:
            mismatches.append({'angle': angle, 'aex': actual.hex(), 'candidate': candidate.hex()})
    report = {'scope': __doc__, 'aex_sha256': hashlib.sha256(args.aex.read_bytes()).hexdigest(),
        'constants': constants, 'instruction_sha256': hashlib.sha256(code).hexdigest(),
        'instructions': [{'address': hex(i.address), 'bytes': i.bytes.hex(),
                          'mnemonic': i.mnemonic, 'operands': i.op_str}
                         for i in Cs(CS_ARCH_X86, CS_MODE_64).disasm(code, begin)],
        'cases': 65536, 'original_output_sha256': digest.hexdigest(),
        'old_mismatches': old_mismatches, 'candidate_mismatches': mismatches}
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    assert not mismatches
    print('PASS', report['cases'], 'old mismatches', len(old_mismatches), flush=True)


if __name__ == '__main__':
    main()
