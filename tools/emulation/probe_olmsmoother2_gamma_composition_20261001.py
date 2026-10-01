#!/usr/bin/env python3
"""Exported Smart HDR+gamma compositions and FLOAT32 color-membership boundaries."""
import argparse
import json
import struct
import subprocess
import tempfile
from pathlib import Path

import probe_olmsmoother2_key_gamma_hdr_20261001 as base

SOURCE = base.SOURCE
ROOT = base.ROOT
ORIGINAL_FIXTURE = base.fixture
f32 = lambda value: struct.unpack('<f', struct.pack('<f', value))[0]
bits32 = lambda value: struct.unpack('<I', struct.pack('<f', value))[0]


def fixture(definition, depth):
    profile = definition['profile']
    if profile not in ('membership_bits', 'random_finite'):
        return ORIGINAL_FIXTURE(definition, depth)
    assert depth == 'PF32'
    w, h = definition['geometry']; rowbytes = w * 16 + 8; output = bytearray()
    state = 0x31415926
    for y in range(h):
        for x in range(w):
            if profile == 'membership_bits':
                rgba = [f32(c / 255) for c in definition['anchor_rgb']] + [f32(definition['alpha'] / 255)]
                if (x + 2 * y) % 3 != 2:
                    rgba[definition['component']] = struct.unpack('<f', struct.pack('<I', definition['component_bits']))[0]
                else:
                    rgba[:3] = [f32((c + 113) % 256 / 255) for c in definition['anchor_rgb']]
                output.extend(struct.pack('<4f', rgba[3], *rgba[:3]))
            else:
                channels = []
                for _ in range(3):
                    state = (1664525 * state + 1013904223) & 0xffffffff
                    channels.append(f32(((state >> 8) % 2049 - 1024) / 256))
                alpha = (0.0, -0.25, 0.5, 1.0, 2.0)[(x + 3 * y) % 5]
                output.extend(struct.pack('<4f', alpha, *channels))
        output.extend(b'\xa5' * 8)
    return bytes(output), rowbytes


def gamma_states():
    for mode, gamma, count, key, palette_kind, smoothing in (
        (3, 1.0, 0, (0, 0), 'normal', (49, 2, 50)),
        (3, 1.8, 5, (0, 0), 'normal', (49, 2, 50)),
        (3, base.GAMMA_MAX, 1, (1, 0), 'normal', (100, 100, 100)),
        (2, 1.8, 5, (0, 0), 'normal', (49, 2, 50)),
        (2, base.GAMMA_MAX, 1, (1, 1), 'normal', (100, 2, 0)),
        (2, 1.8, 0, (0, 0), 'normal', (49, 2, 50)),
        (2, base.GAMMA_MAX, 3, (0, 1), 'duplicate', (1, 1, 1)),
    ):
        palette = [list(c) for c in base.COLORS]
        if palette_kind == 'duplicate': palette[1] = list(palette[0]); palette[2] = list(palette[0])
        yield {'gamma_mode': mode, 'gamma_value': gamma, 'gamma_count': count, 'key': list(key),
               'key_color': list(base.COLORS[0]), 'palette': palette, 'palette_kind': palette_kind,
               'smoothing': list(smoothing)}


def specifications(matrix):
    if matrix == 'hdr':
        for depth, profiles in (('PF16', ('rgb_hdr', 'alpha_hdr', 'combined')),
                                ('PF32', ('rgb_hdr', 'rgb_signed', 'alpha_hdr', 'alpha_signed', 'combined', 'float_bits', 'random_finite'))):
            for profile in profiles:
                for dimensions in ((4, 3), (7, 9), (17, 19)):
                    for pattern in ('diagonal', 'ramp_alpha'):
                        for state in gamma_states():
                            for version in (1, 2):
                                case = dict(state, geometry=list(dimensions), depth=depth, version=version)
                                case['fixture'] = {'id': 'sm2_gamma_hdr_composition', 'width': dimensions[0], 'height': dimensions[1],
                                                   'geometry': list(dimensions), 'pattern': pattern, 'profile': profile}
                                case['parameters'] = base.parameters(case)
                                yield case
    else:
        tolerance = struct.unpack('<f', bytes.fromhex('8180003b'))[0]
        for rgb in ((0, 0, 0), (41, 83, 137), (202, 187, 230), (255, 255, 255)):
            for component in range(3):
                for sign in (-1, 1):
                    estimate = f32(f32(rgb[component] / 255) + sign * tolerance)
                    center_bits = bits32(estimate)
                    for offset in (-2, -1, 0, 1, 2):
                        for alpha in (128, 255):
                            for version in (1, 2):
                                for route in ('gamma_colors', 'key', 'invert_key'):
                                    f = {'id': 'sm2_membership_boundary', 'width': 4, 'height': 3,
                                         'geometry': [4, 3], 'profile': 'membership_bits', 'anchor_rgb': list(rgb),
                                         'component': component, 'component_bits': center_bits + offset, 'alpha': alpha}
                                    color = [255, *rgb]
                                    case = {'fixture': f, 'geometry': [4, 3], 'depth': 'PF32', 'version': version,
                                            'smoothing': [49, 2, 50], 'key': [int(route != 'gamma_colors'), int(route == 'invert_key')],
                                            'key_color': color, 'gamma_mode': 2 if route == 'gamma_colors' else 1,
                                            'gamma_value': 1.8, 'gamma_count': 1,
                                            'palette': [color] + [[255, 17+i, 31+i, 47+i] for i in range(4)],
                                            'palette_kind': 'single_boundary', 'route': route,
                                            'boundary_sign': sign, 'boundary_offset': offset}
                                    case['parameters'] = base.parameters(case)
                                    yield case


