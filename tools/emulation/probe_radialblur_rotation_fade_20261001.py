#!/usr/bin/env python3
"""Compare the real B680 fade tables and Rotation planes without changing references.

The scalar tail retains the existing Zoom expf policy. Three disagreements with
host expf in the controlled worker are evidence, not a reason to replace that
policy. Native Windows ISA/RCPPS/UCRT remain independent open boundaries.
Only hashes/counts and a few scalar differences are published; raw stays private.
"""
import argparse
import copy
import json
import math
import os
from pathlib import Path
import struct
import subprocess

from PIL import Image
import probe_radialblur_rotation_neutral_20261001 as neutral
public = neutral.public
fields = neutral.fields
writer = neutral.writer
BEFORE = public.ROOT/'reports/radialblur_rotation_neutral_alpha_public_20261001.json'
BEFORE_REVISION = 'bed824a79503ef2028a56d5f2428897c85329cbc'
HELPER = '''// AEX B680 builds fade weights with four-wide embedded exp and a scalar tail.
// Keep the existing scalar expf policy; native Windows ISA/RCPPS remain open.
static std::vector<float> RotationFadeGaussianWeights(A_long length)
{
    auto weights = ZoomGaussianWeights(length);
    if (length < 4) return weights;
    float denominator = RadialF32Mul((float)length, (float)length);
    denominator = RadialF32Mul(denominator, 0.111111119389534f);
    denominator = RadialF32Add(denominator, denominator);
    denominator = (float)((double)denominator + 1.0e-5);
    const float inverse = RadialF32Div(1.0f, denominator);
    // The controlled interpreter supplies a division seed to original RCPPS.
    // Preserve the AEX's separate FLOAT32 Newton operations after that seed.
    const float refined = RadialF32Sub(RadialF32Add(inverse, inverse),
        RadialF32Mul(RadialF32Mul(inverse, inverse), denominator));
    const A_long vector_end = length & ~3;
    for (A_long i = 0; i < vector_end; ++i) {
        const float exponent = RadialF32Mul((float)(-((int)i * (int)i)), refined);
        weights[(size_t)i] = RotationGaussianSIMDExp(exponent);
    }
    return weights;
}

'''


def before_source():
    source = subprocess.check_output(['git', 'show', BEFORE_REVISION+':mac/OLMRadialBlur/OLMRadialBlur.cpp'],
                                     cwd=public.ROOT).decode()
    assert public.sha(source.encode()) == json.loads(BEFORE.read_text())['source_sha256']
    return source


def candidate_source(source):
    marker = 'static std::vector<float> RotationGaussianWeights('
    assert source.count(marker) == 1
    source = source.replace(marker, HELPER+marker)
    start = source.index('const A_long outer_fade_span = std::max<A_long>(0, info.outer_edge_fade - 1)')
    end = source.index('auto polar_alpha_linear', start)
    part = source[start:end]; assert part.count('ZoomGaussianWeights(') == 2
    return source[:start]+part.replace('ZoomGaussianWeights(', 'RotationFadeGaussianWeights(')+source[end:]


def model(length):
    denominator = fields.f32(fields.f32(fields.f32(length)*fields.f32(length))*fields.f32(.111111119389534))
    denominator = fields.f32(fields.f32(denominator+denominator)+1e-5)
    inverse = fields.f32(1/denominator)
    refined = fields.f32(fields.f32(inverse+inverse)-fields.f32(fields.f32(inverse*inverse)*denominator))
    end = length & ~3
    args = [fields.f32(fields.f32(-i*i)*(refined if i < end else inverse)) for i in range(length)]
    result = b''.join(struct.pack('<f', fields.simd_exp(x) if i < end else fields.f32(math.exp(x)))
                      for i, x in enumerate(args))
    return result, {'denominator_bits': hex(fields.bits(denominator)), 'division_inverse_bits': hex(fields.bits(inverse)),
                    'controlled_newton_bits': hex(fields.bits(refined)), 'vector_word_count': end,
                    'scalar_word_count': length-end, 'arguments_sha256': public.sha(struct.pack('<%df'%length, *args))}


