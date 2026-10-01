#!/usr/bin/env python3
"""Compare natural Rotation planes and a disposable SIMD Gaussian reconstruction.

The original AEX, parent references and production source are never modified.
Private binary planes stay in the caller's output directory; reports contain
only hashes, counts and scalar witnesses. The candidate is not installed.
"""
import argparse
import copy
import json
import math
import os
from pathlib import Path
import struct
import subprocess

import pefile
from PIL import Image
import probe_radialblur_public_aligned_20261001 as public
from aex_loader import AexLoader

CAPTURE = public.ROOT/'reports/radialblur_pf8_writer_public_20261001.json'
BUILD = public.ROOT/'reports/radialblur_readonly_windows_reference_build_20261001.json'
PLANES = [('polar', 0x2780, 'rdx', None, 27000*16),
          ('scalar', 0x2780, 'rcx', 0x40, 27000*4),
          ('normalized', 0x1000, 'rcx', None, 27000*16),
          ('span', 0x4640, 'rdx', 0x90, 299*4),
          ('accum', 0x1b10, 'rcx', 0x3c940, 27000*16),
          ('max', 0x1b10, 'rcx', 0x3c948, 27000*4),
          ('gaussian', 0xb680, 'rcx', None, 30000*4)]


def f32(x):
    return struct.unpack('<f', struct.pack('<f', x))[0]


def bits(x):
    return struct.unpack('<I', struct.pack('<f', x))[0]


def value(x):
    return struct.unpack('<f', struct.pack('<I', x & 0xffffffff))[0]


def mantissas():
    return [bits(f32(2**(i/64))) & 0x7fffff for i in range(64)]


def simd_exp(x):
    """Scalar transcription of AEX 1ebc0's ordinary Gaussian argument branch."""
    assert -4.5 <= x <= 0
    n = round(f32(x*f32(92.33248138427734)))
    r = f32(f32(x-f32(f32(n)*f32(.01082611083984375)))-
            f32(f32(n)*f32(.000004313856607041089)))
    polynomial = f32(f32(f32(r+r)+2.0)+f32(r*r))
    scale = value((((8064+n) & 0xffffffff) >> 6 << 23) | mantissas()[n & 63])
    return f32(polynomial*scale)


def exponents():
    denominator = f32(f32(f32(30000)*f32(30000))*f32(.111111119389534))
    denominator = f32(f32(denominator+denominator)+1e-5)
    inverse = f32(1/denominator)
    # Unicorn's RCPPS is exact f32 division; original AEX then refines it.
    refined = f32(f32(inverse+inverse)-f32(f32(inverse*inverse)*denominator))
    return [f32(f32(-i*i)*refined) for i in range(30000)], denominator, inverse, refined


def candidate_source(source):
    table = ', '.join(f'0x{x:06x}u' for x in mantissas())
    helper = '''// Disposable diagnostic: AEX 1ebc0 Gaussian-domain polynomial.
// Native Windows RCPPS/ISA selection still requires independent verification.
static float RotationGaussianSIMDExp(float exponent)
{
    static constexpr unsigned mantissa[64] = {TABLE};
    const float scaled = RadialF32Mul(exponent, 92.33248138427734f);
    const float lower = std::floor(scaled);
    const float fraction = RadialF32Sub(scaled, lower);
    int n = (int)lower;
    if (fraction > 0.5f || (fraction == 0.5f && (n & 1))) ++n;
    float r = RadialF32Sub(exponent, RadialF32Mul((float)n, .01082611083984375f));
    r = RadialF32Sub(r, RadialF32Mul((float)n, .000004313856607041089f));
    const float polynomial = RadialF32Add(RadialF32Add(RadialF32Add(r, r), 2.0f), RadialF32Mul(r, r));
    const unsigned scale_bits = (((unsigned)(8064+n) >> 6) << 23) | mantissa[n & 63];
    float scale; std::memcpy(&scale, &scale_bits, sizeof(scale));
    return RadialF32Mul(polynomial, scale);
}

'''.replace('TABLE', table)
    marker = 'static std::vector<float> RotationGaussianWeights('
    assert source.count(marker) == 1
    source = source.replace(marker, helper+marker)
    old = 'weights[(size_t)i] = (float)std::exp((double)exponent);'
    start = source.index(marker)
    end = source.index('static A_long ZoomEffectiveLength', start)
    body = source[start:end]
    assert body.count(old) == 1
    return source[:start]+body.replace(old, 'weights[(size_t)i] = RotationGaussianSIMDExp(exponent);')+source[end:]


