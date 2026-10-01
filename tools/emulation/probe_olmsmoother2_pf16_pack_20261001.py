#!/usr/bin/env python3
"""Isolate the actual AEX PF16 MULSS/ADDSS/CVTTSS2SI/store sequence."""
import argparse
import json
import struct
import subprocess
import tempfile
from pathlib import Path

import pefile
from unicorn.x86_const import (UC_X86_REG_XMM1, UC_X86_REG_XMM6, UC_X86_REG_XMM7,
                               UC_X86_REG_XMM8, UC_X86_REG_XMM9, UC_X86_REG_XMM10,
                               UC_X86_REG_RSP, UC_X86_REG_MXCSR)
from aex_loader import AexLoader
import probe_olmsmoother2_key_gamma_hdr_20261001 as campaign

HARNESS = r'''
#include <cstdio>
#include <cstring>
#include "production_under_test.cpp"
int main() {
    unsigned bits[4];
    while (scanf("%x %x %x %x", &bits[0], &bits[1], &bits[2], &bits[3]) == 4) {
        unsigned short values[4];
        for (int i=0; i<4; ++i) {
            float value; memcpy(&value,&bits[i],4); values[i]=clamp16(value);
        }
        const unsigned char *bytes=reinterpret_cast<const unsigned char *>(values);
        for (int i=0; i<8; ++i) printf("%02x",bytes[i]);
        puts("");
    }
}
'''


def specifications():
    # Float32 representation, quantization, signed conversion and modulo limits.
    anchors = [0, 1, 0x80000000, 0x80000001, 0x007fffff, 0x00800000,
               0x3effffff, 0x3f000000, 0x3f000001, 0x3f7fffff, 0x3f800000,
               0x3f800001, 0x3fffffff, 0x40000000, 0x40000001,
               0xbf800000, 0xc0000000, 0x7f7fffff, 0xff7fffff,
               0x7f800000, 0xff800000, 0x7fc00000, 0xffc00000, 0x7f800001]
    for value in (0.5 / 32768, 1.5 / 32768, 32767.5 / 32768, 32768.5 / 32768,
                  65534.5 / 32768, 65535.5 / 32768, 65536.5 / 32768,
                  -0.5 / 32768, -1.5 / 32768, 2.0 ** 48, -(2.0 ** 48)):
        bits = struct.unpack('<I', struct.pack('<f', value))[0]
        anchors.extend((bits - 1, bits, bits + 1))
    state = 0x13579bdf
    for _ in range(512):
        state = (1664525 * state + 1013904223) & 0xffffffff
        anchors.append(state)
    for i, bits in enumerate(dict.fromkeys(anchors)):
        yield {'argb_input_bits': [bits, bits ^ 0x80000000, 0x3f800000, 0x40000000], 'case_index': i}


def native_pack(cases):
    path = campaign.retained.native_identity.AEX_PATH
    assert campaign.sha(path.read_bytes()) == campaign.retained.native_identity.AEX_SHA256
    pe = pefile.PE(str(path))
    assert struct.unpack('<f', pe.get_data(0x22704, 4))[0] == 32768.0
    assert struct.unpack('<f', pe.get_data(0x22694, 4))[0] == 0.5
    loader = AexLoader(str(path), verbose=False, fast=True)
    # Binary signatures bind the isolation to the original instructions.
    assert pe.get_data(0x3c02, 5).hex() == 'f3480f2cc6'
    assert pe.get_data(0x3c0c, 5).hex() == '6689442432'
    outputs = []

    def finished(current, address, size):
        stack = current.uc.reg_read(UC_X86_REG_RSP)
        outputs.append(current.read_bytes(stack + 0x30, 8))
        current.uc.emu_stop()

    loader.add_code_hook(loader.load_base + 0x3c2f, finished)
    mxcsr_initial = loader.uc.reg_read(UC_X86_REG_MXCSR)
    for case in cases:
        a, r, g, b = case['argb_input_bits']
        for register, bits in ((UC_X86_REG_XMM1, a), (UC_X86_REG_XMM6, r),
                               (UC_X86_REG_XMM7, g), (UC_X86_REG_XMM8, b),
                               (UC_X86_REG_XMM9, 0x47000000), (UC_X86_REG_XMM10, 0x3f000000)):
            loader.uc.reg_write(register, bits)
        before = len(outputs)
        loader.call_function(loader.load_base + 0x3bdd, max_instructions=64)
        assert len(outputs) == before + 1 and not loader.import_log
    return outputs, mxcsr_initial, campaign.sha(pe.get_data(0x3bdd, 0x3c2f - 0x3bdd))