def table_trace(worker, temp, case, length):
    w, h = case['geometry']; image = Image.new('RGBA', (w, h))
    image.putdata([(r, g, b, a) for a, r, g, b in public.initial.pixels(w, h, case['pattern'])])
    image.save(temp/'input.png')
    assignments = [f"param_{q['slot']}@{q['slot']}"+(':angle' if q['kind'] == 'a' else '')+'='+
                   (','.join(map(str, q['value'])) if isinstance(q['value'], list) else str(q['value']))
                   for q in public.native_case(case)['parameters']]
    run = subprocess.run([str(worker), 'render-trace-png', str(public.initial.AEX), str(temp/'input.png'),
                          str(temp/'trace.png'), '--pixel-format', 'argb32f', '--watch',
                          f'function=0xb680,arg=rcx,size={length*4},occurrence=3', *assignments],
                         capture_output=True, check=True)
    (temp/'trace.json').write_bytes(run.stdout); report = json.loads(run.stdout)
    assert report['raw_pixel_sha256'] == case['reference_raw_sha256']
    assert report['render_error'] == 0 and report['guards_intact']
    assert not report['unsupported_suite_calls'] and not report['dropped_unsupported_suite_calls']
    smart = next(x for x in report['execution_traces'] if x['selector'] == 'SMART_RENDER')
    assert not smart['truncated'] and not smart['dropped_memory_witnesses']
    assert not smart['trace_configuration']['unhookable_watches']
    assert len(smart['memory_witnesses']) == 1
    data = smart['memory_witnesses'][0]['after']; assert data['status'] == 'captured'
    raw = bytes.fromhex(data['hex']); assert len(raw) == length*4
    (temp/'gaussian.f32').write_bytes(raw)
    return raw, {'trace_sha256': public.sha(run.stdout), 'raw_sha256': report['raw_pixel_sha256'],
                 'witness_count': 1, 'guards_intact': True, 'truncated': False}


