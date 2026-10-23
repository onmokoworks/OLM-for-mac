#!/usr/bin/env python3
"""Original import-free Kira clamp: preserve input NaN bits and record instructions."""

from pathlib import Path as _HarnessPath
_UCRT_CXX = str(_HarnessPath(__file__).resolve().parents[2] / "tools/ucrt_cxx.py")
import argparse
import hashlib
import json
from pathlib import Path
import struct
import os
import subprocess
import tempfile
from aex_loader import AexLoader
from capstone import Cs, CS_ARCH_X86, CS_MODE_64


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--aex', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--scratch', type=Path, required=True)
    p.add_argument('--header', type=Path, default=Path(__file__).resolve().parents[2] / 'core/kirakira_merge2.h')
    p.add_argument('--require-exact', action='store_true')
    args = p.parse_args()
    args.scratch = args.scratch.resolve()
    assert args.scratch.is_relative_to(Path(__file__).resolve().parents[2] / 'orchestra/state')
    args.scratch.mkdir(parents=True, exist_ok=True)
    os.environ.update(TMPDIR=str(args.scratch), TMP=str(args.scratch), TEMP=str(args.scratch))
    loader = AexLoader(str(args.aex), verbose=False, fast=False)
    address = 0x181156740
    instructions = []
    for instruction in Cs(CS_ARCH_X86, CS_MODE_64).disasm(loader.read_bytes(address, 64), address):
        instructions.append(dict(address=hex(instruction.address), bytes=instruction.bytes.hex(),
                                 operation=instruction.mnemonic, operands=instruction.op_str))
        if instruction.mnemonic == 'ret': break
    words = (0, 0x80000000, 1, 0x80000001, 0x3f000000, 0x3f800000,
             0x3f800001, 0xbf800000, 0x7f7fffff, 0xff7fffff,
             0x7f800000, 0xff800000, 0x7fc00000, 0xffc00000,
             0x7fc12345, 0xffc12346, 0x7f812345, 0xff812346)
    rows = []
    for word in words:
        result = loader.call_function(address, float_args={0: struct.pack('<I', word)}, max_instructions=100)
        rows.append(dict(input=f'{word:08x}', output=f"{int.from_bytes(result['xmm0'][:4], 'little'):08x}"))
    with tempfile.TemporaryDirectory(dir=args.scratch) as directory:
        directory = Path(directory)
        source = directory / 'clamp.cpp'
        source.write_text('#include "' + str(args.header.resolve()) + '"\n' + r"""
#include <cstdio>
int main() {
    unsigned word;
    while (std::fread(&word, 4, 1, stdin) == 1) {
        float value;
        std::memcpy(&value, &word, 4);
        value = olm::kirakira::clamp_merge2_channel(value);
        std::memcpy(&word, &value, 4);
        std::fwrite(&word, 4, 1, stdout);
    }
}
""")
        binary = directory / 'clamp'
        subprocess.run([_UCRT_CXX, '-std=c++20', '-O2', '-fno-fast-math', '-ffp-contract=off',
                        '-fsanitize=address,undefined', str(source), '-o', str(binary)],
                       capture_output=True, check=True)
        result = subprocess.run([str(binary)], input=b''.join(struct.pack('<I', w) for w in words),
                                capture_output=True, check=True)
        assert len(result.stdout) == len(words) * 4
        for row, (word,) in zip(rows, struct.iter_unpack('<I', result.stdout)):
            row['mac'] = f'{word:08x}'
            row['exact'] = row['output'] == row['mac']
    report = dict(aex_sha256=hashlib.sha256(args.aex.read_bytes()).hexdigest(),
        header_sha256=hashlib.sha256(args.header.read_bytes()).hexdigest(),
        instructions=instructions, rows=rows, exact=sum(r['exact'] for r in rows))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    print('clamp', report['exact'], '/', len(rows), 'exact')
    if args.require_exact: assert report['exact'] == len(rows)


if __name__ == '__main__': main()
