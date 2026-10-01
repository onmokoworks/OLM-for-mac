#!/usr/bin/env python3
"""Color/alpha and smoothing-state witnesses without injected dispatch indices."""
import argparse
import gc
import json
import os
import struct
import subprocess
import tempfile
from pathlib import Path

import probe_olmsmoother2_switch_reachability_20261001 as retained

ROOT = retained.ROOT
SOURCE = retained.SOURCE
HARNESS = Path(__file__).with_name('olmsmoother2_color_weight_harness_20261001.cpp')
PROFILES = ('colored', 'partial', 'premul', 'epsilon')
SETTINGS = ((100, 2, 0), (0, 0, 0), (1, 1, 1), (49, 2, 50), (50, 50, 49), (99, 99, 100), (100, 100, 100))
INDICES = (0, 7, 19, 27, 42, 64, 85, 111, 127, 170, 191, 204, 223, 239, 253, 255)


def fixture(index, profile):
    alpha = 255 if profile == 'colored' else 128
    center = (41, 83, 137, alpha)
    pixels = [center] * 12
    for bit, (x, y) in enumerate(retained.NEIGHBORS):
        if (index >> bit) & 1:
            continue
        if profile == 'epsilon':
            color = (center[0] + 1 + bit % 2, center[1], center[2], alpha)
        else:
            a = 255 if profile == 'colored' else (0, 64, 192, 255)[bit % 4]
            color = ((211 + bit * 7) % 256, (29 + bit * 13) % 256, (173 - bit * 11) % 256, a)
        pixels[y * 4 + x] = color
    if profile == 'premul':
        pixels = [tuple((c * p[3] + 127) // 255 for c in p[:3]) + (p[3],) for p in pixels]
    return pixels


def compile_harness(directory, body, sanitize=False):
    directory.mkdir(parents=True)
    anchor = '\tp.class_plane = class_plane.data();'
    assert body.count(anchor) == 1
    # Observe the plane produced by the real code. Do not replace class bytes.
    observer = '\n\tstd::printf("CLASS "); for (auto byte : class_plane) std::printf("%02x", byte); std::puts("");'
    (directory / 'production_under_test.cpp').write_text(body.replace(anchor, anchor + observer))
    binary = directory / 'probe'
    flags = ['-O1', '-g', '-fsanitize=address,undefined', '-fno-omit-frame-pointer'] if sanitize else ['-O2']
    subprocess.run(['clang++', '-std=c++17', *flags, '-fno-fast-math', '-ffp-contract=off',
                    '-Wno-deprecated-declarations', '-I', str(directory),
                    '-I', str(ROOT / 'cli/OLMSmoother2/shim'), '-I', str(SOURCE.parent),
                    str(HARNESS), '-o', str(binary)], check=True)
    return binary


def production(binary, case, env=None):
    pixels = fixture(case['target_index'], case['profile'])
    typed = retained.typed_input(pixels, case['depth'])
    run = subprocess.run([str(binary), '4', '3', case['depth'], str(case['version']),
                          *map(str, case['smoothing'])], input=typed, check=True,
                         capture_output=True, env=env)
    values = dict(line.split(' ', 1) for line in run.stdout.decode().splitlines())
    hist = {int(k): int(v) for k, v in (pair.split(':') for pair in values['HIST'].split(','))} if values['HIST'] else {}
    return bytes.fromhex(values['RAW']), bytes.fromhex(values['CLASS']), hist


def encoded(pixels, depth, matrix):
    if depth == 'PF8':
        inv = matrix.f32(1 / 255)
        return [tuple(matrix.f32(matrix.f32(c) * inv) for c in pixel) for pixel in pixels]
    if depth == 'PF16':
        return [tuple(matrix.f32(round(c * 32768 / 255) / 32768) for c in pixel) for pixel in pixels]
    return [tuple(matrix.f32(c / 255) for c in pixel) for pixel in pixels]


def specifications(matrix):
    if matrix == 'dispatch':
        for index in range(256):
            for profile in ('colored', 'partial'):
                yield {'target_index': index, 'profile': profile, 'depth': 'PF32', 'version': 1, 'smoothing': [100, 2, 0]}
    else:
        for index in INDICES:
            for profile in PROFILES:
                for settings in SETTINGS:
                    for version in (1, 2):
                        for depth in ('PF8', 'PF16', 'PF32'):
                            yield {'target_index': index, 'profile': profile, 'depth': depth,
                                   'version': version, 'smoothing': list(settings)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--matrix', choices=('dispatch', 'controls'), required=True)
    parser.add_argument('--limit', type=int)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    source = SOURCE.read_text()
    matrix, instances = retained.native_setup()
    rows = []
    try:
        with tempfile.TemporaryDirectory(prefix='sm2_color_weight_') as directory:
            temp = Path(directory)
            binary = compile_harness(temp / 'production', source)
            for case in specifications(args.matrix):
                if args.limit is not None and len(rows) >= args.limit:
                    break
                pixels = fixture(case['target_index'], case['profile'])
                typed = retained.typed_input(pixels, case['depth'])
                current, class_plane, hist = production(binary, case)
                native, plane, ci, wi = matrix.actual(case['depth'], case['version'], encoded(pixels, case['depth'], matrix),
                                                    matrix.DEPTHS[case['depth']][1], 4, 3, *case['smoothing'])
                audit = instances[-1]
                assert not audit.import_errors, audit.import_errors
                padding = matrix.DEPTHS[case['depth']][1]
                pixel_size = matrix.DEPTHS[case['depth']][0]
                rb = 4 * pixel_size + padding
                assert len(native) == len(current) == rb * 3
                assert all(native[y * rb + 4 * pixel_size:(y + 1) * rb] == b'\xa5' * padding for y in range(3))
                native_hist = matrix.histogram(plane, 4, 3)
                case.update(input_sha256=retained.sha(typed), native_raw_sha256=retained.sha(native),
                            production_raw_sha256=retained.sha(current), native_class_plane_sha256=retained.sha(plane),
                            production_class_plane_sha256=retained.sha(class_plane), native_histogram=native_hist,
                            production_histogram=hist, raw_exact=native == current, class_exact=plane == class_plane,
                            histogram_exact=native_hist == hist,
                            first_differences=[{'offset': i, 'aex': a, 'mac': b} for i, (a, b) in enumerate(zip(native, current)) if a != b][:16],
                            different_bytes=sum(a != b for a, b in zip(native, current)),
                            executed_imports=sorted(audit.executed_imports), classifier_instructions=ci, worker_instructions=wi,
                            input_and_output_padding_guard_checks=True)
                rows.append(case)
                instances.clear()
                if len(rows) % 4 == 0:
                    gc.collect()
                if len(rows) % 16 == 0:
                    print('SM2_COLOR_WEIGHT', len(rows), sum(c['raw_exact'] for c in rows), sum(c['class_exact'] for c in rows), flush=True)
    finally:
        instances.clear()
        gc.collect()
    dependencies = [Path(__file__), HARNESS, Path(retained.__file__),
                    Path(matrix.__file__), Path(matrix.typed.__file__),
                    Path(matrix.v1.__file__), Path(matrix.v2.__file__), ROOT / 'tools/emulation/aex_loader.py',
                    SOURCE.parent / 'OLMSmoother2_decode_lut_10000.h', SOURCE.parent / 'OLMSmoother2_encode_lut_10000.h']
    report = {'schema': 'olmsmoother2.color-weight/1', 'matrix': args.matrix, 'limit': args.limit,
              'case_count': len(rows), 'source_sha256': retained.sha(source.encode()),
              'aex_sha256': matrix.typed.AEX_SHA256,
              'decode_lut_sha256': retained.sha(matrix.v2.DECODE), 'encode_lut_sha256': retained.sha(matrix.v2.ENCODE),
              'dependencies_sha256': {str(p.relative_to(ROOT)): retained.sha(p.read_bytes()) for p in dependencies},
              'summary': {'raw_exact_count': sum(c['raw_exact'] for c in rows),
                          'class_exact_count': sum(c['class_exact'] for c in rows),
                          'histogram_exact_count': sum(c['histogram_exact'] for c in rows)},
              'cases': rows,
              'claims_not_made': ['Classifier/worker emulation with documented ABI/config layout, not exported parameter-builder or native AE evidence',
                                  'Normalized native scratch uses the same authored typed values; native input-world unpack not executed here',
                                  'Version 2 uses captured LUTs, not general native Windows UCRT/LUT construction proof',
                                  'Temporary production observer prints class bytes without injecting or replacing them',
                                  'No arbitrary input/geometry/settings/state or all 10 completion']}
    args.report.write_text(json.dumps(report, sort_keys=True, indent=2) + '\n')
    print('RESULT', report['summary'], flush=True)


if __name__ == '__main__':
    main()
