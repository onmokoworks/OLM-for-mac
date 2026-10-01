#!/usr/bin/env python3
"""Actual exported AEX Smart versus Mac public Smart for key/gamma and HDR."""
import argparse
import json
import struct
import subprocess
import tempfile
from pathlib import Path

import probe_olmsmoother2_exported_color_weight_20261001 as retained

ROOT = retained.campaign.ROOT
SOURCE = retained.campaign.SOURCE
HARNESS = Path(__file__).with_name('olmsmoother2_public_key_gamma_harness_20261001.cpp')
sha = retained.campaign.retained.sha
GAMMA_MAX = struct.unpack('<f', struct.pack('<f', 2.4))[0]
COLORS = [[255, 41, 83, 137], [255, 213, 39, 97], [0, 41, 83, 137],
          [128, 29, 199, 81], [255, 7, 91, 233]]


def fixture(definition, depth):
    pixels = retained.geometry.fixture(definition)
    packed = bytearray(retained.campaign.retained.typed_input(pixels, depth))
    w, h = definition['geometry']; size = {'PF8': 4, 'PF16': 8, 'PF32': 16}[depth]
    profile = definition['profile']
    if profile != 'sdr':
        assert depth in ('PF16', 'PF32')
        for y in range(h):
            for x in range(w):
                at = (y * w + x) * size
                values = list(struct.unpack_from('<4H' if depth == 'PF16' else '<4f', packed, at))
                if profile == 'float_bits':
                    assert depth == 'PF32'
                    bits = (0, 1, 0x80000000, 0x00800000, 0x3d25aee6, 0x3f7fffff,
                            0x3f800001, 0x3e800001, 0x3f000001, 0xbf000000, 0x40000000)
                    alpha = (0, 1, 0x3f000000, 0x3f800000, 0x40000000, 0xbf000000)[(x + 3 * y) % 6]
                    struct.pack_into('<4I', packed, at, alpha,
                                     *[bits[(x + 2 * y + c * 3) % len(bits)] for c in range(3)])
                    continue
                factor = (2 if (x + y) % 2 else -1) if profile == 'combined' and depth == 'PF32' else 2
                if profile in ('alpha_hdr', 'alpha_signed', 'combined'):
                    values[0] *= -1 if profile == 'alpha_signed' else factor
                if profile in ('rgb_hdr', 'rgb_signed', 'combined'):
                    values[1:] = [v * (-1 if profile == 'rgb_signed' else factor) for v in values[1:]]
                assert profile in ('alpha_hdr', 'alpha_signed', 'rgb_hdr', 'rgb_signed', 'combined')
                if depth == 'PF16': values = [min(65535, v) for v in values]
                struct.pack_into('<4H' if depth == 'PF16' else '<4f', packed, at, *values)
    rowbytes = w * size + 8
    return b''.join(packed[y * w * size:(y + 1) * w * size] + b'\xa5' * 8 for y in range(h)), rowbytes


def parameters(case):
    s, r, e = case['smoothing']
    values = {1: case['key'][0], 3: case['key'][1], 4: s, 5: e, 6: r,
              7: case['version'], 8: case['gamma_mode'], 9: case['gamma_value'], 10: case['gamma_count']}
    out = [{'slot': slot, 'value': value} for slot, value in values.items()]
    out.append({'slot': 2, 'color': case['key_color']})
    out.extend({'slot': 11 + i, 'color': color} for i, color in enumerate(case['palette']))
    return sorted(out, key=lambda p: p['slot'])


def config_text(params):
    return ''.join(f"{p['slot']} c " + ' '.join(map(str, p['color'])) + '\n' if 'color' in p
                   else f"{p['slot']} s {p['value']}\n" for p in params)


def compile_public(directory, source, sanitize=False):
    directory.mkdir(parents=True)
    (directory / 'production_under_test.cpp').write_text(source)
    binary = directory / 'probe'
    flags = ['-O1', '-g', '-fsanitize=address,undefined', '-fno-omit-frame-pointer'] if sanitize else ['-O2']
    subprocess.run(['clang++', '-std=c++17', *flags, '-fno-fast-math', '-ffp-contract=off',
                    '-Wno-deprecated-declarations', '-I', str(directory),
                    '-I', str(ROOT / 'cli/OLMSmoother2/shim'), '-I', str(SOURCE.parent),
                    str(HARNESS), '-o', str(binary)], check=True)
    return binary


