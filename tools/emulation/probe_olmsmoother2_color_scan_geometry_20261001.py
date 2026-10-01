#!/usr/bin/env python3
"""Independent larger patterns exercise scanner length and polygon weighting."""
import argparse
import gc
import json
import subprocess
import tempfile
from pathlib import Path

import probe_olmsmoother2_color_weight_20261001 as campaign
import olmsmoother2_dispatch_observer_20261001 as observer


def fixture(case):
    w, h = case['geometry']
    pixels = []
    for y in range(h):
        for x in range(w):
            if case['pattern'] == 'diagonal':
                pixel = (41, 83, 137, 128) if x * h < y * w else (213, 39, 97, 255)
            elif case['pattern'] == 'staircase':
                pixel = ((41, 83, 137, 128), (213, 39, 97, 255), (29, 199, 81, 64))[((x + 2 * y) // 3) % 3]
            elif case['pattern'] == 'islands':
                distance = abs(x - w // 2) + abs(y - h // 2)
                pixel = (213, 39, 97, 192) if 2 <= distance <= min(w, h) // 2 else (7, 91, 233, 0)
                if x == w // 2 or y == h // 2:
                    pixel = (41, 83, 137, 128)
            else:
                assert case['pattern'] == 'ramp_alpha'
                pixel = ((x * 17 + y * 23) % 256, (x * 3 + y * 11) % 256,
                         (x * 29 + y * 5) % 256, (0, 1, 64, 128, 192, 255)[(x + 3 * y) % 6])
            pixels.append(pixel)
    return pixels


def specifications():
    for geometry in ((7, 9), (17, 19)):
        for pattern in ('diagonal', 'staircase', 'islands', 'ramp_alpha'):
            for smoothing in ((100, 2, 0), (49, 2, 50), (1, 1, 1)):
                for version in (1, 2):
                    for depth in ('PF8', 'PF16', 'PF32'):
                        yield {'geometry': list(geometry), 'pattern': pattern, 'smoothing': list(smoothing),
                               'version': version, 'depth': depth}


def production(binary, case, env=None):
    typed = campaign.retained.typed_input(fixture(case), case['depth'])
    run = subprocess.run([str(binary), *map(str, case['geometry']), case['depth'], str(case['version']),
                          *map(str, case['smoothing'])], input=typed, check=True, capture_output=True, env=env)
    values = dict(line.split(' ', 1) for line in run.stdout.decode().splitlines())
    histogram = {int(k): int(v) for k, v in (p.split(':') for p in values['HIST'].split(','))} if values['HIST'] else {}
    return bytes.fromhex(values['RAW']), bytes.fromhex(values['CLASS']), histogram


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    source = campaign.SOURCE.read_text()
    matrix, instances = observer.native_setup()
    cases = []
    with tempfile.TemporaryDirectory(prefix='sm2_color_scan_geometry_') as directory:
        binary = campaign.compile_harness(Path(directory) / 'production', source)
        for case in specifications():
            w, h = case['geometry']
            pixels = fixture(case)
            typed = campaign.retained.typed_input(pixels, case['depth'])
            current, class_plane, histogram = production(binary, case)
            native, plane, ci, wi = matrix.actual(case['depth'], case['version'], campaign.encoded(pixels, case['depth'], matrix),
                                                matrix.DEPTHS[case['depth']][1], w, h, *case['smoothing'])
            audit = instances[-1]
            assert not audit.import_errors and not audit.dispatch_observer_errors
            size, pad = matrix.DEPTHS[case['depth']]
            rb = w * size + pad
            assert len(native) == len(current) == rb * h
            assert all(native[y * rb + w * size:(y + 1) * rb] == b'\xa5' * pad for y in range(h))
            case.update(input_sha256=campaign.retained.sha(typed), native_raw_sha256=campaign.retained.sha(native),
                        production_raw_sha256=campaign.retained.sha(current), raw_exact=native == current,
                        native_class_plane_sha256=campaign.retained.sha(plane), production_class_plane_sha256=campaign.retained.sha(class_plane),
                        class_exact=plane == class_plane, native_dispatch_histogram=dict(sorted(audit.executed_dispatch_histogram.items())),
                        production_dispatch_histogram=histogram, actual_dispatch_exact=dict(audit.executed_dispatch_histogram) == histogram,
                        different_bytes=sum(a != b for a, b in zip(native, current)),
                        first_differences=[{'offset': i, 'aex': a, 'mac': b} for i, (a, b) in enumerate(zip(native, current)) if a != b][:16],
                        executed_imports=sorted(audit.executed_imports), classifier_instructions=ci, worker_instructions=wi,
                        input_and_output_padding_guard_checks=True)
            cases.append(case)
            instances.clear()
            gc.collect()
            if len(cases) % 12 == 0:
                print('SM2_COLOR_SCAN_GEOMETRY', len(cases), sum(c['raw_exact'] for c in cases), sum(c['class_exact'] for c in cases), flush=True)
    dependencies = [Path(__file__), Path(campaign.__file__), campaign.HARNESS, Path(observer.__file__),
                    Path(campaign.retained.__file__), Path(matrix.__file__), Path(matrix.typed.__file__),
                    Path(matrix.v1.__file__), Path(matrix.v2.__file__), campaign.ROOT / 'tools/emulation/aex_loader.py']
    report = {'schema': 'olmsmoother2.color-scan-geometry/1', 'source_sha256': campaign.retained.sha(source.encode()),
              'case_count': len(cases), 'aex_sha256': matrix.typed.AEX_SHA256, 'observer_rva': '0xc50a',
              'decode_lut_sha256': campaign.retained.sha(matrix.v2.DECODE), 'encode_lut_sha256': campaign.retained.sha(matrix.v2.ENCODE),
              'dependencies_sha256': {str(p.relative_to(campaign.ROOT)): campaign.retained.sha(p.read_bytes()) for p in dependencies},
              'summary': {name: sum(c[name] for c in cases) for name in ('raw_exact', 'class_exact', 'actual_dispatch_exact')},
              'cases': cases,
              'claims_not_made': ['Internal classifier/typed worker with documented config ABI, not exported parameter-builder proof',
                                  'Version 2 uses captured LUTs rather than native Windows construction',
                                  'No native Windows/Mac AE, arbitrary inputs/settings, UI, save, ROI/downsample or full compatibility completion']}
    args.report.write_text(json.dumps(report, sort_keys=True, indent=2) + '\n')
    print('RESULT', report['summary'], flush=True)


if __name__ == '__main__':
    main()
