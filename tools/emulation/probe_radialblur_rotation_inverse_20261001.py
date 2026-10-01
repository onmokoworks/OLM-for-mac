#!/usr/bin/env python3
"""Locate the next natural Rotation difference after a matched Gaussian field."""
import argparse
import json
import os
from pathlib import Path
import struct
import subprocess

import probe_radialblur_rotation_fields_20261001 as fields
public = fields.public
FIELD_REPORT = public.ROOT/'reports/radialblur_rotation_fields_20261001.json'


def candidate_inverse_source(source):
    source = fields.candidate_source(source)
    start = source.index('\tconst double alpha_quantize_epsilon = 1.0e-4;', source.index('const bool use_generic_two_stage'))
    end = source.index('static bool RequiresNoiseLayer', start)
    final = source[start:end]
    old = """const float angle_scale = (use_aex_typed_quality_repeat || rotation_quality_repeat_noise_tuple) && info.quality == 3.0
                    ? RadialF32Div(RadialF32Mul((float)quality, 180.0f), (float)kPi)
                    : (float)(quality * 180.0 / kPi);""".replace('                    ', '\t\t\t\t\t')
    assert final.count(old) == 1
    replacement = """const float angle_scale = use_generic_two_stage
                    ? RadialF32Div(1.0f, (float)((double)(float)(1.0 / quality) * 0.017453292500000002))
                    : ((use_aex_typed_quality_repeat || rotation_quality_repeat_noise_tuple) && info.quality == 3.0
                       ? RadialF32Div(RadialF32Mul((float)quality, 180.0f), (float)kPi)
                       : (float)(quality * 180.0 / kPi));""".replace('                    ', '\t\t\t\t\t')
    final = final.replace(old, replacement)
    final = final.replace('use_aex_exact', '(use_aex_exact || use_generic_two_stage)')
    return source[:start]+final+source[end:]


