#!/usr/bin/env python3
"""Binary-ground Rotation noise coordinates independently of render fixtures."""
import json
from pathlib import Path
import struct
import subprocess

from aex_loader import AexLoader
import probe_radialblur_gain_20261002 as gain

public = gain.public
THICKNESSES = [1, 1.7, 3.4, 3.4444446563720703, 7.000000953674316, 10, 16.5, 100]
COORDINATES = [0, 1, 2, 3, 7, 10, 16, 17, 18, 21, 31]
HARNESS = '''#include "production_under_test.cpp"
#include <iostream>
int main() {
  float samples[36*36];
  for(int i=0;i<36*36;++i)samples[i]=(float)((i*73+19)%4096)/4096.0f;
  unsigned word;int x,y,smooth;
  while(std::cin>>std::hex>>word>>std::dec>>x>>y>>smooth) {
    float size;std::memcpy(&size,&word,4);
    float value=smooth?SampleRadialNoisePlaneAEX(samples,36,size,x,y):
      SampleRadialBlockNoisePlaneAEX(samples,36,size,x,y);
    unsigned output;std::memcpy(&output,&value,4);
    std::cout<<std::hex<<output<<"\\n";
  }
}
'''


def cases():
    return [(size, x, y, smooth) for size in THICKNESSES
        for x in COORDINATES for y in COORDINATES for smooth in [0, 1]]


def probe(directory, source):
    directory.mkdir(parents=True, exist_ok=False)
    loader = AexLoader(str(public.initial.AEX), verbose=False, fast=False)
    definition, samples = loader.bump_alloc(80), loader.bump_alloc(36*36*4)
    loader.write_bytes(definition, bytes(80))
    # +8/+10/+40 are observed in the original 9680 readonly context and
    # initialized-grid witnesses; synthetic data isolates the sampler leaf.
    loader.write_bytes(definition+8, struct.pack('<Q', samples))
    loader.write_bytes(definition+0x10, struct.pack('<i', 36))
    plane = b''.join(struct.pack('<f', ((i*73+19)%4096)/4096) for i in range(36*36))
    loader.write_bytes(samples, plane)
    expected = []; commands = []
    for size, x, y, smooth in cases():
        encoded = struct.pack('<f', size)
        loader.write_bytes(definition+0x40, encoded)
        result = loader.call_function(0x180009680, int_args=[definition, x, y, smooth], max_instructions=200)
        assert not loader.import_log
        expected.append(struct.unpack('<I', result['xmm0'][:4])[0])
        commands.append(f'{struct.unpack("<I", encoded)[0]:x} {x} {y} {smooth}\n')
    assert loader.read_bytes(samples, len(plane)) == plane
    assert loader.read_bytes(definition, 0x40) == bytes(8)+struct.pack('<Q', samples)+struct.pack('<i',36)+bytes(0x40-20)
    previous = public.initial.HARNESS
    hp = directory/'sampler.cpp'; hp.write_text(HARNESS)
    comparisons = {}
    try:
        public.initial.HARNESS = hp
        sources = [('before', gain.before_source(), False), ('o2', source, False), ('san', source, True)]
        for name, code, sanitize in sources:
            binary = public.build(directory/name, code, sanitize)
            run = subprocess.run([str(binary)], input=''.join(commands).encode(), capture_output=True, check=True, env=gain.ENV)
            assert not run.stderr
            words = [int(s,16) for s in run.stdout.split()]
            assert len(words) == len(expected)
            different = [i for i, (a,b) in enumerate(zip(words,expected)) if a!=b]
            if name != 'before': assert not different
            comparisons[name] = dict(case_count=len(words), different_words=len(different),
                raw_sha256=public.sha(b''.join(struct.pack('<I',w) for w in words)))
    finally: public.initial.HARNESS = previous
    assert comparisons['before']['different_words'] > 0
    indices = [i for i,c in enumerate(cases()) if c[0] == 3.4 and c[1] == 17 and c[2] == 0]
    return dict(case_count=len(expected), imports=0, original_plane_unchanged=True,
        original_sampler_rva='0x9680', original_rule=gain.original_rule(), comparisons=comparisons,
        constructed_grid_sha256=public.sha(plane), native_output_sha256=public.sha(b''.join(struct.pack('<I',w) for w in expected)),
        scalar_witnesses=[dict(thickness=cases()[i][0], x=17, y=0, smooth=cases()[i][3], native_word=f'{expected[i]:08x}') for i in indices],
        native_windows_isa_or_host_claimed=False)


if __name__ == '__main__':
    import sys
    report = probe(Path(sys.argv[1]), gain.candidate_source(gain.before_source()))
    Path(sys.argv[2]).write_text(json.dumps(report, indent=2)+'\n')
    print('GAIN_SAMPLER', report['case_count'], report['comparisons'], flush=True)