def plane_harness():
    harness = '#define OLM_RADIALBLUR_TEST_SEAM 1\n'+public.initial.HARNESS.read_text()
    setup = '''const size_t cap_cells=100000;
    std::vector<float> capture_polar(cap_cells*4),capture_scalar(cap_cells),capture_accum(cap_cells*4),capture_max(cap_cells),capture_normalized(cap_cells*4),capture_span(w*h),capture_prepass(cap_cells),capture_final(w*h*4),capture_coordinates(w*h*2);
    std::vector<A_u_char> capture_eligible(cap_cells);
    RadialBlurTestRotationCapture capture{};capture.polar_rgba=capture_polar.data();capture.eligibility=capture_eligible.data();capture.source_scalar=capture_scalar.data();capture.accum_rgba=capture_accum.data();capture.max_alpha=capture_max.data();capture.normalized_rgba=capture_normalized.data();capture.source_span=capture_span.data();capture.prepass_alpha=capture_prepass.data();capture.final_rgba=capture_final.data();capture.final_coordinates=capture_coordinates.data();capture.capacity_cells=cap_cells;capture.capacity_output_pixels=w*h;g_rotation_test_capture=&capture;
    PF_Err error=0;'''
    post = '''g_rotation_test_capture=nullptr;
    const char* dir=getenv("ROTATION_PLANES_DIRECTORY");
    if(dir&&capture.written_cells){
      auto dump=[&](const char* name,const void* data,size_t size){std::ofstream f(std::string(dir)+"/"+name,std::ios::binary);f.write((const char*)data,size);};
      size_t cells=capture.written_cells;
      dump("polar.f32",capture_polar.data(),cells*16);dump("scalar.f32",capture_scalar.data(),cells*4);dump("accum.f32",capture_accum.data(),cells*16);dump("max.f32",capture_max.data(),cells*4);dump("normalized.f32",capture_normalized.data(),cells*16);dump("span.f32",capture_span.data(),w*h*4);dump("eligible.u8",capture_eligible.data(),cells);dump("coordinates.f32",capture_coordinates.data(),w*h*8);dump("final.f32",capture_final.data(),w*h*16);
      int dimensions[2]={(int)capture.width,(int)capture.height};dump("dimensions.i32",dimensions,8);
    }
    if(a!=before)return 67;'''
    assert harness.count('PF_Err error=0;') == harness.count('if(a!=before)return 67;') == 1
    return harness.replace('PF_Err error=0;', setup).replace('if(a!=before)return 67;', post)