def tables(worker, parent, temp, capture, binaries):
    seed = next(r for r in capture['rows'] if r['matrix'] == 'getters' and r['row_index'] == 27)
    harness = public.initial.HARNESS
    try:
        public.initial.HARNESS = Path(__file__).with_name('radialblur_rotation_fade_sdk_harness_20261001.cpp')
        helpers = {name: public.build(temp/('table_'+name), candidate_source(before_source()), name == 'san')
                   for name in ['o2', 'san']}
    finally:
        public.initial.HARNESS = harness
    payload = ''.join(f'{i}\n' for i in range(1, 100))
    env = dict(os.environ, ASAN_OPTIONS='detect_leaks=0:halt_on_error=1', UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
    helper_outputs = {}
    for name, binary in helpers.items():
        run = subprocess.run([str(binary)], input=payload, text=True, capture_output=True, check=True, env=env)
        assert not run.stderr
        helper_outputs[name] = [struct.pack('<%dI'%(len(line)//8), *[int(line[i:i+8], 16) for i in range(0, len(line), 8)])
                                for line in run.stdout.splitlines()]
        assert len(helper_outputs[name]) == 99
    assert helper_outputs['o2'] == helper_outputs['san']
    rows = []
    for length in range(1, 100):
        case = copy.deepcopy(seed); next(q for q in case['parameters'] if q['slot'] == 7)['value'] = length+1
        case = {k: case[k] for k in ['family', 'geometry', 'depth', 'pattern', 'state', 'parameters', 'input_sha256']}
        directory = temp/f'table_{length}'; directory.mkdir()
        raw, frame, _, close, _ = public.native_render(parent, directory, case)
        assert not frame['render_error'] and frame['output']['guards_intact']
        assert close['session_clean'] and not close['unsupported_suite_calls']
        case['reference_raw_sha256'] = public.sha(raw)
        native, trace = table_trace(worker, directory, case, length)
        candidate, math_record = model(length)
        assert helper_outputs['o2'][length-1] == candidate
        vector_end = (length & ~3)*4
        vector = fields.compare_words(native[:vector_end], candidate[:vector_end])
        scalar = fields.compare_words(native[vector_end:], candidate[vector_end:])
        assert vector['different_words'] == 0
        results = {}
        for name, binary in binaries.items():
            for command in ['classic', 'smart']:
                error, rendered, metadata = public.mac_render(binary, temp, case, command, env)
                assert not error
                result = {'error': error, 'raw_sha256': public.sha(rendered), 'raw_exact': rendered == raw, 'metadata': metadata}
                if name == 'o2': results[command] = result
                else: assert result == results[command]
        rows.append({'length': length, 'case': case, 'math': math_record, 'vector_comparison': vector,
                     'scalar_comparison': scalar, 'trace': trace, 'public_results': results})
        if scalar['different_words'] or length % 20 == 0:
            print('FADE_TABLE', length, 'VECTOR', vector['different_words'], 'SCALAR', scalar['different_words'], flush=True)
    return rows


def natural(worker, temp, capture, source, candidate):
    hp = temp/'planes.cpp'; hp.write_text(fields.plane_harness()); harness = public.initial.HARNESS
    try:
        public.initial.HARNESS = hp
        binaries = {'before': public.build(temp/'before_planes', source), 'candidate': public.build(temp/'candidate_planes', candidate)}
    finally:
        public.initial.HARNESS = harness
    result = []
    for index in [27, 28]:
        case = next(r for r in capture['rows'] if r['matrix'] == 'getters' and r['row_index'] == index)
        directory = temp/f'natural_{index}'; directory.mkdir()
        native, trace = neutral.trace(worker, directory, case)
        comparisons, raw_hashes, dimensions = {}, {}, {}
        for name, binary in binaries.items():
            plane_dir = directory/name; plane_dir.mkdir()
            error, raw, _ = public.mac_render(binary, directory, case, 'classic', dict(os.environ, ROTATION_PLANES_DIRECTORY=str(plane_dir)))
            assert not error; raw_hashes[name] = public.sha(raw)
            if name == 'before': assert raw_hashes[name] == case['results']['classic']['raw_sha256']
            dimensions[name] = list(struct.unpack('<2i', (plane_dir/'dimensions.i32').read_bytes()))
            comparisons[name] = {nm: fields.compare_words(data, (plane_dir/f'{nm}.f32').read_bytes()[:len(data)]) for nm, data in native.items()}
        assert all(q['different_words'] == 0 for q in comparisons['candidate'].values())
        assert raw_hashes['candidate'] == case['reference_raw_sha256']
        result.append({'case': case, 'trace': trace, 'mac_dimensions': dimensions, 'field_comparisons': comparisons,
                       'mac_raw_sha256': raw_hashes, 'candidate_raw_exact': True})
        print('FADE_NATURAL', index, {nm: q['different_words'] for nm, q in comparisons['before'].items()}, flush=True)
    return result


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--worker', type=Path, required=True); ap.add_argument('--parent-worker', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True); ap.add_argument('--report', type=Path, required=True)
    args = ap.parse_args(); args.output.mkdir(exist_ok=False, parents=True)
    capture = json.loads(BEFORE.read_text()); source = before_source(); candidate = candidate_source(source)
    start_source_sha = public.sha(public.SOURCE.read_bytes())
    build = json.loads((public.ROOT/'reports/radialblur_readonly_windows_reference_build_20261001.json').read_text())
    assert public.sha(args.worker.read_bytes()) == build['worker_sha256']
    assert public.sha(args.parent_worker.read_bytes()) == capture['controlled_worker_sha256']
    assert public.sha(public.initial.AEX.read_bytes()) == capture['aex_sha256']
    witnesses = natural(args.worker, args.output, capture, source, candidate)
    binaries = {'o2': public.build(args.output/'o2', candidate), 'san': public.build(args.output/'san', candidate, True)}
    table_rows = tables(args.worker, args.parent_worker, args.output, capture, binaries)
    env = dict(os.environ, ASAN_OPTIONS='detect_leaks=0:halt_on_error=1', UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
    rows = []
    for index, case in enumerate(capture['rows']):
        results = {}
        for name, binary in binaries.items():
            for command in ['classic', 'smart']:
                error, raw, metadata = public.mac_render(binary, args.output, case, command, env)
                old = case['results'][command]; assert error == old['error'] and metadata == old['metadata']
                result = {'error': error, 'raw_sha256': public.sha(raw) if not error else None,
                          'raw_exact': not error and public.sha(raw) == case['reference_raw_sha256'], 'metadata': metadata,
                          'before_raw_exact': old['raw_exact'], 'before_raw_unchanged': (public.sha(raw) if not error else None) == old['raw_sha256']}
                if name == 'o2': results[command] = result
                else: assert result == results[command]
        row = {k: copy.deepcopy(case[k]) for k in ['family', 'geometry', 'depth', 'pattern', 'state', 'parameters', 'group', 'matrix', 'row_index',
                                                 'input_sha256', 'reference_raw_sha256', 'parent_raw_sha256']}
        row['results'] = results; rows.append(row)
        if (index+1) % 128 == 0: print('FADE_PUBLIC', index+1, flush=True)
    assert public.sha(public.SOURCE.read_bytes()) == start_source_sha
    summary = writer.summarize(rows); assert summary['lost_exact'] == 0
    import pefile
    report = {'schema': 'radialblur.rotation-fade-public/1', 'before_revision': BEFORE_REVISION,
              'source_before_sha256': capture['source_sha256'], 'source_sha256': public.sha(candidate.encode()),
              'header_sha256': capture['header_sha256'], 'aex_sha256': capture['aex_sha256'],
              'controlled_worker_sha256': capture['controlled_worker_sha256'], 'window_worker_sha256': build['worker_sha256'],
              'probe_start_source_sha256': start_source_sha, 'production_source_changed_during_probe': False,
              'b680_code_sha256': public.sha(pefile.PE(str(public.initial.AEX)).get_data(0xb680, 0x135)),
              'summary': summary, 'rows': rows, 'natural_witnesses': witnesses, 'fade_tables': table_rows,
              'matrix_summaries': {m: writer.summarize([r for r in rows if r['matrix'] == m]) for m in capture['matrix_summaries']},
              'public_replay_count': len(rows)*4, 'table_public_replay_count': len(table_rows)*4, 'table_sdk_replay_count': len(table_rows)*2,
              'table_summary': {'length_count': 99, 'vector_words': sum(r['math']['vector_word_count'] for r in table_rows),
                                'scalar_words': sum(r['math']['scalar_word_count'] for r in table_rows),
                                'vector_different_words': sum(r['vector_comparison']['different_words'] for r in table_rows),
                                'scalar_different_words': sum(r['scalar_comparison']['different_words'] for r in table_rows),
                                'public_both_commands_exact': sum(all(q['raw_exact'] for q in r['public_results'].values()) for r in table_rows)},
              'dependencies_sha256': {str(p.relative_to(public.ROOT)): public.sha(p.read_bytes()) for p in
                                      [Path(__file__), Path(__file__).with_name('radialblur_rotation_fade_sdk_harness_20261001.cpp'), BEFORE,
                                       public.SOURCE.with_suffix('.h'), public.initial.HARNESS]},
              'claims_not_made': ['The controlled worker uses host expf, not a general native Windows UCRT implementation.',
                                 'Scalar tails differing from host expf are retained unresolved; no reference or scalar policy is changed to fit them.',
                                 'Native Windows RCPPS approximation and ISA selection remain unverified.',
                                 'The extra Mac radius row is excluded from native owned plane comparisons.',
                                 'Finite fade/source/geometry checks do not prove all combinations, inputs, Quality, Size/Noise, Zoom, native AE/UI/save/ROI/downsample or all-ten completion.']}
    args.report.write_text(json.dumps(report, sort_keys=True, indent=2)+'\n')
    print('FADE_DONE', summary, report['table_summary'], flush=True)


if __name__ == '__main__':
    main()
