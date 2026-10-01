#!/usr/bin/env python3
"""Paired actual exported AEX resident owner and Mac public Smart owner."""
import argparse
import json
import struct
import subprocess
import tempfile
from pathlib import Path

import probe_olmsmoother2_color_weight_20261001 as campaign
import probe_olmsmoother2_color_scan_geometry_20261001 as geometry
import probe_olmcolorkey_typed_controls_20261001 as typed_owner
import test_olmsmoother2_typed_writeback_20260717 as native_identity

HARNESS = Path(__file__).with_name('olmsmoother2_public_color_weight_harness_20261001.cpp')
FROZEN_SHA = '0eb2f7705598f7b5f53563b9d920274ba094c835ff3dbaaf5f6fb214ec0cfd61'


def source_fixture(definition, depth):
    pixels = geometry.fixture({'geometry': definition['geometry'], 'pattern': definition['pattern']})
    packed = campaign.retained.typed_input(pixels, depth)
    w, h = definition['geometry']; size = {'PF8': 4, 'PF16': 8, 'PF32': 16}[depth]
    return b''.join(packed[y * w * size:(y + 1) * w * size] + b'\xa5' * 8 for y in range(h)), w * size + 8


def compile_public(directory, source, sanitize=False):
    directory.mkdir(parents=True)
    (directory / 'production_under_test.cpp').write_text(source)
    binary = directory / 'public_probe'
    flags = ['-O1', '-g', '-fsanitize=address,undefined', '-fno-omit-frame-pointer'] if sanitize else ['-O2']
    subprocess.run(['clang++', '-std=c++17', *flags, '-fno-fast-math', '-ffp-contract=off',
                    '-Wno-deprecated-declarations', '-I', str(directory),
                    '-I', str(campaign.ROOT / 'cli/OLMSmoother2/shim'), '-I', str(campaign.SOURCE.parent),
                    str(HARNESS), '-o', str(binary)], check=True)
    return binary


def mac_render(binary, case, env=None):
    values = campaign.retained.typed_input(geometry.fixture(case), case['depth'])
    run = subprocess.run([str(binary), *map(str, case['geometry']), case['depth'], str(case['version']),
                          *map(str, case['smoothing'])], input=values, capture_output=True, check=True, env=env)
    result = dict(line.split(' ', 1) for line in run.stdout.decode().splitlines())
    return int(result['ERROR']), bytes.fromhex(result['RAW']), list(map(int, result['CALLBACKS'].split(',')))


def parameters(case):
    s, r, e = case['smoothing']
    values = {1: 0, 3: 0, 4: s, 5: e, 6: r, 7: case['version'], 8: 1, 9: float(struct.unpack('<f', struct.pack('<f', 2.4))[0]), 10: 1}
    return [{'slot': slot, 'value': value} for slot, value in sorted(values.items())]


def specifications():
    for dimensions in ((1, 1), (1, 9), (9, 1), (2, 2), (4, 3), (7, 9), (17, 19)):
        for pattern in ('diagonal', 'ramp_alpha'):
            for smoothing in ((100, 2, 0), (49, 2, 50), (1, 1, 1)):
                for version in (1, 2):
                    for depth in ('PF8', 'PF16', 'PF32'):
                        yield {'geometry': list(dimensions), 'pattern': pattern, 'smoothing': list(smoothing),
                               'version': version, 'depth': depth,
                               'fixture': {'id': 'exported_sm2_color_weight', 'width': dimensions[0], 'height': dimensions[1],
                                           'geometry': list(dimensions), 'pattern': pattern}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--worker', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    assert campaign.retained.sha(args.worker.read_bytes()) == FROZEN_SHA
    assert campaign.retained.sha(native_identity.AEX_PATH.read_bytes()) == native_identity.AEX_SHA256
    source = campaign.SOURCE.read_text()
    saved_aex, saved_fixture = typed_owner.AEX, typed_owner.fixture
    typed_owner.AEX, typed_owner.fixture = native_identity.AEX_PATH, source_fixture
    cases = []
    try:
        with tempfile.TemporaryDirectory(prefix='sm2_exported_color_weight_') as directory:
            temp = Path(directory); binary = compile_public(temp / 'production', source)
            for case in specifications():
                case['parameters'] = parameters(case)
                native, frame, payload, close = typed_owner.native_render(args.worker, temp, case)
                error, current, callbacks = mac_render(binary, case)
                raw, _ = source_fixture(case['fixture'], case['depth'])
                case.update(input_sha256=campaign.retained.sha(raw), native_raw_sha256=campaign.retained.sha(native),
                            production_raw_sha256=campaign.retained.sha(current) if not error else None,
                            mac_error=error, mac_callbacks=callbacks, raw_exact=not error and native == current,
                            different_bytes=sum(a != b for a, b in zip(native, current)) if not error else None,
                            first_differences=[{'offset': i, 'aex': a, 'mac': b} for i, (a, b) in enumerate(zip(native, current)) if a != b][:16] if not error else [],
                            parameter_payload=payload, frame_done=frame, session_clean=close['session_clean'],
                            unsupported_suite_calls=close['unsupported_suite_calls'])
                cases.append(case)
                if len(cases) % 36 == 0:
                    print('SM2_EXPORTED_COLOR_WEIGHT', len(cases), sum(c['raw_exact'] for c in cases),
                          sum(c['mac_error'] != 0 for c in cases), flush=True)
    finally:
        typed_owner.AEX, typed_owner.fixture = saved_aex, saved_fixture
    deps = [Path(__file__), HARNESS, Path(campaign.__file__), campaign.HARNESS, Path(geometry.__file__),
            Path(typed_owner.__file__), Path(native_identity.__file__)]
    report = {'schema': 'olmsmoother2.exported-color-weight/1', 'source_sha256': campaign.retained.sha(source.encode()),
              'aex_sha256': native_identity.AEX_SHA256, 'frozen_worker_sha256': FROZEN_SHA, 'case_count': len(cases),
              'summary': {'raw_exact_count': sum(c['raw_exact'] for c in cases), 'mac_reject_count': sum(c['mac_error'] != 0 for c in cases)},
              'dependencies_sha256': {str(p.relative_to(campaign.ROOT)): campaign.retained.sha(p.read_bytes()) for p in deps},
              'cases': cases,
              'claims_not_made': ['Actual AEX exported resident Smart owner with emulated host imports; not native Windows UCRT or AE',
                                  'Mac public EffectMain compiled with CLI shim host, not installed/native AE or real-SDK host',
                                  'Resident parameter payload is slot/type validated; no per-frame parameter readback',
                                  'No arbitrary input/settings/state or full compatibility completion']}
    args.report.write_text(json.dumps(report, sort_keys=True, indent=2) + '\n')
    print('RESULT', report['summary'], flush=True)


if __name__ == '__main__':
    main()
