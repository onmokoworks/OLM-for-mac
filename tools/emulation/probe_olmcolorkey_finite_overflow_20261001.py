#!/usr/bin/env python3
"""Independent finite FLOAT32 extremes, including internal premultiply overflow."""
import argparse
import copy
import itertools
import json
import math
import struct
import tempfile
from pathlib import Path

import probe_olmcolorkey_typed_controls_20261001 as owner
import probe_olmcolorkey_lab_state_boundary_20261001 as independent
from colorkey_yuv_threshold_candidate_20261001 import candidate_source

FROZEN_SHA = '0eb2f7705598f7b5f53563b9d920274ba094c835ff3dbaaf5f6fb214ec0cfd61'


def fixture(f, depth):
    assert depth == 'PF32' and f['width'] == f['height'] == 1
    assert all(math.isfinite(independent.number(v)) for v in f['argb_u32'])
    return struct.pack('<4I', *f['argb_u32']) + b'\xa5' * 8, 24


def specifications():
    max_positive, max_negative = 0x7f7fffff, 0xff7fffff
    rgb_patterns = ((max_positive,) * 3, (max_positive, max_negative, max_positive),
                    (max_negative, max_positive, max_negative), (max_positive, 0, 0))
    for space, component, threshold, keep, alpha, pattern, premultiplied in itertools.product(
        (1, 2, 5, 6), (False, True), (0.0, 1.0), (False, True),
        (0x40000000, max_positive), range(4), (False, True),
    ):
        params = owner.parameters(count=1, keep=keep, replace=False, space=space,
                                  precision=1, per_component=component,
                                  premultiplied=premultiplied, threshold=threshold)
        for p in params:
            if p['slot'] == 26:
                p['color'] = [255, 26, 191, 204]
        yield {'fixture': {'id': 'finite_overflow', 'width': 1, 'height': 1,
                           'argb_u32': [alpha, *rgb_patterns[pattern]]},
               'depth': 'PF32',
               'label': f'space{space}_component{component}_threshold{threshold}_keep{keep}_alpha{alpha:08x}_pattern{pattern}_premult{premultiplied}',
               'parameters': params}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--worker', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--production-only', action='store_true')
    args = parser.parse_args()
    assert owner.sha(args.worker.read_bytes()) == FROZEN_SHA
    source = owner.SOURCE.read_text()
    candidate = None if args.production_only else candidate_source(source)
    saved_fixture = owner.fixture
    owner.fixture = fixture
    cases = []
    try:
        with tempfile.TemporaryDirectory(prefix='olmck_finite_overflow_') as directory:
            temp = Path(directory)
            exes = {'production': owner.compile_public(temp / 'production', source)}
            if candidate is not None:
                exes['candidate'] = owner.compile_public(temp / 'candidate', candidate)
            for case in specifications():
                native, frame, payload, close = owner.native_render(args.worker, temp, case)
                raw, _ = fixture(case['fixture'], case['depth'])
                case.update(input_sha256=owner.sha(raw), packed_input_sha256=owner.sha(raw[:16]),
                            actual_sha256=owner.sha(native), raw_pixel_bytes=len(native),
                            parameter_payload=payload, frame_done=frame,
                            session_clean=close['session_clean'], unsupported_suite_calls=close['unsupported_suite_calls'],
                            results={name: independent.compare(exe, temp, case, native) for name, exe in exes.items()})
                cases.append(case)
                if len(cases) % 64 == 0:
                    print('FINITE_OVERFLOW', len(cases),
                          {name: sum(c['results'][name]['classic']['exact'] for c in cases) for name in exes}, flush=True)
    finally:
        owner.fixture = saved_fixture
    dependencies = [Path(__file__), Path(owner.__file__), Path(independent.__file__), owner.HARNESS]
    if candidate is not None:
        dependencies.append(Path(__file__).with_name('colorkey_yuv_threshold_candidate_20261001.py'))
    report = {'schema': 'olmcolorkey.finite-overflow/1', 'case_count': len(cases),
              'source_sha256': owner.sha(source.encode()),
              'candidate_source_sha256': owner.sha(candidate.encode()) if candidate is not None else None,
              'summary': {name: {r: sum(c['results'][name][r]['exact'] for c in cases) for r in ('classic', 'smart')} for name in exes},
              'dependencies_sha256': {str(p.relative_to(owner.ROOT)): owner.sha(p.read_bytes()) for p in dependencies},
              'aex_sha256': owner.sha(owner.AEX.read_bytes()), 'frozen_worker_sha256': FROZEN_SHA,
              'cases': cases, 'claims_not_made': ['All source channels finite; derived intermediates can be nonfinite',
                                                'FLOAT32 source with precision 1; forced-lower-precision not tested here',
                                                'No native Windows UCRT/AE, normal host production of these worlds, or full input/state completion']}
    head = copy.copy(report)
    del head['cases']
    text = json.dumps(head, sort_keys=True, indent=2)[:-2] + ',\n  "cases": [\n'
    text += ',\n'.join('    ' + json.dumps(c, sort_keys=True) for c in cases) + '\n  ]\n}\n'
    args.report.write_text(text)
    assert json.loads(text) == report
    print('RESULT', report['summary'], flush=True)


if __name__ == '__main__':
    main()
