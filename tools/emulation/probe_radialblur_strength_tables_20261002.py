#!/usr/bin/env python3
"""Compare every legal positive Strength table with original B680.

The local interpreter selects the original SSE vector branch and uses its
FLOAT32 division RCPPS seed and DOUBLE-exp-to-FLOAT32 scalar import. This is
controlled arithmetic evidence, not native Windows ISA or general UCRT proof.
"""
import json
from pathlib import Path
import struct
import subprocess

from aex_loader import AexLoader
import probe_radialblur_strength_20261002 as strength

public = strength.public
HARNESS = '''#include "production_under_test.cpp"
#include <iostream>
#include <iomanip>
int main() {
  int length;
  while(std::cin>>length) {
    auto native_rule=RotationFadeGaussianWeights(length);
    auto old_rule=ZoomGaussianWeights(length);
    for(const auto& table: {native_rule,old_rule}) {
      for(float value:table) { unsigned word;std::memcpy(&word,&value,4);
        std::cout<<std::hex<<std::setw(8)<<std::setfill('0')<<word; }
      std::cout<<"\\n";
    }
  }
}
'''


def probe(directory, source):
    directory.mkdir(parents=True, exist_ok=False)
    loader = AexLoader(str(public.initial.AEX), verbose=False, fast=True)
    loader.register_libm_impls()
    # B680 and its 1d0e0 dispatcher read this ISA field; choose the observed
    # four-wide branch in disposable mapped memory, never the AEX on disk.
    loader.write_bytes(loader.image_base+0x2b180, struct.pack('<i', 2))
    pointer = loader.bump_alloc(2000*4+32)
    expected = []; import_count = 0
    for length in range(1, 2001):
        loader.write_bytes(pointer, bytes([0xa5])*(length*4+16))
        loader.call_function(loader.image_base+0xb680, int_args=[pointer, length], max_instructions=length*150+2000)
        assert len(loader.import_log) == length % 4
        import_count += len(loader.import_log)
        expected.append(loader.read_bytes(pointer, length*4))
        assert loader.read_bytes(pointer+length*4, 16) == bytes([0xa5])*16
        if length % 250 == 0: print('STRENGTH_TABLE_ORIGINAL', length, flush=True)
    hp = directory/'tables.cpp'; hp.write_text(HARNESS)
    previous = public.initial.HARNESS
    outputs = {}
    try:
        public.initial.HARNESS = hp
        for name, sanitize in [('o2', False), ('san', True)]:
            binary = public.build(directory/name, source, sanitize)
            run = subprocess.run([str(binary)], input=''.join(f'{n}\n' for n in range(1, 2001)),
                text=True, capture_output=True, check=True, env=strength.ENV)
            assert not run.stderr
            # Formatting changes std::cin to hex only on std::cout, so the
            # input Length remains decimal throughout the helper.
            lines = run.stdout.splitlines(); assert len(lines) == 4000
            outputs[name] = [struct.pack('<%dI'%(len(line)//8),
                *[int(line[i:i+8], 16) for i in range(0, len(line), 8)]) for line in lines]
    finally: public.initial.HARNESS = previous
    assert outputs['o2'] == outputs['san']
    rows = []
    for length, native in enumerate(expected, 1):
        actual, old = outputs['o2'][(length-1)*2:(length-1)*2+2]
        assert actual == native, length
        different = sum(a != b for a, b in zip(struct.iter_unpack('<I', native), struct.iter_unpack('<I', old)))
        rows.append(dict(length=length, word_count=length, vector_word_count=length & ~3,
            scalar_word_count=length-(length & ~3), before_different_words=different,
            native_sha256=public.sha(native), before_sha256=public.sha(old), both_sdk_builds_exact=True))
    return dict(case_count=len(rows), word_count=sum(r['word_count'] for r in rows),
        before_different_words=sum(r['before_different_words'] for r in rows), guards_intact=True,
        original_builder_rva='0xb680', controlled_isa_field=2, rows=rows,
        scalar_policy='FLOAT32 exponent -> host DOUBLE exp -> FLOAT32; native Windows UCRT unverified',
        native_windows_rcpps_or_isa_claimed=False, import_call_count=import_count,
        native_output_sha256=public.sha(b''.join(expected)))


if __name__ == '__main__':
    import sys
    result = probe(Path(sys.argv[1]), strength.candidate_source(strength.before_source()))
    Path(sys.argv[2]).write_text(json.dumps(result, indent=2)+'\n')
    print('STRENGTH_TABLES_DONE', {k: v for k, v in result.items() if k != 'rows'}, flush=True)
