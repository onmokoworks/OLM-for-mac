#!/usr/bin/env python3
"""Natural no-noise Rotation fields justify removing a feature-dependent gate."""
import argparse
import copy
import json
import os
from pathlib import Path
import struct
import subprocess

from PIL import Image
import probe_radialblur_rotation_fields_20261001 as fields
import probe_radialblur_pf8_writer_20261001 as writer
public = fields.public
BEFORE = public.ROOT/'reports/radialblur_rotation_restoration_public_20261001.json'
BEFORE_REVISION = 'f5a74754df8b279455dd1c13839313078faa68b1'
OLD = '''const bool use_generic_two_stage = use_generic_baseline &&
		(info.inner_strength != 0 || info.outer_edge_fade != 0 || info.inner_edge_fade != 0 ||
		 info.outer_offset_mode != 1 || info.inner_offset_mode != 1 ||
		 info.noise_variation != 0.0 || info.size_variation != 0.0);'''


def before_source():
    source = subprocess.check_output(['git', 'show', BEFORE_REVISION+':mac/OLMRadialBlur/OLMRadialBlur.cpp'],
                                     cwd=public.ROOT).decode()
    assert public.sha(source.encode()) == json.loads(BEFORE.read_text())['source_sha256']
    return source


def candidate_source(source):
    assert source.count(OLD) == 1
    return source.replace(OLD, 'const bool use_generic_two_stage = use_generic_baseline;')


def passive_legacy_source(source):
    """Read four real legacy planes; do not invent nonexistent accum/max planes."""
    start = source.index('const bool use_generic_two_stage')
    marker = '\tconst double alpha_quantize_epsilon = 1.0e-4;'
    pos = source.index(marker, start)
    capture = '''#if defined(OLM_RADIALBLUR_TEST_SEAM)
    if (!use_aex_two_stage && g_rotation_test_capture) {
        auto &capture = *g_rotation_test_capture;
        const size_t cells = (size_t)radius_count * angular_count;
        if (capture.capacity_cells < cells) return PF_Err_BAD_CALLBACK_PARAM;
        std::copy(polar.rgba.begin(), polar.rgba.end(), capture.polar_rgba);
        std::copy(rotation_source_scalar.begin(), rotation_source_scalar.end(), capture.source_scalar);
        std::copy(blurred.rgba.begin(), blurred.rgba.end(), capture.normalized_rgba);
        std::copy(rotation_scalar_source_with_guard.begin(), rotation_scalar_source_with_guard.end()-1, capture.source_span);
        capture.written_cells = cells; capture.width = angular_count; capture.height = radius_count;
    }
#endif
'''
    return source[:pos]+capture+source[pos:]