def mac_render(binary, temp, case, env=None):
    saved = base.fixture; base.fixture = fixture
    try:
        return base.mac_render(binary, temp, case, env)
    finally:
        base.fixture = saved


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--worker', type=Path, required=True)
    parser.add_argument('--matrix', choices=('hdr', 'tolerance'), required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    assert base.sha(args.worker.read_bytes()) == base.retained.FROZEN_SHA
    assert base.sha(base.retained.native_identity.AEX_PATH.read_bytes()) == base.retained.native_identity.AEX_SHA256
    saved_aex, saved_fixture = base.retained.typed_owner.AEX, base.retained.typed_owner.fixture
    base.retained.typed_owner.AEX, base.retained.typed_owner.fixture = base.retained.native_identity.AEX_PATH, fixture
    source = SOURCE.read_text(); cases = []
    try:
        with tempfile.TemporaryDirectory(prefix='sm2_gamma_composition_') as directory:
            temp = Path(directory); binary = base.compile_public(temp / 'production', source)
            for case in specifications(args.matrix):
                native, frame, payload, close = base.retained.typed_owner.native_render(args.worker, temp, case)
                error, output, callbacks = mac_render(binary, temp, case)
                raw, _ = fixture(case['fixture'], case['depth'])
                case.update(input_sha256=base.sha(raw), native_raw_sha256=base.sha(native),
                            production_raw_sha256=base.sha(output) if not error else None, mac_error=error,
                            mac_callbacks=callbacks, raw_exact=not error and output == native,
                            different_bytes=sum(a != b for a, b in zip(native, output)) if not error else None,
                            first_differences=[{'offset': i, 'aex': a, 'mac': b} for i, (a, b) in enumerate(zip(native, output)) if a != b][:16] if not error else [],
                            parameter_payload=payload, frame_done=frame, session_clean=close['session_clean'],
                            unsupported_suite_calls=close['unsupported_suite_calls'])
                cases.append(case)
                if len(cases) % 120 == 0:
                    print('SM2_GAMMA_COMPOSITION', args.matrix, len(cases), sum(c['raw_exact'] for c in cases), flush=True)
    finally:
        base.retained.typed_owner.AEX, base.retained.typed_owner.fixture = saved_aex, saved_fixture
    deps = [Path(__file__), Path(base.__file__), base.HARNESS, Path(base.retained.__file__),
            Path(base.retained.campaign.__file__), Path(base.retained.campaign.retained.__file__),
            Path(base.retained.geometry.__file__), Path(base.retained.typed_owner.__file__),
            Path(base.retained.native_identity.__file__), ROOT / 'cli/OLMSmoother2/shim/OLMSmoother2.h',
            SOURCE.parent / 'OLMSmoother2_decode_lut_10000.h', SOURCE.parent / 'OLMSmoother2_encode_lut_10000.h']
    report = {'schema': 'olmsmoother2.gamma-composition/1', 'matrix': args.matrix, 'case_count': len(cases),
              'source_sha256': base.sha(source.encode()), 'aex_sha256': base.retained.native_identity.AEX_SHA256,
              'frozen_worker_sha256': base.retained.FROZEN_SHA,
              'dependencies_sha256': {str(p.relative_to(ROOT)): base.sha(p.read_bytes()) for p in deps},
              'summary': {'raw_exact_count': sum(c['raw_exact'] for c in cases), 'mac_reject_count': sum(c['mac_error'] != 0 for c in cases)},
              'cases': cases, 'claims_not_made': [
                  'Actual AEX exported resident Smart uses emulated host imports, not native Windows UCRT or AE',
                  'Mac numerical public chain uses CLI shim, not installed/native AE or SDK runtime',
                  'FLOAT32 color-boundary inputs are authored from approximate threshold locations, not a proof of every transition',
                  'HDR/signed/raw-uint16 worlds are authored; no normal AE UI reachability claim',
                  'No arbitrary input/settings/geometry/floating environment/UI/save/ROI/downsample or all-ten completion']}
    args.report.write_text(json.dumps(report, sort_keys=True, indent=2) + '\n')
    print('RESULT', report['summary'], flush=True)


if __name__ == '__main__':
    main()