def mac_render(binary, temp, case, env=None):
    raw, rowbytes = fixture(case['fixture'], case['depth'])
    w, h = case['geometry']; size = {'PF8': 4, 'PF16': 8, 'PF32': 16}[case['depth']]
    packed = b''.join(raw[y * rowbytes:y * rowbytes + w * size] for y in range(h))
    config = temp / 'parameters.txt'; config.write_text(config_text(case['parameters']))
    result = subprocess.run([str(binary), str(w), str(h), case['depth'], str(config)], input=packed,
                            check=True, capture_output=True, env=env)
    values = dict(line.split(' ', 1) for line in result.stdout.decode().splitlines())
    return int(values['ERROR']), bytes.fromhex(values['RAW']), list(map(int, values['CALLBACKS'].split(',')))


def scenarios():
    # Deliberately independent states, rather than one fixed source/key identity.
    for mode, gamma, count, key, palette_kind, smoothing in (
        (1, GAMMA_MAX, 0, (0, 1), 'normal', (100, 2, 0)),
        (1, 1.0, 5, (1, 0), 'normal', (49, 2, 50)),
        (1, 1.8, 1, (1, 1), 'normal', (100, 2, 0)),
        (3, 1.0, 0, (0, 0), 'normal', (100, 2, 0)),
        (3, 1.8, 5, (1, 0), 'reordered', (49, 2, 50)),
        (3, GAMMA_MAX, 1, (1, 1), 'normal', (100, 100, 100)),
        (2, 1.0, 0, (0, 0), 'normal', (100, 2, 0)),
        (2, 1.8, 0, (1, 0), 'normal', (49, 2, 50)),
        (2, GAMMA_MAX, 0, (1, 1), 'normal', (100, 100, 100)),
        (2, 1.0, 1, (1, 0), 'normal', (100, 2, 0)),
        (2, 1.8, 2, (1, 1), 'reordered', (49, 2, 50)),
        (2, GAMMA_MAX, 5, (0, 0), 'normal', (100, 100, 100)),
        (2, 1.8, 3, (0, 1), 'duplicate', (100, 2, 0)),
        (2, GAMMA_MAX, 1, (1, 0), 'unmatched', (0, 0, 0)),
        (2, 1.0, 5, (1, 1), 'duplicate', (1, 1, 1)),
    ):
        palette = [list(c) for c in COLORS]
        if palette_kind == 'reordered': palette.reverse()
        if palette_kind == 'duplicate': palette[1] = list(palette[0]); palette[2] = list(palette[0])
        if palette_kind == 'unmatched': palette = [[255, 17 + i, 31 + i, 47 + i] for i in range(5)]
        yield {'gamma_mode': mode, 'gamma_value': gamma, 'gamma_count': count, 'key': list(key),
               'key_color': list(COLORS[0]), 'palette': palette, 'palette_kind': palette_kind,
               'smoothing': list(smoothing)}


