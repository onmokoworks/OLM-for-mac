#!/usr/bin/env python3
"""Natural public samples and unchanged field distinguish the PF8 writer bug."""
import argparse
import copy
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import tempfile

import pefile
from PIL import Image
import probe_radialblur_public_aligned_20261001 as public
import probe_radialblur_doublecast_reference_20261001 as reference

CAPTURE = public.ROOT/'reports/radialblur_doublecast_reference_public_20261001.json'


def candidate_source(source):
    start = source.index('\tstatic void WriteZoom(PF_Pixel8 &pixel')
    end = source.index('\n\t}\n};', start)+len('\n\t}')
    assert 'const double rgb_epsilon = use_fft ? 0.0 : 1.0e-4;' in source
    replacement = '''\tstatic void WriteZoom(PF_Pixel8 &pixel, const RadialBlurOuterSampleState &state, bool)
\t{
\t\t// The public PF8 owner applies MINSS 1.0 to brightness-scaled RGB,
\t\t// then FUN_180017400 uses MULSS 255 and CVTTSS2SI, storing low bytes.
\t\t// No epsilon or DOUBLE multiplication occurs; alpha is not saturated.
\t\tauto store_rgb = [](float value) -> A_u_char {
\t\t\tconst float saturated = value < 1.0f ? value : 1.0f;
\t\t\treturn (A_u_char)RadialCVTTSS2SI(RadialF32Mul(saturated, 255.0f));
\t\t};
\t\tpixel.red = store_rgb(state.final_rgb[0]);
\t\tpixel.green = store_rgb(state.final_rgb[1]);
\t\tpixel.blue = store_rgb(state.final_rgb[2]);
\t\tpixel.alpha = (A_u_char)RadialCVTTSS2SI(RadialF32Mul(state.alpha, 255.0f));
\t}'''
    return source[:start]+replacement+source[end:]


def summarize(rows):
    return {'case_count': len(rows),
            'both_commands_exact': sum(all(x['raw_exact'] for x in r['results'].values()) for r in rows),
            'different': sum(not r['results']['classic']['error'] and not r['results']['classic']['raw_exact'] for r in rows),
            'mac_rejected': sum(bool(r['results']['classic']['error']) for r in rows),
            'became_exact': sum(not r['results']['classic']['before_raw_exact'] and r['results']['classic']['raw_exact'] for r in rows),
            'lost_exact': sum(r['results']['classic']['before_raw_exact'] and not r['results']['classic']['raw_exact'] for r in rows),
            'raw_changed': sum(not r['results']['classic']['before_raw_unchanged'] for r in rows)}


