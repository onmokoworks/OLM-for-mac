#!/usr/bin/env python3
"""Bind the first sampler discrepancy to its reference axis and typed public row."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile

from PIL import Image
import probe_radialblur_public_aligned_20261001 as public


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--parent-worker', type=Path, required=True)
    ap.add_argument('--worker', type=Path, required=True)
    ap.add_argument('--public-report', type=Path, required=True)
    ap.add_argument('--report', type=Path, required=True)
    args = ap.parse_args()
    capture = json.loads(args.public_report.read_text())
    case = next(r for r in capture['rows'] if r['matrix'] == 'topology' and r['family'] == 1
                and r['depth'] == 32 and r['geometry'] == [17, 11]
                and r['pattern'] == 'opaque' and r['state'] == 'neutral')
    assert public.sha(args.parent_worker.read_bytes()) == capture['parent_worker_sha256']
    assert public.sha(args.worker.read_bytes()) == capture['worker_sha256']
    assert public.sha(public.SOURCE.read_bytes()) == capture['source_sha256']
    native = public.native_case(case)
    assignments = [f"param_{p['slot']}@{p['slot']}"+(':angle' if p['kind'] == 'a' else '')+'='+
                   (','.join(map(str, p['value'])) if isinstance(p['value'], list) else str(p['value']))
                   for p in native['parameters']]
    traces = {}
    with tempfile.TemporaryDirectory(prefix='radial_axis_sampler_') as directory:
        temp = Path(directory)
        image = Image.new('RGBA', (17, 11))
        image.putdata([(r, g, b, a) for a, r, g, b in public.initial.pixels(17, 11, 'opaque')])
        ip = temp/'input.png'; image.save(ip)
        for name, worker in [('parent', args.parent_worker), ('corrected', args.worker)]:
            # Cartesian-to-polar and final normalized sampler calls for pixel (0,5).
            cmd = [str(worker), 'render-trace-png', str(public.initial.AEX), str(ip), str(temp/(name+'.png')),
                   '--pixel-format', 'argb32f',
                   '--watch', 'function=0xa850,arg=r9,size=4,occurrence=86',
                   '--watch', 'function=0xa850,arg=stack5,size=4,occurrence=86',
                   '--watch', 'function=0x9d80,arg=rdx,size=16,occurrence=86', *assignments]
            run = subprocess.run(cmd, capture_output=True, check=True)
            trace = json.loads(run.stdout)
            assert trace['render_error'] == 0 and trace['guards_intact']
            assert not trace['unsupported_suite_calls'] and not trace['dropped_unsupported_suite_calls']
            smart = next(t for t in trace['execution_traces'] if t['selector'] == 'SMART_RENDER')
            assert not smart['truncated'] and not smart['dropped_memory_witnesses']
            selected = {wid: [w for w in smart['memory_witnesses'] if w['watch_id'] == wid]
                        for wid in ('watch-1', 'watch-2', 'watch-3')}
            assert all(len(v) == 1 for v in selected.values())
            traces[name] = {'local_trace_sha256': public.sha(run.stdout),
                            'raw_sha256': trace['raw_pixel_sha256'],
                            'radius_f32_le_hex': selected['watch-1'][0]['after']['hex'],
                            'angle_f32_le_hex': selected['watch-2'][0]['after']['hex'],
                            'sample_rgba_f32_le_hex': selected['watch-3'][0]['after']['hex'],
                            'guards_intact': True, 'unsupported_suite_calls': []}
            expected = case['parent_raw_sha256'] if name == 'parent' else case['corrected_raw_sha256']
            assert trace['raw_pixel_sha256'] == expected, (name, 'PNG trace/resident mismatch')
        binary = public.build(temp/'o2', public.SOURCE.read_text())
        error, raw, metadata = public.mac_render(binary, temp, case, 'classic')
        assert error == 0
        offset = 5*17*16
        rgba = raw[offset+4:offset+16]+raw[offset:offset+4]
        assert rgba.hex() == traces['corrected']['sample_rgba_f32_le_hex']
        assert public.sha(raw) == traces['corrected']['raw_sha256']
        assert traces['parent']['raw_sha256'] != traces['corrected']['raw_sha256']
        assert traces['parent']['angle_f32_le_hex'] == 'da0f4940'
        assert traces['corrected']['angle_f32_le_hex'] == 'db0f4940'
        assert traces['parent']['radius_f32_le_hex'] == traces['corrected']['radius_f32_le_hex'] == '00000041'
    deps = [Path(__file__), args.public_report.resolve(), public.SOURCE, public.initial.HARNESS,
            Path(public.__file__), Path(public.initial.__file__)]
    report = {'schema': 'radialblur.axis-sampler-first-difference/1',
              'case': {k: case[k] for k in ('matrix', 'row_index', 'geometry', 'depth', 'pattern',
                                          'family', 'state', 'parameters', 'input_sha256')},
              'aex_sha256': capture['aex_sha256'], 'worker_sha256': capture['worker_sha256'],
              'parent_worker_sha256': capture['parent_worker_sha256'], 'source_sha256': capture['source_sha256'],
              'public_coordinate': [0, 5], 'relative_coordinate': [-8, 0], 'call_occurrence': 86,
              'traces': traces, 'mac_raw_sha256': public.sha(raw),
              'mac_sample_rgba_f32_le_hex': rgba.hex(), 'mac_metadata': metadata,
              'corrected_trace_matches_typed_resident': True,
              'corrected_trace_and_mac_full_raw_exact': True,
              'dependencies_sha256': {str(p.relative_to(public.ROOT)): public.sha(p.read_bytes()) for p in deps},
              'claims_not_made': ['Only the captured scalar axis is bound to retained native Windows evidence',
                                 'Controlled public render is not native Windows AE',
                                 'No private trace addresses, raw frames, PNGs or original AEX published']}
    args.report.write_text(json.dumps(report, sort_keys=True, indent=2)+'\n')
    print('AXIS_SAMPLER', report['mac_raw_sha256'], flush=True)


if __name__ == '__main__':
    main()