def compile_pack(directory, source, sanitize):
    directory.mkdir(parents=True)
    (directory / 'production_under_test.cpp').write_text(source)
    program = directory / 'probe.cpp'; program.write_text(HARNESS)
    binary = directory / 'probe'
    flags = ['-O1', '-g', '-fsanitize=address,undefined', '-fno-omit-frame-pointer'] if sanitize else ['-O2']
    subprocess.run(['clang++', '-std=c++17', *flags, '-fno-fast-math', '-ffp-contract=off',
                    '-Wno-deprecated-declarations', '-I', str(directory),
                    '-I', str(campaign.ROOT / 'cli/OLMSmoother2/shim'), '-I', str(campaign.SOURCE.parent),
                    str(program), '-o', str(binary)], check=True)
    return binary


def mac_pack(binary, cases, env=None):
    payload = ''.join(' '.join(f'{v:08x}' for v in c['argb_input_bits']) + '\n' for c in cases).encode()
    result = subprocess.run([str(binary)], input=payload, capture_output=True, check=True, env=env)
    values = [bytes.fromhex(line) for line in result.stdout.decode().splitlines()]
    assert len(values) == len(cases) and all(len(raw) == 8 for raw in values)
    return values


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, default=campaign.SOURCE)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    cases = list(specifications()); native, mxcsr, instruction_sha = native_pack(cases)
    source = args.source.read_text()
    with tempfile.TemporaryDirectory(prefix='sm2_pack16_') as directory:
        binary = compile_pack(Path(directory) / 'production', source, False)
        current = mac_pack(binary, cases)
    for case, actual, production in zip(cases, native, current):
        case.update(native_raw_sha256=campaign.sha(actual),
                    production_raw_sha256=campaign.sha(production), raw_exact=actual == production)
    deps = [Path(__file__), Path(campaign.__file__), campaign.ROOT / 'tools/emulation/aex_loader.py']
    report = {'schema': 'olmsmoother2.pf16-pack-isolated/1', 'source_sha256': campaign.sha(source.encode()),
              'aex_sha256': campaign.retained.native_identity.AEX_SHA256, 'case_count': len(cases),
              'start_rva': '0x3bdd', 'stop_rva': '0x3c2f', 'instruction_bytes_sha256': instruction_sha,
              'mxcsr_initial': mxcsr, 'summary': {'raw_exact_count': sum(c['raw_exact'] for c in cases)},
              'dependencies_sha256': {str(p.relative_to(campaign.ROOT)): campaign.sha(p.read_bytes()) for p in deps},
              'cases': cases, 'claims_not_made': [
                  'Original AEX writer instruction slice with explicitly authored XMM registers; no render parameter builder or world',
                  'Includes non-finite/negative/out-of-range writer-only diagnostics; not normal UI input or native Windows behavior',
                  'Outputs are isolated pack words, not full-frame output samples',
                  'No native Windows UCRT/AE, arbitrary float environment or full compatibility completion']}
    args.report.write_text(json.dumps(report, sort_keys=True, indent=2) + '\n')
    print('RESULT', len(cases), report['summary'], flush=True)


if __name__ == '__main__':
    main()
