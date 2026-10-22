#!/usr/bin/env python3
"""Bind the C11 first differing Gaussian word to the pinned worker's expf import.

This diagnoses an external reference boundary; it does not change either renderer.
Run after trace_radialblur_smart_C06.py on fixtures/radialblur_exp_C11.json.
"""
import argparse
import ctypes
import hashlib
import json
import math
from pathlib import Path
import struct

import capstone
import pefile


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--trace', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    root = Path(__file__).resolve().parents[2]
    assert args.output.resolve().is_relative_to(root/'orchestra/state/C11-radial-smart-r2')
    trace = json.loads(args.trace.read_text())
    weights = trace['rows'][0]['weights']
    assert weights['different_words'] == 1
    difference = weights['first_differences'][0]
    length, index = weights['word_count'], difference['word']
    f32 = lambda v: struct.unpack('<f', struct.pack('<f', v))[0]
    bits = lambda v: struct.pack('<f', v).hex()
    denominator = f32(f32(float(length)*length) * f32(0.111111119389534))
    denominator = f32(f32(denominator + denominator) + 1.e-5)
    exponent = f32(float(-index*index)*f32(1./denominator))
    host = ctypes.CDLL(None).expf
    host.argtypes, host.restype = [ctypes.c_float], ctypes.c_float
    host_hex = bits(host(exponent))
    double_hex = bits(math.exp(exponent))
    assert host_hex == difference['native_f32_le_hex']
    assert double_hex == difference['mac_f32_le_hex']
    assert host_hex != double_hex
    worker = Path(trace['provenance']['worker_path'])
    worker_root = worker.parents[2]
    imports = worker_root/'crates/aex-guest-worker/src/x64/imports.rs'
    source = imports.read_text()
    marker = 'install_float_import(unicorn, stub, "expf", f32::exp)?;'
    assert marker in source
    aex = Path(trace['provenance']['aex_path'])
    pe = pefile.PE(str(aex))
    decoder = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    base = pe.OPTIONAL_HEADER.ImageBase
    static = {}
    for label, start, end in [('weight_builder', 0xb680, 0xb7b5), ('expf_thunk', 0x1f574, 0x1f57a)]:
        static[label] = [dict(rva=hex(i.address-base), bytes=i.bytes.hex(),
                              instruction=i.mnemonic+' '+i.op_str)
                         for i in decoder.disasm(pe.get_data(start,end-start),base+start)]
    bindings = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in (args.trace, worker, imports, aex)}
    result = dict(length=length, index=index, denominator=denominator, exponent=exponent,
                  exponent_le_hex=bits(exponent), host_expf_le_hex=host_hex,
                  double_exp_cast_le_hex=double_hex, worker_import=marker,
                  bindings=bindings, static=static,
                  conclusion='Pinned worker tail expf agrees with host expf; Mac agrees with double-exp cast. Native Windows UCRT equivalence is not inferred.')
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print('EXP_BOUNDARY', index, host_hex, double_hex)


if __name__ == '__main__':
    main()