def compare_words(native, mac):
    assert len(native) == len(mac) and len(native) % 4 == 0
    different = [i//4 for i in range(0, len(native), 4) if native[i:i+4] != mac[i:i+4]]
    return {'word_count': len(native)//4, 'different_words': len(different),
            'native_sha256': public.sha(native), 'mac_sha256': public.sha(mac),
            'first_differences': [{'word': i, 'native_f32_le_hex': native[i*4:i*4+4].hex(),
                                   'mac_f32_le_hex': mac[i*4:i*4+4].hex()} for i in different[:8]]}


def trace_planes(worker, temp, case):
    w, h = case['geometry']
    image = Image.new('RGBA', (w, h))
    image.putdata([(r, g, b, a) for a, r, g, b in public.initial.pixels(w, h, case['pattern'])])
    image.save(temp/'input.png')
    assignments = [f"param_{q['slot']}@{q['slot']}"+(':angle' if q['kind'] == 'a' else '')+'='+
                   (','.join(map(str, q['value'])) if isinstance(q['value'], list) else str(q['value']))
                   for q in public.native_case(case)['parameters']]
    watches, windows = [], []
    for name, rva, register, deref, size in PLANES:
        for offset in range(0, size, 4096):
            length = min(4096, size-offset)
            spec = f'function={hex(rva)},arg={register},size={length},offset={offset},occurrence=1'
            if deref is not None: spec += f',deref={hex(deref)}'
            watches += ['--watch', spec]; windows.append((name, offset, length))
    # This is a real direct call from B680, including when its dispatcher tail-jumps.
    watches += ['--watch', 'function=0x1d0e0,arg=rcx,size=4,occurrence=1']
    run = subprocess.run([str(worker), 'render-trace-png', str(public.initial.AEX), str(temp/'input.png'),
                          str(temp/'native.png'), '--pixel-format', 'argb32f', *watches, *assignments],
                         capture_output=True, check=True)
    (temp/'native_trace.json').write_bytes(run.stdout)
    report = json.loads(run.stdout)
    assert report['raw_pixel_sha256'] == case['reference_raw_sha256']
    assert report['render_error'] == 0 and report['guards_intact']
    assert not report['unsupported_suite_calls'] and not report['dropped_unsupported_suite_calls']
    trace = next(t for t in report['execution_traces'] if t['selector'] == 'SMART_RENDER')
    assert not trace['truncated'] and not trace['dropped_memory_witnesses']
    assert not trace['trace_configuration']['unhookable_watches']
    witnesses = {w['watch_id']: w for w in trace['memory_witnesses']}
    assert len(witnesses) == len(windows)+1
    planes = {}
    for name, *_ in PLANES:
        parts = []
        for i, (nm, offset, size) in enumerate(windows):
            if nm != name: continue
            witness = witnesses[f'watch-{i+1}']
            data = witness['after' if name == 'gaussian' else 'before']
            assert data['status'] == 'captured'
            raw = bytes.fromhex(data['hex']); assert len(raw) == size
            parts.append(raw)
        planes[name] = b''.join(parts)
        (temp/f'native_{name}.f32').write_bytes(planes[name])
    return planes, {'trace_sha256': public.sha(run.stdout), 'window_count': len(windows),
                    'witness_count': len(witnesses), 'simd_dispatcher_observed': True,
                    'raw_sha256': report['raw_pixel_sha256'], 'guards_intact': True,
                    'truncated': False, 'unsupported_suite_calls': []}


def leaf_probe():
    pe = pefile.PE(str(public.initial.AEX))
    encoded = b''.join(struct.pack('<Q', n) for n in mantissas())
    assert encoded == pe.get_data(0x2f400, 64*8)
    xs, denominator, inverse, refined = exponents()
    loader = AexLoader(str(public.initial.AEX), verbose=False, fast=False)
    observed = bytearray()
    for i in range(0, len(xs), 4):
        result = loader.call_function(loader.image_base+0x1ebc0,
                                      float_args={0: struct.pack('<4f', *xs[i:i+4])}, max_instructions=500)
        assert not loader.import_log
        observed.extend(result['xmm0'])
    model = b''.join(struct.pack('<f', simd_exp(x)) for x in xs)
    assert observed == model
    return model, {'argument_count': len(xs), 'vector_calls': len(xs)//4,
                   'import_calls': 0, 'rva': '0x1ebc0', 'model_sha256': public.sha(model),
                   'arguments_sha256': public.sha(b''.join(struct.pack('<f', x) for x in xs)),
                   'code_sha256': public.sha(pe.get_data(0x1ebc0, 0xbc)),
                   'mantissa_table_sha256': public.sha(encoded),
                   'denominator_bits': hex(bits(denominator)), 'div_inverse_bits': hex(bits(inverse)),
                   'controlled_rcpps_newton_bits': hex(bits(refined)),
                   'native_windows_rcpps_verified': False}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--worker', type=Path, required=True)
    ap.add_argument('--parent-worker', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--report', type=Path, required=True)
    args = ap.parse_args(); args.output.mkdir(parents=True, exist_ok=False)
    source = public.SOURCE.read_text(); source_hash = public.sha(source.encode())
    capture = json.loads(CAPTURE.read_text()); build = json.loads(BUILD.read_text())
    assert source_hash == capture['source_sha256']
    assert public.sha(args.worker.read_bytes()) == build['worker_sha256']
    assert public.sha(args.parent_worker.read_bytes()) == build['parent_worker_sha256']
    assert public.sha(public.initial.AEX.read_bytes()) == capture['aex_sha256']
    case = next(r for r in capture['rows'] if r['group'] == 'independent' and r['family'] == 2
                and r['depth'] == 32 and r['geometry'] == [23, 13] and r['row_index'] == 160)
    temp = args.output; candidate = candidate_source(source)
    (temp/'candidate.cpp').write_text(candidate)
    hp = temp/'planes_harness.cpp'; hp.write_text(plane_harness()); old_harness = public.initial.HARNESS
    env = dict(os.environ, ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',
               UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
    binaries, fields, results = {}, {}, {}
    try:
        public.initial.HARNESS = hp
        for name, code, sanitize in [('before', source, False), ('candidate', candidate, False),
                                      ('candidate_san', candidate, True)]:
            binaries[name] = public.build(temp/name, code, sanitize=sanitize)
            directory = temp/f'{name}_planes'; directory.mkdir()
            error, raw, metadata = public.mac_render(binaries[name], temp, case, 'classic',
                                      dict(env, ROTATION_PLANES_DIRECTORY=str(directory)))
            assert not error
            if name == 'before': assert public.sha(raw) == case['results']['classic']['raw_sha256']
            fields[name] = {nm: (directory/f'{nm}.f32').read_bytes()[:size]
                            for nm, _, _, _, size in PLANES if nm != 'gaussian'}
            results[name] = {'raw_sha256': public.sha(raw), 'metadata': metadata,
                             'dimensions': list(struct.unpack('<2i', (directory/'dimensions.i32').read_bytes()))}
    finally:
        public.initial.HARNESS = old_harness
    assert fields['candidate_san'] == fields['candidate'] and results['candidate_san'] == results['candidate']
    native, trace = trace_planes(args.worker, temp, case)
    parent_raw, _, _, close, _ = public.native_render(args.parent_worker, temp, case)
    window_raw, _, _, close_window, _ = public.native_render(args.worker, temp, case)
    assert close['session_clean'] and close_window['session_clean']
    assert public.sha(parent_raw) == public.sha(window_raw) == case['reference_raw_sha256']
    model, leaf = leaf_probe(); assert model == native['gaussian']
    xs, *_ = exponents()
    old_model = b''.join(struct.pack('<f', math.exp(x)) for x in xs)
    comparisons = {name: {nm: compare_words(native[nm], data) for nm, data in planes.items()}
                   for name, planes in fields.items()}
    assert all(r['different_words'] == 0 for r in comparisons['candidate'].values())
    print('ROTATION_FIELDS', {name: {k: v['different_words'] for k, v in group.items()}
                              for name, group in comparisons.items()}, flush=True)
    rows = []
    for index, row in enumerate(capture['rows']):
        replay = {}
        for name in ['candidate', 'candidate_san']:
            for command in ['classic', 'smart']:
                error, raw, metadata = public.mac_render(binaries[name], temp, row, command, env)
                before = row['results'][command]
                assert error == before['error'] and metadata == before['metadata']
                result = {'error': error, 'raw_sha256': public.sha(raw) if not error else None,
                          'raw_exact': not error and public.sha(raw) == row['reference_raw_sha256'],
                          'before_raw_exact': before['raw_exact'],
                          'before_raw_unchanged': (public.sha(raw) if not error else None) == before['raw_sha256']}
                if name == 'candidate': replay[command] = result
                else: assert result == replay[command]
        rows.append({k: copy.deepcopy(row[k]) for k in ['group', 'matrix', 'row_index', 'family', 'depth',
                    'geometry', 'pattern', 'state', 'parameters', 'input_sha256', 'reference_raw_sha256']} |
                    {'results': replay})
        if (index+1) % 128 == 0: print('ROTATION_CANDIDATE_PUBLIC', index+1, flush=True)
    assert public.sha(public.SOURCE.read_bytes()) == source_hash
    report = {'schema': 'radialblur.rotation-fields/1', 'source_sha256': source_hash,
              'production_source_changed': False, 'candidate_source_sha256': public.sha(candidate.encode()),
              'aex_sha256': capture['aex_sha256'], 'worker_sha256': build['worker_sha256'],
              'parent_worker_sha256': build['parent_worker_sha256'], 'natural_case': case,
              'native_dimensions': [1800, 15], 'mac_dimensions': results['before']['dimensions'],
              'native_owned_rows_only': True, 'field_comparisons': comparisons, 'natural_results': results,
              'trace': trace, 'parent_and_window_resident_raw_exact': True, 'scalar_leaf': leaf,
              'gaussian_scalar_double_exp_comparison': compare_words(native['gaussian'], old_model),
              'gaussian_simd_model_exact': True, 'rows': rows, 'public_replay_count': len(rows)*4,
              'candidate_summary': {'case_count': len(rows),
                  'both_commands_exact': sum(all(x['raw_exact'] for x in r['results'].values()) for r in rows),
                  'became_exact': sum(not r['results']['classic']['before_raw_exact'] and r['results']['classic']['raw_exact'] for r in rows),
                  'lost_exact': sum(r['results']['classic']['before_raw_exact'] and not r['results']['classic']['raw_exact'] for r in rows),
                  'raw_changed': sum(not r['results']['classic']['before_raw_unchanged'] for r in rows)},
              'dependencies_sha256': {str(p.relative_to(public.ROOT)): public.sha(p.read_bytes()) for p in
                  [Path(__file__), CAPTURE, BUILD, public.SOURCE.with_suffix('.h'), public.initial.HARNESS,
                   Path(public.__file__), Path(public.initial.__file__)]},
              'claims_not_made': ['Candidate is a diagnostic copy, not a production/plugin installation.',
                                 'Full finite natural planes do not prove arbitrary settings or geometry.',
                                 'Unicorn RCPPS exact division does not prove Windows CPU approximate reciprocal.',
                                 'Scalar expf and lower ISA paths remain separate unverified branches.',
                                 'Final inverse coordinates/sampling/writer and native extra-row ownership remain open.',
                                 'No native AE/UI/save/ROI/downsample or all-ten completion.']}
    args.report.write_text(json.dumps(report, sort_keys=True, indent=2)+'\n')
    print('ROTATION_FIELDS_DONE', report['candidate_summary'], flush=True)


if __name__ == '__main__':
    main()
