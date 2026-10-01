#!/usr/bin/env python3
"""Typed public Angle/Offset builder and transform observations, with calibration."""
import argparse
import copy
import json
from pathlib import Path
import struct
import subprocess
import tempfile

from PIL import Image
import probe_radialblur_public_aligned_20261001 as public

ANGLE_RAW = [-23592960, -20564372, -7055345, -16384, -1, 0, 1, 16384,
             2949120, 14253070, 20963609, 23592960]


def cases():
    for family in (1, 2):
        base = next(c for c in public.specifications('getters')
                    if c['state'] == 'angle' and c['family'] == family and c['depth'] == 8)
        for raw in ANGLE_RAW:
            case = copy.deepcopy(base)
            case['state'] = 'angle'
            for p in case['parameters']:
                if p['slot'] == 18: p['value'] = raw/65536.0
            yield case
        for offset in (1, 30):
            case = next(c for c in public.specifications('getters')
                        if c['state'] == 'offset' and c['family'] == family and c['depth'] == 8)
            for p in case['parameters']:
                if p['slot'] == 28: p['value'] = offset
            yield case


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--worker', type=Path, required=True)
    ap.add_argument('--parent-worker', type=Path, required=True)
    ap.add_argument('--build', type=Path, required=True)
    ap.add_argument('--trace-dir', type=Path, required=True)
    ap.add_argument('--report', type=Path, required=True)
    args = ap.parse_args()
    build = json.loads(args.build.read_text())
    assert public.sha(args.worker.read_bytes()) == build['worker_sha256']
    assert public.sha(args.parent_worker.read_bytes()) == build['parent_worker_sha256']
    assert public.sha(public.initial.AEX.read_bytes()) == public.initial.AEX_SHA
    args.trace_dir.mkdir(parents=True, exist_ok=True)
    image = Image.new('RGBA', (20, 14))
    image.putdata([(r, g, b, a) for a, r, g, b in public.initial.pixels(20, 14, 'opaque')])
    ip = args.trace_dir/'input.png'; image.save(ip)
    rows, calibration = [], []
    with tempfile.TemporaryDirectory(prefix='radial_typed_trace_calibration_') as directory:
        temp = Path(directory)
        old = json.loads((public.ROOT/'reports/radialblur_public_getters_edge_fixed_20261001.json').read_text())
        for case in old['cases']:
            parent, *_ = public.native_render(args.parent_worker, temp, case)
            current, *_ = public.native_render(args.worker, temp, case)
            assert parent == current and public.sha(current) == case['native_raw_sha256']
            calibration.append({'family': case['family'], 'depth': case['depth'], 'state': case['state'],
                                'input_sha256': case['input_sha256'], 'raw_sha256': public.sha(current),
                                'parent_and_typed_worker_equal': True})
        for index, case in enumerate(cases()):
            native = public.native_case(case)
            assignments = [f"param_{p['slot']}@{p['slot']}"+(':angle' if p['kind'] == 'a' else '')+'='+
                           (','.join(map(str, p['value'])) if isinstance(p['value'], list) else str(p['value']))
                           for p in native['parameters']]
            init = 0x56f0 if case['family'] == 1 else 0x4640
            # 56f0 is Zoom; 4640 is Rotation. Decode their distinct layouts.
            command = [str(args.worker), 'render-trace-png', str(public.initial.AEX), str(ip),
                       str(args.trace_dir/f'output_{index}.png'),
                       '--watch', 'function=0x8690,arg=r9,size=272',
                       '--watch', 'function=0x1a2a0,arg=rdx,size=4',
                       '--watch', 'function=0x1a2b0,arg=rdx,size=4',
                       '--watch', f'function={hex(init)},arg=rcx,size=48', *assignments]
            run = subprocess.run(command, capture_output=True, check=True)
            (args.trace_dir/f'trace_{index}.json').write_bytes(run.stdout)
            data = json.loads(run.stdout)
            assert data['render_error'] == 0 and data['guards_intact']
            assert not data['unsupported_suite_calls'] and not data['dropped_unsupported_suite_calls']
            smart = next(t for t in data['execution_traces'] if t['selector'] == 'SMART_RENDER')
            assert not smart['truncated'] and not smart['dropped_memory_witnesses']
            witnesses = smart['memory_witnesses']
            selected = {wid: [w for w in witnesses if w['watch_id'] == wid]
                        for wid in ('watch-1', 'watch-2', 'watch-3', 'watch-4')}
            assert all(len(v) == 1 for v in selected.values())
            config = bytes.fromhex(selected['watch-1'][0]['after']['hex'])
            transform = bytes.fromhex(selected['watch-4'][0]['after']['hex'])
            cos_offset, sin_offset = ((0x28, 0x2c) if case['family'] == 1 else (0x1c, 0x20))
            raw, frame, payload, close, _ = public.native_render(args.worker, temp, case)
            assert public.sha(raw) == data['raw_pixel_sha256']
            rows.append(dict(case,
                native_api_parameters=native['parameters'], input_sha256=public.sha(public.fixture(case)),
                parameter_payload=payload, native_raw_sha256=public.sha(raw), frame_done=frame,
                angle_raw_hex=selected['watch-2'][0]['after']['hex'],
                angle_builder_i32=struct.unpack_from('<i', config, 0x7c)[0],
                noise_offset_f32_hex=selected['watch-3'][0]['after']['hex'],
                noise_offset_builder_f32_hex=config[0x100:0x104].hex(),
                center=list(struct.unpack_from('<2d', config, 0x28)),
                transform_function_rva=hex(init),
                transform_cos_f32_hex=transform[cos_offset:cos_offset+4].hex(),
                transform_sin_f32_hex=transform[sin_offset:sin_offset+4].hex(),
                local_trace_sha256=public.sha(run.stdout), render_mode=data['render_mode'],
                session_clean=close['session_clean']))
            print('RADIAL_TYPED_ROUTE', index+1, case['family'], case['state'],
                  rows[-1]['angle_builder_i32'], rows[-1]['noise_offset_builder_f32_hex'], flush=True)
    dependencies = [Path(__file__), Path(public.__file__), Path(public.initial.__file__),
                    Path(__file__).with_name('aexcompat_radial_typed_angle_trace_20261001.patch'),
                    Path(__file__).with_name('build_radialblur_typed_trace_worker_20261001.py')]
    report = {'schema': 'radialblur.typed-angle-public-route/1', 'aex_sha256': public.initial.AEX_SHA,
              'worker_sha256': build['worker_sha256'], 'parent_worker_sha256': build['parent_worker_sha256'],
              'build_sha256': public.sha(args.build.read_bytes()), 'case_count': len(rows), 'rows': rows,
              'calibration': calibration, 'input_png_sha256': public.sha(ip.read_bytes()),
              'dependencies_sha256': {str(p.relative_to(public.ROOT)): public.sha(p.read_bytes()) for p in dependencies},
              'claims_not_made': ['CLI extension sets original typed Angle field; does not change AEX or materializer',
                                 'Native Windows UCRT/AE and arbitrary settings/topology remain unproved',
                                 'Private trace/context addresses, PNGs and raw pixels are not published']}
    args.report.write_text(json.dumps(report, sort_keys=True, indent=2)+'\n')
    print('RESULT', len(rows), 'traced cases', len(calibration), 'calibrated resident cases', flush=True)


if __name__ == '__main__':
    main()
