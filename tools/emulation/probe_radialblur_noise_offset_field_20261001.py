#!/usr/bin/env python3
"""Original public builder -> initialized noise plane, compared with the port.

Read the plane at the first sampler call: a constructor-entry pointer is still
uninitialized, and the trace worker resolves dereferences at entry.
"""
import argparse
import json
from pathlib import Path
import struct
import subprocess
import tempfile

from PIL import Image
import probe_radialblur_public_aligned_20261001 as public

HARNESS = Path(__file__).with_name('radialblur_noise_plane_harness_20261001.cpp')
PHASE_RAW = [0, 1, 16384, 65536, 1966080, 5898240, 23592960, 2147483647]
PROFILES = [(1, 1, 3.0), (1, 2, 10.0), (2, 1, 10.0)]
GEOMETRIES = [(23, 13), (31, 19)]


def case_for(family, geometry, depth, noise_type, seed, thickness, raw, variation=25):
    case = {'family': family, 'geometry': list(geometry), 'depth': depth,
            'pattern': 'opaque', 'state': 'noise_offset',
            'parameters': public.initial.settings(family, *geometry)}
    changes = {24: variation, 25: noise_type, 27: seed, 28: raw/65536.0, 29: thickness}
    for p in case['parameters']:
        if p['slot'] in changes: p['value'] = changes[p['slot']]
    return case


def f32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]


def plane_dimensions(geometry, thickness):
    inverse = f32(1.0/f32(thickness))
    return [int(f32(f32(f32(v)*inverse)+3.0)) for v in geometry]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--worker', type=Path, required=True)
    ap.add_argument('--build', type=Path, required=True)
    ap.add_argument('--report', type=Path, required=True)
    args = ap.parse_args()
    build = json.loads(args.build.read_text())
    assert public.sha(args.worker.read_bytes()) == build['worker_sha256']
    assert public.sha(public.initial.AEX.read_bytes()) == public.initial.AEX_SHA
    rows = []
    with tempfile.TemporaryDirectory(prefix='radial_offset_field_') as directory:
        temp = Path(directory)
        binary = temp/'plane'
        subprocess.run(['clang++', '-std=c++17', '-O2', '-fno-fast-math', '-ffp-contract=off',
                        str(HARNESS), '-o', str(binary)], check=True)
        for family in (1, 2):
            for geometry in GEOMETRIES:
                image = Image.new('RGBA', geometry)
                image.putdata([(r, g, b, a) for a, r, g, b in public.initial.pixels(*geometry, 'opaque')])
                ip = temp/'input.png'; image.save(ip)
                for noise_type, seed, thickness in PROFILES:
                    dimensions = plane_dimensions(geometry, thickness)
                    size = 4*dimensions[0]*dimensions[1]
                    assert size <= 4096
                    for raw in PHASE_RAW:
                        case = case_for(family, geometry, 8, noise_type, seed, thickness, raw)
                        native = public.native_case(case)
                        assignments = [f"param_{p['slot']}@{p['slot']}"+(':angle' if p['kind'] == 'a' else '')+'='+
                                       (','.join(map(str, p['value'])) if isinstance(p['value'], list) else str(p['value']))
                                       for p in native['parameters']]
                        run = subprocess.run([str(args.worker), 'render-trace-png', str(public.initial.AEX),
                            str(ip), str(temp/'output.png'),
                            '--watch', 'function=0x1a2b0,arg=rdx,size=4',
                            '--watch', 'function=0x9680,arg=rcx,size=72,occurrence=1',
                            '--watch', f'function=0x9680,arg=rcx,deref=8,size={size},occurrence=1',
                            *assignments], capture_output=True, check=True)
                        trace = json.loads(run.stdout)
                        assert trace['render_error'] == 0 and trace['guards_intact']
                        assert not trace['unsupported_suite_calls'] and not trace['dropped_unsupported_suite_calls']
                        smart = next(t for t in trace['execution_traces'] if t['selector'] == 'SMART_RENDER')
                        assert not smart['truncated'] and not smart['dropped_memory_witnesses']
                        selected = {wid: [w for w in smart['memory_witnesses'] if w['watch_id'] == wid]
                                    for wid in ('watch-1', 'watch-2', 'watch-3')}
                        assert all(len(v) == 1 for v in selected.values())
                        leaf = bytes.fromhex(selected['watch-1'][0]['after']['hex'])
                        context = bytes.fromhex(selected['watch-2'][0]['before']['hex'])
                        native_plane = bytes.fromhex(selected['watch-3'][0]['before']['hex'])
                        assert selected['watch-3'][0]['before']['status'] == 'captured'
                        assert selected['watch-3'][0]['before']['hex'] == selected['watch-3'][0]['after']['hex']
                        assert list(struct.unpack_from('<2i', context, 0x10)) == dimensions
                        assert list(struct.unpack_from('<2i', context, 0x18)) == list(geometry)
                        assert struct.unpack_from('<i', context, 0x20)[0] == 100
                        thickness_bits = struct.unpack_from('<I', context, 0x40)[0]
                        phase_bits = struct.unpack('<I', leaf)[0]
                        assert struct.unpack('<f', leaf)[0] == f32(raw*2.663161090079238e-7)
                        expected = subprocess.run([str(binary), *map(str, geometry), f'{thickness_bits:08x}',
                                                   f'{phase_bits:08x}', str(seed)], capture_output=True, check=True)
                        assert list(map(int, expected.stderr.split())) == dimensions
                        assert expected.stdout == native_plane, (family, geometry, noise_type, seed, raw)
                        resident, frame, _, close, _ = public.native_render(args.worker, temp, case)
                        assert public.sha(resident) == trace['raw_pixel_sha256']
                        assert close['session_clean'] and not close['unsupported_suite_calls']
                        rows.append(dict(case, raw_fixed=raw, input_sha256=public.sha(public.fixture(case)),
                                         native_raw_sha256=public.sha(resident), phase_f32_le_hex=leaf.hex(),
                                         plane_dimensions=dimensions, plane_float_count=size//4,
                                         native_plane_sha256=public.sha(native_plane), core_plane_sha256=public.sha(expected.stdout),
                                         plane_first_four_f32_le_hex=native_plane[:16].hex(),
                                         native_plane_unchanged_by_sampler=True, core_plane_raw_exact=True,
                                         local_trace_sha256=public.sha(run.stdout), session_clean=True))
                        if len(rows) % 12 == 0: print('OFFSET_FIELD', len(rows), flush=True)
    deps = [Path(__file__), HARNESS, public.ROOT/'core/dblur_noise.h', Path(public.__file__),
            Path(public.initial.__file__), public.ROOT/'reports/radialblur_axis_reference_build_20261001.json']
    report = {'schema': 'radialblur.noise-offset-public-field/1', 'case_count': len(rows), 'rows': rows,
              'summary': {'plane_raw_exact': len(rows), 'typed_resident_matches_trace': len(rows)},
              'aex_sha256': public.initial.AEX_SHA, 'worker_sha256': build['worker_sha256'],
              'dependencies_sha256': {str(p.relative_to(public.ROOT)): public.sha(p.read_bytes()) for p in deps},
              'claims_not_made': ['Positive fixed phases only; negative-phase table reads remain unverified',
                                 'Independent source factor/scatter/writer and all settings are not closed',
                                 'Controlled imports do not prove native Windows UCRT/AE equivalence',
                                 'No original AEX, private contexts, full grid or image data published']}
    args.report.write_text(json.dumps(report, sort_keys=True, indent=2)+'\n')
    print('OFFSET_FIELD_RESULT', report['summary'], flush=True)


if __name__ == '__main__':
    main()