def trace(worker, temp, case):
    w, h = case['geometry']; image = Image.new('RGBA', (w, h))
    image.putdata([(r, g, b, a) for a, r, g, b in public.initial.pixels(w, h, case['pattern'])])
    image.save(temp/'input.png')
    assignments = [f"param_{q['slot']}@{q['slot']}"+(':angle' if q['kind'] == 'a' else '')+'='+
                   (','.join(map(str, q['value'])) if isinstance(q['value'], list) else str(q['value']))
                   for q in public.native_case(case)['parameters']]
    command = [str(worker), 'render-trace-png', str(public.initial.AEX), str(temp/'input.png'),
               str(temp/'native.png'), '--pixel-format', 'argb32f']
    run = subprocess.run(command+['--watch', 'function=0x4640,arg=rcx,size=64,occurrence=1']+assignments,
                         capture_output=True, check=True)
    output = json.loads(run.stdout)
    assert output['raw_pixel_sha256'] == case['reference_raw_sha256']
    smart = next(x for x in output['execution_traces'] if x['selector'] == 'SMART_RENDER')
    config = bytes.fromhex(smart['memory_witnesses'][0]['after']['hex'])
    minimum, maximum = struct.unpack_from('<2i', config, 12)
    step, = struct.unpack_from('<f', config)
    angular = int(fields.f32(360/step)); radial = maximum-minimum
    planes = [('polar', 0x2780, 'rdx', None, angular*radial*16),
              ('scalar', 0x2780, 'rcx', 0x40, angular*radial*4),
              ('normalized', 0x1000, 'rcx', None, angular*radial*16),
              ('span', 0x4640, 'rdx', 0x90, w*h*4),
              ('accum', 0x1b10, 'rcx', 0x3c940, angular*radial*16),
              ('max', 0x1b10, 'rcx', 0x3c948, angular*radial*4)]
    watches, windows = [], []
    for name, rva, register, deref, size in planes:
        for offset in range(0, size, 4096):
            length = min(4096, size-offset)
            spec = f'function={hex(rva)},arg={register},size={length},offset={offset},occurrence=1'
            if deref is not None: spec += f',deref={hex(deref)}'
            watches += ['--watch', spec]; windows.append((name, length))
    run = subprocess.run(command+watches+assignments, capture_output=True, check=True)
    (temp/'native_trace.json').write_bytes(run.stdout); output = json.loads(run.stdout)
    assert output['raw_pixel_sha256'] == case['reference_raw_sha256']
    assert output['render_error'] == 0 and output['guards_intact']
    assert not output['unsupported_suite_calls'] and not output['dropped_unsupported_suite_calls']
    smart = next(x for x in output['execution_traces'] if x['selector'] == 'SMART_RENDER')
    assert not smart['truncated'] and not smart['dropped_memory_witnesses']
    assert not smart['trace_configuration']['unhookable_watches']
    witnesses = {x['watch_id']: x for x in smart['memory_witnesses']}; assert len(witnesses) == len(windows)
    native = {}
    for name, *_ in planes:
        parts = []
        for i, (nm, size) in enumerate(windows):
            if nm != name: continue
            data = witnesses[f'watch-{i+1}']['before']; assert data['status'] == 'captured'
            raw = bytes.fromhex(data['hex']); assert len(raw) == size; parts.append(raw)
        native[name] = b''.join(parts)
        (temp/f'native_{name}.f32').write_bytes(native[name])
    return native, {'native_dimensions': [angular, radial], 'native_min_radius': minimum,
                    'witness_count': len(witnesses), 'trace_sha256': public.sha(run.stdout),
                    'config_trace_sha256': public.sha(config), 'raw_sha256': output['raw_pixel_sha256'],
                    'truncated': False, 'guards_intact': True}


def natural_cases(capture):
    return [next(r for r in capture['rows'] if r['group'] == 'retained' and r['family'] == 2
                 and r['depth'] == 32 and r['geometry'] == geometry and r['pattern'] == pattern and r['state'] == 'neutral')
            for geometry, pattern in [([20, 14], 'opaque'), ([17, 11], 'islands'), ([20, 14], 'right'), ([20, 14], 'ring')]]