def specifications(matrix):
    if matrix == 'controls':
        for dimensions in ((1, 1), (1, 9), (9, 1), (2, 2), (4, 3), (7, 9), (17, 19)):
            for pattern in ('diagonal', 'ramp_alpha'):
                for scenario in scenarios():
                    for version in (1, 2):
                        for depth in ('PF8', 'PF16', 'PF32'):
                            case = dict(scenario, geometry=list(dimensions), version=version, depth=depth)
                            case['fixture'] = {'id': 'sm2_public_key_gamma', 'width': dimensions[0], 'height': dimensions[1],
                                               'geometry': list(dimensions), 'pattern': pattern, 'profile': 'sdr'}
                            case['parameters'] = parameters(case)
                            yield case
    else:
        for depth, profiles in (('PF16', ('rgb_hdr', 'alpha_hdr', 'combined')),
                                ('PF32', ('rgb_hdr', 'rgb_signed', 'alpha_hdr', 'alpha_signed', 'combined', 'float_bits'))):
            for profile in profiles:
                for dimensions in ((1, 1), (4, 3), (7, 9), (17, 19)):
                    for pattern in ('diagonal', 'ramp_alpha'):
                        for key in ((0, 0), (1, 0), (1, 1)):
                            for version in (1, 2):
                                case = {'geometry': list(dimensions), 'depth': depth, 'version': version,
                                        'smoothing': [49, 2, 50], 'key': list(key), 'key_color': list(COLORS[0]),
                                        'gamma_mode': 1, 'gamma_value': GAMMA_MAX, 'gamma_count': 1,
                                        'palette': [list(c) for c in COLORS], 'palette_kind': 'normal'}
                                case['fixture'] = {'id': 'sm2_public_typed_hdr', 'width': dimensions[0], 'height': dimensions[1],
                                                   'geometry': list(dimensions), 'pattern': pattern, 'profile': profile}
                                case['parameters'] = parameters(case)
                                yield case


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--worker', type=Path, required=True)
    parser.add_argument('--matrix', choices=('controls', 'hdr'), required=True)
    parser.add_argument('--limit', type=int)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    assert sha(args.worker.read_bytes()) == retained.FROZEN_SHA
    assert sha(retained.native_identity.AEX_PATH.read_bytes()) == retained.native_identity.AEX_SHA256
    saved_aex, saved_fixture = retained.typed_owner.AEX, retained.typed_owner.fixture
    retained.typed_owner.AEX, retained.typed_owner.fixture = retained.native_identity.AEX_PATH, fixture
    source = SOURCE.read_text(); cases = []
    try:
        with tempfile.TemporaryDirectory(prefix='sm2_key_gamma_hdr_') as directory:
            temp = Path(directory); binary = compile_public(temp / 'production', source)
            for case in specifications(args.matrix):
                if args.limit is not None and len(cases) >= args.limit: break
                native, frame, payload, close = retained.typed_owner.native_render(args.worker, temp, case)
                error, output, callbacks = mac_render(binary, temp, case)
                raw, _ = fixture(case['fixture'], case['depth'])
                case.update(input_sha256=sha(raw), native_raw_sha256=sha(native),
                            production_raw_sha256=sha(output) if not error else None, mac_error=error,
                            mac_callbacks=callbacks, raw_exact=not error and native == output,
                            different_bytes=sum(a != b for a, b in zip(native, output)) if not error else None,
                            first_differences=[{'offset': i, 'aex': a, 'mac': b} for i, (a, b) in enumerate(zip(native, output)) if a != b][:16] if not error else [],
                            parameter_payload=payload, frame_done=frame, session_clean=close['session_clean'],
                            unsupported_suite_calls=close['unsupported_suite_calls'])
                cases.append(case)
                if len(cases) % 90 == 0:
                    print('SM2_KEY_GAMMA_HDR', args.matrix, len(cases), sum(c['raw_exact'] for c in cases),
                          sum(c['mac_error'] != 0 for c in cases), flush=True)
    finally:
        retained.typed_owner.AEX, retained.typed_owner.fixture = saved_aex, saved_fixture
    deps = [Path(__file__), HARNESS, Path(retained.__file__), Path(retained.geometry.__file__),
            Path(retained.campaign.__file__), Path(retained.campaign.retained.__file__),
            Path(retained.typed_owner.__file__), Path(retained.native_identity.__file__),
            ROOT / 'cli/OLMSmoother2/shim/OLMSmoother2.h',
            SOURCE.parent / 'OLMSmoother2_decode_lut_10000.h', SOURCE.parent / 'OLMSmoother2_encode_lut_10000.h']
    report = {'schema': 'olmsmoother2.public-key-gamma-hdr/1', 'matrix': args.matrix, 'limit': args.limit,
              'case_count': len(cases), 'source_sha256': sha(source.encode()),
              'aex_sha256': retained.native_identity.AEX_SHA256, 'frozen_worker_sha256': retained.FROZEN_SHA,
              'dependencies_sha256': {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in deps},
              'summary': {'raw_exact_count': sum(c['raw_exact'] for c in cases), 'mac_reject_count': sum(c['mac_error'] != 0 for c in cases)},
              'cases': cases, 'claims_not_made': [
                  'Actual AEX exported resident Smart with emulated host imports, not native Windows UCRT/AE',
                  'Mac public EffectMain with CLI shim, not installed/native AE or real SDK runtime',
                  'Resident payload is slot/type validated, not per-frame parameter readback',
                  'HDR/raw uint16 inputs are authored, not proof of normal AE UI reachability',
                  'No arbitrary inputs/settings/geometry/ROI/downsample/UI/save or all-ten compatibility completion']}
    args.report.write_text(json.dumps(report, sort_keys=True, indent=2) + '\n')
    print('RESULT', report['summary'], flush=True)


if __name__ == '__main__':
    main()
