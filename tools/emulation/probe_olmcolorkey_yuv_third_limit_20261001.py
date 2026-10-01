#!/usr/bin/env python3
"""Witness the third limit sign gate, including controls outside normal UI range."""
import argparse
import json
import tempfile
from pathlib import Path

import probe_olmcolorkey_typed_controls_20261001 as owner
import probe_olmcolorkey_lab_state_boundary_20261001 as independent
import probe_olmcolorkey_rgb_hsv_yuv_boundary_20261001 as campaign
from colorkey_yuv_complete_limits_candidate_20261001 import candidate_source


def specifications():
    for space in (5, 6):
        for depth in ('PF8', 'PF16', 'PF32'):
            epsilon = {'PF8': independent.number(independent.bits(0.5 / 255)),
                       'PF16': 1 / 65536, 'PF32': independent.number(independent.bits(1e-6))}[depth]
            for per_color in (False, True):
                for factor in (-2, -1.000001, -1, -0.999999, -0.5, 0, 0.5, 1, 2):
                    threshold = epsilon * factor
                    params = owner.parameters(count=1, keep=True, replace=False, space=space,
                                              per_component=True, per_color=per_color, threshold=1)
                    for p in params:
                        if p['slot'] in (11, 31):
                            p['value'] = threshold
                        elif p['slot'] == 26:
                            p['color'] = [255, 26, 191, 204]
                    yield {'fixture': {'id': 'third_limit_sign', 'width': 1, 'height': 1,
                                       'rgb': [44, 75, 119], 'alpha': 255},
                           'depth': depth,
                           'label': f'space{space}_percolor{per_color}_third_factor{factor}',
                           'outside_ui_range': threshold < 0,
                           'double_threshold_hex': threshold.hex(),
                           'parameters': params}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--worker', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--production-only', action='store_true')
    args = parser.parse_args()
    assert owner.sha(args.worker.read_bytes()) == campaign.FROZEN_SHA
    source = owner.SOURCE.read_text()
    candidate = None if args.production_only else candidate_source(source)
    saved_fixture = owner.fixture
    owner.fixture = campaign.fixture
    cases = []
    try:
        with tempfile.TemporaryDirectory(prefix='olmck_yuv_third_limit_') as directory:
            temp = Path(directory)
            exes = {'production': owner.compile_public(temp / 'production', source)}
            if candidate is not None:
                exes['candidate'] = owner.compile_public(temp / 'candidate', candidate)
            for case in specifications():
                native, frame, payload, close = owner.native_render(args.worker, temp, case)
                raw, _ = campaign.fixture(case['fixture'], case['depth'])
                size = {'PF8': 4, 'PF16': 8, 'PF32': 16}[case['depth']]
                case.update(input_sha256=owner.sha(raw), packed_input_sha256=owner.sha(raw[:size]),
                            actual_sha256=owner.sha(native), raw_pixel_bytes=len(native),
                            parameter_payload=payload, frame_done=frame,
                            session_clean=close['session_clean'], unsupported_suite_calls=close['unsupported_suite_calls'],
                            results={name: independent.compare(exe, temp, case, native) for name, exe in exes.items()})
                cases.append(case)
    finally:
        owner.fixture = saved_fixture
    dependencies = [Path(__file__), Path(owner.__file__), Path(independent.__file__), Path(campaign.__file__), owner.HARNESS]
    if candidate is not None:
        dependencies += [Path(__file__).with_name('colorkey_yuv_complete_limits_candidate_20261001.py'),
                         Path(__file__).with_name('colorkey_yuv_threshold_candidate_20261001.py')]
    report = {'schema': 'olmcolorkey.yuv-third-limit/1', 'case_count': len(cases),
              'source_sha256': owner.sha(source.encode()),
              'candidate_source_sha256': owner.sha(candidate.encode()) if candidate is not None else None,
              'aex_sha256': owner.sha(owner.AEX.read_bytes()), 'frozen_worker_sha256': campaign.FROZEN_SHA,
              'dependencies_sha256': {str(p.relative_to(owner.ROOT)): owner.sha(p.read_bytes()) for p in dependencies},
              'summary': {name: {r: sum(c['results'][name][r]['exact'] for c in cases) for r in ('classic', 'smart')} for name in exes},
              'cases': cases,
              'claims_not_made': ['Negative controls are exported-owner diagnostics outside normal UI range; not a claim that UI produces them',
                                  'No native Windows UCRT/AE, malformed-project host reachability or full-input completion']}
    head = dict(report)
    del head['cases']
    text = json.dumps(head, sort_keys=True, indent=2)[:-2] + ',\n  "cases": [\n'
    text += ',\n'.join('    ' + json.dumps(c, sort_keys=True) for c in cases) + '\n  ]\n}\n'
    args.report.write_text(text)
    assert json.loads(text) == report
    print('RESULT', report['summary'], flush=True)


if __name__ == '__main__':
    main()