def natural(worker, temp, capture, source, candidate):
    old_harness = public.initial.HARNESS; hp = temp/'planes.cpp'; hp.write_text(fields.plane_harness())
    try:
        public.initial.HARNESS = hp
        binaries = {'before': public.build(temp/'before_planes', passive_legacy_source(source)),
                    'candidate': public.build(temp/'candidate_planes', candidate)}
    finally:
        public.initial.HARNESS = old_harness
    results = []
    for index, case in enumerate(natural_cases(capture)):
        directory = temp/f'natural_{index}'; directory.mkdir()
        native, witness = trace(worker, directory, case)
        comparisons, hashes, dims = {}, {}, {}
        for name, binary in binaries.items():
            plane_dir = directory/name; plane_dir.mkdir()
            error, raw, _ = public.mac_render(binary, directory, case, 'classic',
                                              dict(os.environ, ROTATION_PLANES_DIRECTORY=str(plane_dir)))
            assert not error; hashes[name] = public.sha(raw)
            if name == 'before': assert hashes[name] == case['results']['classic']['raw_sha256']
            dims[name] = list(struct.unpack('<2i', (plane_dir/'dimensions.i32').read_bytes()))
            selected = ['polar', 'scalar', 'normalized', 'span'] if name == 'before' else list(native)
            comparisons[name] = {key: fields.compare_words(native[key], (plane_dir/f'{key}.f32').read_bytes()[:len(native[key])])
                                  for key in selected}
        results.append({'case': case, 'trace': witness, 'mac_dimensions': dims, 'field_comparisons': comparisons,
                        'mac_raw_sha256': hashes, 'candidate_raw_exact': hashes['candidate'] == case['reference_raw_sha256']})
        print('NEUTRAL_NATURAL', index, case['pattern'], results[-1]['candidate_raw_exact'],
              {k: v['different_words'] for k, v in comparisons['candidate'].items()}, flush=True)
    return results


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--worker', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True); ap.add_argument('--report', type=Path, required=True)
    args = ap.parse_args(); args.output.mkdir(exist_ok=False, parents=True)
    before = json.loads(BEFORE.read_text()); source = before_source(); candidate = candidate_source(source)
    live_source_sha = public.sha(public.SOURCE.read_bytes())
    build = json.loads((public.ROOT/'reports/radialblur_readonly_windows_reference_build_20261001.json').read_text())
    assert public.sha(args.worker.read_bytes()) == build['worker_sha256']
    assert public.sha(public.initial.AEX.read_bytes()) == before['aex_sha256']
    witnesses = natural(args.worker, args.output, before, source, candidate)
    binaries = {'o2': public.build(args.output/'o2', candidate), 'san': public.build(args.output/'san', candidate, sanitize=True)}
    env = dict(os.environ, ASAN_OPTIONS='detect_leaks=0:halt_on_error=1', UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
    rows = []
    for index, case in enumerate(before['rows']):
        results = {}
        for build_name, binary in binaries.items():
            for command in ['classic', 'smart']:
                error, raw, metadata = public.mac_render(binary, args.output, case, command, env)
                old = case['results'][command]; assert error == old['error'] and metadata == old['metadata']
                result = {'error': error, 'raw_sha256': public.sha(raw) if not error else None,
                          'raw_exact': not error and public.sha(raw) == case['reference_raw_sha256'],
                          'metadata': metadata, 'before_raw_exact': old['raw_exact'],
                          'before_raw_unchanged': (public.sha(raw) if not error else None) == old['raw_sha256']}
                if build_name == 'o2': results[command] = result
                else: assert result == results[command], (index, command)
        row = {k: copy.deepcopy(case[k]) for k in ['family', 'geometry', 'depth', 'pattern', 'state', 'parameters',
               'group', 'matrix', 'row_index', 'input_sha256', 'reference_raw_sha256', 'parent_raw_sha256']}
        row['results'] = results; rows.append(row)
        if (index+1) % 128 == 0: print('NEUTRAL_PUBLIC', index+1, flush=True)
    assert public.sha(public.SOURCE.read_bytes()) == live_source_sha
    report = {'schema': 'radialblur.rotation-neutral-public/1', 'source_before_sha256': before['source_sha256'],
              'source_sha256': public.sha(candidate.encode()), 'header_sha256': before['header_sha256'],
              'production_source_changed_during_probe': False, 'probe_start_source_sha256': live_source_sha,
              'before_revision': BEFORE_REVISION, 'aex_sha256': before['aex_sha256'],
              'controlled_worker_sha256': before['controlled_worker_sha256'], 'window_worker_sha256': build['worker_sha256'],
              'rows': rows, 'summary': writer.summarize(rows), 'public_replay_count': len(rows)*4,
              'natural_witnesses': witnesses,
              'matrix_summaries': {m: writer.summarize([r for r in rows if r['matrix'] == m]) for m in before['matrix_summaries']},
              'dependencies_sha256': {str(p.relative_to(public.ROOT)): public.sha(p.read_bytes()) for p in
                                      [Path(__file__), Path(fields.__file__), BEFORE, public.SOURCE.with_suffix('.h'), public.initial.HARNESS]},
              'claims_not_made': ['A neutral opaque anchor does not prove alpha topology or Size/Angle compatibility.',
                                 'Extra radius row, Windows CPU/UCRT/AE/UI/save/ROI/downsample and all-ten completion remain open.']}
    args.report.write_text(json.dumps(report, sort_keys=True, indent=2)+'\n')
    print('NEUTRAL_DONE', report['summary'], flush=True)


if __name__ == '__main__':
    main()
