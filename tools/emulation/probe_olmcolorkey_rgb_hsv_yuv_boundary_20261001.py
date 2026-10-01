#!/usr/bin/env python3
"""Locate native FLOAT32 boundaries and probe DOUBLE controls across their bins."""
import argparse
import copy
import json
import struct
import tempfile
from pathlib import Path

import probe_olmcolorkey_typed_controls_20261001 as owner
import probe_olmcolorkey_lab_state_boundary_20261001 as independent

FROZEN_SHA = '0eb2f7705598f7b5f53563b9d920274ba094c835ff3dbaaf5f6fb214ec0cfd61'


def fixture(f, depth):
    pixel_size = {'PF8': 4, 'PF16': 8, 'PF32': 16}[depth]
    assert f['width'] == f['height'] == 1
    values = [f['alpha'], *f['rgb']]
    if depth == 'PF8':
        pixel = struct.pack('<4B', *values)
    elif depth == 'PF16':
        pixel = struct.pack('<4H', *(int(v * 32768 / 255) for v in values))
    else:
        pixel = struct.pack('<4f', *(v / 255 for v in values))
    return pixel + b'\xa5' * 8, pixel_size + 8


def families():
    for space in (1, 2, 5, 6):
        for component in (False, True):
            for precision in (1, 2, 3):
                for depth in ('PF8', 'PF16', 'PF32'):
                    for profile, rgb, alpha, premultiplied in (
                        ('opaque_blue', [44, 75, 119], 255, False),
                        ('partial_gray', [127, 129, 126], 128, True),
                    ):
                        params = owner.parameters(
                            count=1, keep=True, replace=False, space=space,
                            precision=precision, per_component=component,
                            premultiplied=premultiplied,
                        )
                        for p in params:
                            if p['slot'] == 26:
                                p['color'] = [255, 26, 191, 204]
                        yield {
                            'fixture': {'id': profile, 'width': 1, 'height': 1,
                                        'rgb': rgb, 'alpha': alpha},
                            'depth': depth,
                            'label': f'space{space}_component{component}_precision{precision}_{profile}',
                            'parameters': params,
                        }


def threshold_case(family, threshold, per_color=False):
    case = independent.set_threshold(family, threshold)
    for param in case['parameters']:
        if param['slot'] == 7:
            param['value'] = int(per_color)
    return case


def matched(raw, depth):
    alpha = struct.unpack_from({'PF8': '<B', 'PF16': '<H', 'PF32': '<f'}[depth], raw)[0]
    assert alpha >= 0
    return alpha != 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--worker', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    assert owner.sha(args.worker.read_bytes()) == FROZEN_SHA
    source = owner.SOURCE.read_text()
    saved_fixture = owner.fixture
    owner.fixture = fixture
    cases, searches = [], []
    try:
        with tempfile.TemporaryDirectory(prefix='olmck_color_boundary_') as directory:
            temp = Path(directory)
            exe = owner.compile_public(temp / 'production', source)
            for family in families():
                trace = []

                def measure(bits):
                    trial = threshold_case(family, independent.number(bits))
                    raw, _, _, _ = owner.native_render(args.worker, temp, trial)
                    hit = matched(raw, family['depth'])
                    trace.append({'threshold_bits': bits,
                                  'threshold': independent.number(bits),
                                  'matched': hit, 'actual_sha256': owner.sha(raw)})
                    return hit

                low, high = independent.bits(0.0), independent.bits(1.0)
                # Prove both endpoint states before assuming a transition.
                assert not measure(low), family
                assert measure(high), family
                while high - low > 1:
                    mid = (low + high) // 2
                    if measure(mid):
                        high = mid
                    else:
                        low = mid
                assert not measure(low) and measure(high)
                searches.append({'label': family['label'], 'depth': family['depth'],
                                 'last_unmatched_bits': low, 'first_matched_bits': high,
                                 'trace': trace})
                lo, hi = independent.number(low), independent.number(high)
                samples = [(independent.number(bit), f'f32_{bit:08x}')
                           for bit in range(low - 1, high + 3)]
                samples += [(lo + (hi - lo) * numerator / 16, f'fraction_{numerator}/16')
                            for numerator in (-4, 3, 7, 8, 9, 13, 20)]
                assert len(samples) == 12
                for index, (threshold, sample) in enumerate(samples):
                    case = threshold_case(family, threshold, per_color=index % 2 == 1)
                    case['label'] += '_' + sample
                    case['double_threshold_hex'] = threshold.hex()
                    case['materialized_threshold_bits'] = independent.bits(threshold)
                    native, frame, payload, close = owner.native_render(args.worker, temp, case)
                    raw, _ = fixture(case['fixture'], case['depth'])
                    pixel_size = {'PF8': 4, 'PF16': 8, 'PF32': 16}[case['depth']]
                    case.update(
                        input_sha256=owner.sha(raw), packed_input_sha256=owner.sha(raw[:pixel_size]),
                        actual_sha256=owner.sha(native), raw_pixel_bytes=len(native),
                        parameter_payload=payload, config_sha256=owner.sha(owner.config_text(case['parameters']).encode()),
                        frame_done=frame, session_clean=close['session_clean'],
                        unsupported_suite_calls=close['unsupported_suite_calls'],
                        reference_kind='frozen-exported-owner', worker_sha256=FROZEN_SHA,
                        native_matched=matched(native, case['depth']),
                        results=independent.compare(exe, temp, case, native),
                    )
                    cases.append(case)
                print('COLOR_BOUNDARY', len(searches), len(cases), family['label'], family['depth'],
                      sum(c['results']['classic']['exact'] for c in cases), flush=True)
    finally:
        owner.fixture = saved_fixture
    dependencies = (Path(__file__), Path(owner.__file__), Path(independent.__file__), owner.HARNESS)
    report = {
        'schema': 'olmcolorkey.rgb-hsv-yuv-boundary/1', 'case_count': len(cases),
        'family_count': len(searches),
        'summary': {r: sum(c['results'][r]['exact'] for c in cases) for r in ('classic', 'smart')},
        'source_sha256': owner.sha(source.encode()), 'aex_sha256': owner.sha(owner.AEX.read_bytes()),
        'frozen_worker_sha256': FROZEN_SHA,
        'dependencies_sha256': {str(p.relative_to(owner.ROOT)): owner.sha(p.read_bytes()) for p in dependencies},
        'searches': searches, 'cases': cases,
        'claims_not_made': [
            'Native boundaries belong to the frozen local exported AEX owner, not Windows UCRT or installed AE',
            'Binary search is within an independently bracketed single-key family; arbitrary palettes are not proven monotonic',
            'Per Color alternates between samples; this is not a full Cartesian product of controls',
            'No all-input, threshold, HDR, geometry, ROI/downsample, UI or project state completion',
            'Resident per-frame parameter readback unavailable',
        ],
    }
    head = copy.copy(report)
    del head['cases']
    text = json.dumps(head, sort_keys=True, indent=2)[:-2] + ',\n  "cases": [\n'
    text += ',\n'.join('    ' + json.dumps(c, sort_keys=True) for c in cases) + '\n  ]\n}\n'
    args.report.write_text(text)
    assert json.loads(text) == report
    print('RESULT', report['summary'], flush=True)


if __name__ == '__main__':
    main()