def natural_witnesses(worker, temp, capture, before_binary, after_binary):
    witnesses = []
    for geometry in [[23, 13], [31, 19]]:
        for noise in [25, 100]:
            case = next(r for r in capture['rows'] if r['group'] == 'independent'
                        and r['family'] == 1 and r['depth'] == 8 and r['geometry'] == geometry
                        and next(p['value'] for p in r['parameters'] if p['slot'] == 24) == noise
                        and next(p['value'] for p in r['parameters'] if p['slot'] == 28) == 0)
            width, height = geometry
            native, frame, _, close, _ = public.native_render(worker, temp, case)
            assert close['session_clean'] and not close['unsupported_suite_calls']
            assert public.sha(native) == case['reference_raw_sha256']
            error, before, _ = public.mac_render(before_binary, temp, case, 'classic')
            assert not error and public.sha(before) == case['results']['classic']['raw_sha256']
            differences = sorted({i//4 for i, (a, b) in enumerate(zip(before, native)) if a != b})
            points = [(i%width, i//width) for i in differences[:4]] if differences else [
                (0, 0), (width//2, height//2), (width-1, height-1), (width-2, height-2)]
            debug_path = temp/'debug.txt'
            debug_path.unlink(missing_ok=True)
            env = dict(os.environ, OLMRADIALBLUR_DEBUG_DUMP_PATH=str(debug_path),
                       OLMRADIALBLUR_DEBUG_POINTS=';'.join(f'{x},{y}' for x, y in points))
            _, before_debug, _ = public.mac_render(before_binary, temp, case, 'classic', env)
            assert before_debug == before
            mac_samples = {}
            for line in debug_path.read_text().splitlines():
                if not line.startswith('OLMRADIALBLUR_DEBUG_POINT kind=zoom '): continue
                x, y = map(int, re.search(r' x=(\d+) y=(\d+) ', line).groups())
                rgba = [float.fromhex(v) for v in re.search(r'sample_rgba_hex=\(([^)]+)\)', line)[1].split(',')]
                mac_samples[(x, y)] = struct.pack('<4f', *rgba)
            image = Image.new('RGBA', (width, height))
            image.putdata([(r, g, b, a) for a, r, g, b in public.initial.pixels(width, height, 'opaque')])
            ip = temp/'input.png'; image.save(ip)
            assignments = [f"param_{p['slot']}@{p['slot']}"+(':angle' if p['kind'] == 'a' else '')+'='+
                           (','.join(map(str, p['value'])) if isinstance(p['value'], list) else str(p['value']))
                           for p in public.native_case(case)['parameters']]
            watches = []
            for x, y in points:
                occurrence = y*width+x+1
                watches += ['--watch', f'function=0x9d80,arg=rdx,size=16,occurrence={occurrence}',
                            '--watch', f'function=0x17400,arg=stack5,size=4,occurrence={occurrence}']
            run = subprocess.run([str(worker), 'render-trace-png', str(public.initial.AEX), str(ip),
                                  str(temp/'native.png'), '--pixel-format', 'argb8', *watches, *assignments],
                                 check=True, capture_output=True)
            trace = json.loads(run.stdout)
            assert trace['raw_pixel_sha256'] == public.sha(native)
            assert trace['render_error'] == 0 and trace['guards_intact']
            assert not trace['unsupported_suite_calls'] and not trace['dropped_unsupported_suite_calls']
            smart = next(t for t in trace['execution_traces'] if t['selector'] == 'SMART_RENDER')
            assert not smart['truncated'] and not smart['dropped_memory_witnesses']
            ws = smart['memory_witnesses']
            _, after, _ = public.mac_render(after_binary, temp, case, 'classic')
            assert after == native
            selected = []
            for index, (x, y) in enumerate(points):
                sample = next(w for w in ws if w['watch_id'] == f'watch-{index*2+1}')
                writer = next(w for w in ws if w['watch_id'] == f'watch-{index*2+2}')
                sample_bytes = bytes.fromhex(sample['after']['hex'])
                assert sample_bytes == mac_samples[(x, y)]
                off = (y*width+x)*4
                assert writer['after']['hex'] == native[off:off+4].hex()
                assert sample['pc_rva'] == 0x5e68 and writer['pc_rva'] == 0x7c14
                selected.append({'coordinate': [x, y], 'native_sample_rgba_f32_le_hex': sample_bytes.hex(),
                                 'before_mac_sample_rgba_f32_le_hex': mac_samples[(x, y)].hex(),
                                 'before_argb8_hex': before[off:off+4].hex(),
                                 'native_writer_argb8_hex': writer['after']['hex'],
                                 'after_argb8_hex': after[off:off+4].hex()})
            witnesses.append({'geometry': geometry, 'noise_variation': noise, 'parameters': case['parameters'],
                              'input_sha256': case['input_sha256'], 'before_raw_sha256': public.sha(before),
                              'native_raw_sha256': public.sha(native), 'after_raw_sha256': public.sha(after),
                              'before_different_bytes': sum(a != b for a, b in zip(before, native)),
                              'trace_typed_resident_raw_exact': True, 'trace_sha256': public.sha(run.stdout),
                              'selected_points': selected})
    return witnesses


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--before-source', type=Path, required=True)
    ap.add_argument('--worker', type=Path, required=True)
    ap.add_argument('--report', type=Path, required=True)
    args = ap.parse_args()
    capture = json.loads(CAPTURE.read_text())
    source = args.before_source.read_text()
    assert public.sha(source.encode()) == capture['source_sha256']
    assert public.sha(public.SOURCE.read_bytes()) == capture['source_sha256']
    assert public.sha(args.worker.read_bytes()) == capture['worker_sha256']
    assert public.sha(public.initial.AEX.read_bytes()) == capture['aex_sha256']
    candidate = candidate_source(source)
    pe = pefile.PE(str(public.initial.AEX))
    assert pe.get_data(0x252a0, 4) == struct.pack('<f', 255.0)
    assert pe.get_data(0x212d4, 4) == struct.pack('<f', 1.0)
    env = dict(os.environ, ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',
               UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
    rows = []
    with tempfile.TemporaryDirectory(prefix='radial_pf8_writer_probe_') as directory:
        temp = Path(directory)
        before_binary = public.build(temp/'before', source)
        binaries = {'o2': public.build(temp/'o2', candidate),
                    'sanitizer': public.build(temp/'san', candidate, sanitize=True)}
        witnesses = natural_witnesses(args.worker, temp, capture, before_binary, binaries['o2'])
        for index, case in enumerate(capture['rows']):
            results = {}
            for build, binary in binaries.items():
                for command in ['classic', 'smart']:
                    error, raw, metadata = public.mac_render(binary, temp, case, command, env)
                    before = case['results'][command]
                    assert error == before['error'] and metadata == before['metadata']
                    result = {'error': error, 'raw_sha256': public.sha(raw) if not error else None,
                              'raw_exact': not error and public.sha(raw) == case['reference_raw_sha256'],
                              'before_raw_exact': before['raw_exact'], 'metadata': metadata,
                              'before_raw_unchanged': (public.sha(raw) if not error else None) == before['raw_sha256']}
                    if build == 'o2': results[command] = result
                    else: assert result == results[command], (index, command)
            row = {k: copy.deepcopy(case[k]) for k in ['family', 'geometry', 'depth', 'pattern', 'state', 'parameters',
                   'group', 'matrix', 'row_index', 'input_sha256', 'reference_raw_sha256', 'parent_raw_sha256']}
            row['results'] = results
            rows.append(row)
            if (index+1) % 64 == 0: print('PF8_WRITER_PUBLIC', index+1, flush=True)
    assert public.sha(public.SOURCE.read_bytes()) == capture['source_sha256']
    deps = [Path(__file__), CAPTURE, public.SOURCE.with_suffix('.h'), Path(public.__file__),
            Path(public.initial.__file__), public.initial.HARNESS, public.ROOT/'core/dblur_noise.h']
    report = {'schema': 'radialblur.pf8-writer-public/1', 'source_before_sha256': capture['source_sha256'],
              'source_sha256': public.sha(candidate.encode()), 'header_sha256': public.sha(public.SOURCE.with_suffix('.h').read_bytes()),
              'reference_capture_sha256': public.sha(CAPTURE.read_bytes()), 'aex_sha256': capture['aex_sha256'],
              'controlled_worker_sha256': capture['worker_sha256'], 'rows': rows, 'summary': summarize(rows),
              'matrix_summaries': {m: summarize([r for r in rows if r['matrix'] == m]) for m in capture['matrix_summaries']},
              'public_replay_count': 4*len(rows), 'builds': ['o2', 'asan-ubsan-strict-halt'],
              'natural_public_witnesses': witnesses, 'natural_trace_count': len(witnesses),
              'native_writer_rva': '0x17400', 'native_writer_bytes_sha256': public.sha(pe.get_data(0x17400, 0x39)),
              'native_owner_rgb_min_rva': '0x7bdd', 'native_owner_rgb_min_bytes_sha256': public.sha(pe.get_data(0x7bdd, 0x1e)),
              'dependencies_sha256': {str(p.relative_to(public.ROOT)): public.sha(p.read_bytes()) for p in deps},
              'claims_not_made': ['Controlled reference math is not arbitrary Windows UCRT proof.',
                                 'Remaining Rotation/Zoom field differences and 84 rejected cases are not closed.',
                                 'No full settings/input/UI/save/native AE/installed/ROI/downsample/all-ten completion.']}
    args.report.write_text(json.dumps(report, sort_keys=True, indent=2)+'\n')
    print('PF8_WRITER_DONE', report['summary'], flush=True)


if __name__ == '__main__':
    main()
