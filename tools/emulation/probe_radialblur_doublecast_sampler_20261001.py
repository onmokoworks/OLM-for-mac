#!/usr/bin/env python3
"""Bind two residual pixels and every captured Zoom angle to retained UCRT bits.

The comparison explicitly counts arguments outside the Windows scalar census.
Full angle vectors/guest contexts/raw frames remain private.
"""
import argparse
import json
from pathlib import Path
import struct
import subprocess
import tempfile

import pefile
from PIL import Image
import probe_radialblur_public_aligned_20261001 as public
import probe_radialblur_noise_offset_counterfactual_20261001 as offset
import probe_radialblur_axis_reference_20261001 as axis


def bits(value):
    return '0x'+struct.pack('>f', value).hex()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--parent-worker', type=Path, required=True)
    ap.add_argument('--worker', type=Path, required=True)
    ap.add_argument('--build', type=Path, required=True)
    ap.add_argument('--report', type=Path, required=True)
    args = ap.parse_args()
    build = json.loads(args.build.read_text())
    assert public.sha(args.worker.read_bytes()) == build['worker_sha256']
    assert public.sha(args.parent_worker.read_bytes()) == build['parent_worker_sha256']
    cf = json.loads(offset.BASELINE.with_name('radialblur_noise_offset_counterfactual_20261001.json').read_text())
    assert public.sha(public.SOURCE.read_bytes()) == cf['candidate_source_sha256']
    native = json.loads(axis.NATIVE.read_text())
    native_rows = native['native_rows']
    assert public.sha(json.dumps(native_rows, sort_keys=True, separators=(',', ':')).encode()) == axis.NATIVE_ROWS_SHA
    lookup = {(r['left_bits'], r['right_bits']): r['native_ucrt_result_bits']
              for r in native_rows if r['function'] == 'atan2f'}
    pe = pefile.PE(str(public.initial.AEX))
    tau_bytes = pe.get_data(0x212e0, 8)
    tau = struct.unpack('<d', tau_bytes)[0]
    assert tau == 6.2831853
    rows = []
    with tempfile.TemporaryDirectory(prefix='radial_doublecast_sampler_') as directory:
        temp = Path(directory)
        binary = public.build(temp/'o2', public.SOURCE.read_text())
        for geometry in ([23, 13], [31, 19]):
            case = next(r for r in cf['rows'] if r['group'] == 'independent' and r['family'] == 1
                        and r['depth'] == 32 and r['geometry'] == geometry
                        and next(p['value'] for p in r['parameters'] if p['slot'] == 28) == 0)
            width, height = geometry
            image = Image.new('RGBA', (width, height))
            image.putdata([(r, g, b, a) for a, r, g, b in public.initial.pixels(width, height, 'opaque')])
            ip = temp/'input.png'; image.save(ip)
            api = public.native_case(case)
            assignments = [f"param_{p['slot']}@{p['slot']}"+(':angle' if p['kind'] == 'a' else '')+'='+
                           (','.join(map(str, p['value'])) if isinstance(p['value'], list) else str(p['value']))
                           for p in api['parameters']]
            selected_points = [(30, 16), (24, 17)] if geometry == [31, 19] else []
            watches = ['--watch', 'function=0x8690,arg=r9,size=272',
                       '--watch', 'function=0x56f0,arg=rcx,size=48',
                       '--watch', 'function=0xa850,arg=stack5,size=4']
            for x, y in selected_points:
                watches += ['--watch', f'function=0x9d80,arg=rdx,size=16,occurrence={y*width+x+1}']
            run = subprocess.run([str(args.worker), 'render-trace-png', str(public.initial.AEX), str(ip),
                                  str(temp/'corrected.png'), '--pixel-format', 'argb32f', *watches, *assignments],
                                 capture_output=True, check=True)
            trace = json.loads(run.stdout)
            assert trace['render_error'] == 0 and trace['guards_intact']
            assert not trace['unsupported_suite_calls'] and not trace['dropped_unsupported_suite_calls']
            smart = next(t for t in trace['execution_traces'] if t['selector'] == 'SMART_RENDER')
            assert not smart['truncated'] and not smart['dropped_memory_witnesses']
            ws = smart['memory_witnesses']
            config = bytes.fromhex(next(w for w in ws if w['watch_id'] == 'watch-1')['after']['hex'])
            transform = bytes.fromhex(next(w for w in ws if w['watch_id'] == 'watch-2')['after']['hex'])
            center = list(struct.unpack_from('<2d', config, 0x28))
            assert center == [width//2, height//2]
            assert struct.unpack_from('<f', transform, 0x20)[0] == 1.0
            assert transform[0x28:0x30] == struct.pack('<2f', 1.0, 0.0)
            angles = [bytes.fromhex(w['after']['hex']) for w in ws if w['watch_id'] == 'watch-3']
            assert len(angles) == width*height
            expected, observed, unknown = bytearray(), bytearray(), []
            for i, angle in enumerate(angles):
                x, y = i % width, i//width
                key = (bits(y-center[1]), bits(x-center[0]))
                if key not in lookup:
                    unknown.append([x, y]); continue
                native_angle = struct.unpack('>f', bytes.fromhex(lookup[key][2:]))[0]
                normalized = struct.pack('<f', native_angle+tau if native_angle < 0 else native_angle)
                assert angle == normalized, (geometry, x, y, angle.hex(), normalized.hex())
                expected.extend(normalized); observed.extend(angle)
            parent, _, _, close, _ = public.native_render(args.parent_worker, temp, case)
            corrected, _, _, close2, _ = public.native_render(args.worker, temp, case)
            assert close['session_clean'] and close2['session_clean']
            assert public.sha(parent) == case['native_raw_sha256']
            assert public.sha(corrected) == trace['raw_pixel_sha256']
            error, mac, metadata = public.mac_render(binary, temp, case, 'classic')
            assert error == 0 and mac == corrected
            differences = sorted({i//16 for i, (a, b) in enumerate(zip(parent, mac)) if a != b})
            assert [[i%width, i//width] for i in differences] == [list(p) for p in selected_points]
            points = []
            if selected_points:
                parent_watches = []
                for x, y in selected_points:
                    occ = y*width+x+1
                    parent_watches += ['--watch', f'function=0xa850,arg=stack5,size=4,occurrence={occ}',
                                       '--watch', f'function=0x9d80,arg=rdx,size=16,occurrence={occ}']
                run2 = subprocess.run([str(args.parent_worker), 'render-trace-png', str(public.initial.AEX),
                                      str(ip), str(temp/'parent.png'), '--pixel-format', 'argb32f',
                                      *parent_watches, *assignments], capture_output=True, check=True)
                parent_trace = json.loads(run2.stdout)
                assert parent_trace['raw_pixel_sha256'] == public.sha(parent)
                old_ws = next(t for t in parent_trace['execution_traces'] if t['selector'] == 'SMART_RENDER')['memory_witnesses']
                for index, (x, y) in enumerate(selected_points):
                    off = (y*width+x)*16
                    rgba = mac[off+4:off+16]+mac[off:off+4]
                    sample = next(w for w in ws if w['watch_id'] == f'watch-{index+4}')['after']['hex']
                    assert sample == rgba.hex()
                    old_angle = next(w for w in old_ws if w['watch_id'] == f'watch-{2*index+1}')['after']['hex']
                    old_sample = next(w for w in old_ws if w['watch_id'] == f'watch-{2*index+2}')['after']['hex']
                    key = (bits(y-center[1]), bits(x-center[0]))
                    points.append({'coordinate': [x, y], 'relative_coordinate': [x-center[0], y-center[1]],
                                   'native_scalar_argument_bits_yx': list(key), 'native_scalar_result_bits': lookup[key],
                                   'parent_angle_f32_le_hex': old_angle,
                                   'corrected_angle_f32_le_hex': angles[y*width+x].hex(),
                                   'parent_sample_rgba_f32_le_hex': old_sample,
                                   'corrected_sample_rgba_f32_le_hex': sample, 'mac_sample_rgba_f32_le_hex': rgba.hex()})
            rows.append({'geometry': geometry, 'family': 1, 'depth': 32, 'parameters': case['parameters'],
                         'input_sha256': case['input_sha256'], 'center': center,
                         'basis_cos_sin_f32_le_hex': transform[0x28:0x30].hex(),
                         'angle_count': len(angles), 'native_scalar_covered': len(observed)//4,
                         'native_scalar_uncovered': len(unknown), 'uncovered_coordinates': unknown,
                         'native_covered_expected_angle_sha256': public.sha(expected),
                         'native_covered_observed_angle_sha256': public.sha(observed),
                         'local_trace_sha256': public.sha(run.stdout), 'selected_points': points,
                         'parent_raw_sha256': public.sha(parent), 'corrected_raw_sha256': public.sha(corrected),
                         'mac_raw_sha256': public.sha(mac), 'corrected_trace_resident_exact': True,
                         'corrected_reference_mac_raw_exact': True, 'parent_different_bytes': sum(a != b for a, b in zip(parent, mac))})
    deps = [Path(__file__), public.SOURCE, offset.HEADER, offset.BASELINE.with_name('radialblur_noise_offset_counterfactual_20261001.json'),
            axis.NATIVE, Path(public.__file__), Path(public.initial.__file__), public.initial.HARNESS]
    report = {'schema': 'radialblur.doublecast-sampler-native-coverage/1', 'rows': rows,
              'aex_sha256': public.initial.AEX_SHA, 'source_sha256': cf['candidate_source_sha256'],
              'worker_sha256': build['worker_sha256'], 'parent_worker_sha256': build['parent_worker_sha256'],
              'native_rows_sha256': axis.NATIVE_ROWS_SHA, 'native_angle_wrap_f64_le_hex': tau_bytes.hex(),
              'summary': {'angle_count': sum(r['angle_count'] for r in rows),
                          'native_scalar_covered': sum(r['native_scalar_covered'] for r in rows),
                          'native_scalar_uncovered': sum(r['native_scalar_uncovered'] for r in rows),
                          'corrected_reference_mac_raw_exact': len(rows)},
              'dependencies_sha256': {str(p.relative_to(public.ROOT)): public.sha(p.read_bytes()) for p in deps},
              'claims_not_made': ['Uncovered y=+9 arguments have no retained native scalar evidence',
                                 'No new Windows run or arbitrary-argument UCRT implementation proof',
                                 'No full private angle vectors, contexts, raw frames, or original AEX published']}
    args.report.write_text(json.dumps(report, sort_keys=True, indent=2)+'\n')
    print('DOUBLECAST_SAMPLER_COVERAGE', report['summary'], flush=True)


if __name__ == '__main__':
    main()