def run(worker, temp):
    saved = json.loads(FIELD_REPORT.read_text()); case = saved['natural_case']
    assert public.sha(worker.read_bytes()) == saved['worker_sha256']
    assert public.sha(public.SOURCE.read_bytes()) == saved['source_sha256']
    hp = temp/'planes.cpp'; hp.write_text(fields.plane_harness()); old_harness = public.initial.HARNESS
    mac = {}; raw_hashes = {}
    try:
        public.initial.HARNESS = hp
        for name, source in [('before', public.SOURCE.read_text()),
                             ('gaussian_candidate', fields.candidate_source(public.SOURCE.read_text())),
                             ('inverse_candidate', candidate_inverse_source(public.SOURCE.read_text()))]:
            binary = public.build(temp/name, source)
            directory = temp/f'{name}_planes'; directory.mkdir()
            error, raw, _ = public.mac_render(binary, temp, case, 'classic',
                                            dict(os.environ, ROTATION_PLANES_DIRECTORY=str(directory)))
            assert not error
            raw_hashes[name] = public.sha(raw)
            if name != 'inverse_candidate':
                expected = saved['natural_results']['before' if name == 'before' else 'candidate']['raw_sha256']
                assert public.sha(raw) == expected
            mac[name] = {key: (directory/f'{key}.f32').read_bytes() for key in ['coordinates', 'final']}
    finally:
        public.initial.HARNESS = old_harness
    # Create the input through the same natural public fixture API.
    from PIL import Image
    w, h = case['geometry']; image = Image.new('RGBA', (w, h))
    image.putdata([(r, g, b, a) for a, r, g, b in public.initial.pixels(w, h, case['pattern'])])
    image.save(temp/'input.png')
    assignments = [f"param_{q['slot']}@{q['slot']}"+(':angle' if q['kind'] == 'a' else '')+'='+
                   (','.join(map(str, q['value'])) if isinstance(q['value'], list) else str(q['value']))
                   for q in public.native_case(case)['parameters']]
    watches = ['--watch', 'function=0x4640,arg=rcx,size=64,occurrence=1']
    for i in range(w*h):
        for rva, register, size in [(0x1b10, 'r9', 4), (0x1b10, 'stack5', 4), (0x1000, 'rdx', 16)]:
            watches += ['--watch', f'function={hex(rva)},arg={register},size={size},occurrence={i+1}']
    process = subprocess.run([str(worker), 'render-trace-png', str(public.initial.AEX), str(temp/'input.png'),
                              str(temp/'native.png'), '--pixel-format', 'argb32f', *watches, *assignments],
                             check=True, capture_output=True)
    (temp/'trace.json').write_bytes(process.stdout); output = json.loads(process.stdout)
    assert output['raw_pixel_sha256'] == case['reference_raw_sha256']
    assert output['render_error'] == 0 and output['guards_intact']
    assert not output['unsupported_suite_calls'] and not output['dropped_unsupported_suite_calls']
    trace = next(x for x in output['execution_traces'] if x['selector'] == 'SMART_RENDER')
    assert not trace['truncated'] and not trace['dropped_memory_witnesses']
    assert not trace['trace_configuration']['unhookable_watches']
    witnesses = {x['watch_id']: x for x in trace['memory_witnesses']}
    assert len(witnesses) == w*h*3+1
    config = bytes.fromhex(witnesses['watch-1']['after']['hex'])
    scale = struct.unpack_from('<f', config, 8)[0]
    step_degree, step_radian = struct.unpack_from('<2f', config)
    expected_radian = fields.f32(fields.f32(1/5)*.017453292500000002)
    assert step_degree == fields.f32(1/5) and step_radian == expected_radian
    assert scale == fields.f32(1/expected_radian)
    native_coords, native_final = bytearray(), bytearray()
    selected = []
    for i in range(w*h):
        def raw(k):
            witness = witnesses[f'watch-{2+i*3+k}']; assert witness['after']['status'] == 'captured'
            return bytes.fromhex(witness['after']['hex'])
        radius, = struct.unpack('<f', raw(0)); angle, = struct.unpack('<f', raw(1))
        native_coords.extend(struct.pack('<2f', fields.f32(angle*scale), radius))
        native_final.extend(raw(2))
        if i in [0, 1, h//2*w+w//2, w*h-1]:
            selected.append({'coordinate': [i%w, i//w], 'native_radius_f32_le_hex': raw(0).hex(),
                             'native_angle_f32_le_hex': raw(1).hex(),
                             'native_angle_index_f32_le_hex': struct.pack('<f', fields.f32(angle*scale)).hex(),
                             'before_coordinates_f32_le_hex': mac['before']['coordinates'][i*8:i*8+8].hex()})
    comparisons = {name: {'coordinates': fields.compare_words(bytes(native_coords), planes['coordinates']),
                          'sample_rgba': fields.compare_words(bytes(native_final), planes['final'])}
                   for name, planes in mac.items()}
    return {'schema': 'radialblur.rotation-inverse/1', 'source_sha256': saved['source_sha256'],
            'production_source_changed': False, 'worker_sha256': saved['worker_sha256'],
            'candidate_inverse_source_sha256': public.sha(candidate_inverse_source(public.SOURCE.read_text()).encode()),
            'mac_raw_sha256': raw_hashes,
            'inverse_candidate_natural_raw_exact': raw_hashes['inverse_candidate'] == case['reference_raw_sha256'],
            'field_report_sha256': public.sha(FIELD_REPORT.read_bytes()),
            'trace_sha256': public.sha(process.stdout), 'witness_count': len(witnesses),
            'truncated': False, 'native_raw_sha256': output['raw_pixel_sha256'],
            'native_angle_scale_f32_le_hex': config[8:12].hex(),
            'native_step_degree_f32_le_hex': config[:4].hex(),
            'native_step_radian_f32_le_hex': config[4:8].hex(),
            'angle_scale_matches_native_setter_order': True, 'comparisons': comparisons,
            'selected_points': selected,
            'dependencies_sha256': {str(p.relative_to(public.ROOT)): public.sha(p.read_bytes()) for p in
                                   [Path(__file__), Path(fields.__file__), public.initial.HARNESS]},
            'claims_not_made': ['No inverse coordinate/sampler/writer production change.',
                               'Gaussian matching does not close final output differences.',
                               'Controlled atan2 and RCPPS remain unverified for arbitrary native Windows inputs.']}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--worker', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True); ap.add_argument('--report', type=Path, required=True)
    args = ap.parse_args(); args.output.mkdir(exist_ok=False, parents=True)
    report = run(args.worker, args.output)
    args.report.write_text(json.dumps(report, sort_keys=True, indent=2)+'\n')
    print('ROTATION_INVERSE', {k: {nm: x['different_words'] for nm, x in v.items()}
                              for k, v in report['comparisons'].items()}, flush=True)


if __name__ == '__main__':
    main()
