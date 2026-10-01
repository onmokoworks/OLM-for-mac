#!/usr/bin/env python3
"""Recapture historical counterexamples without modifying their input or oracle hashes."""
import argparse
import copy
import json
import tempfile
from pathlib import Path

import probe_olmcolorkey_typed_controls_20261001 as owner
import probe_olmcolorkey_lab_state_boundary_20261001 as independent
import probe_olmcolorkey_rgb_hsv_yuv_boundary_20261001 as boundary
import probe_olmcolorkey_finite_overflow_20261001 as overflow


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--worker', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    assert owner.sha(args.worker.read_bytes()) == boundary.FROZEN_SHA
    source = owner.SOURCE.read_text()
    definitions = (('rgb_hsv_yuv_boundary', boundary.fixture),
                   ('finite_overflow', overflow.fixture),
                   ('yuv_third_limit', boundary.fixture))
    dependencies = [Path(__file__), Path(owner.__file__), Path(independent.__file__),
                    Path(boundary.__file__), Path(overflow.__file__), owner.HARNESS]
    saved_fixture = owner.fixture
    cases, groups = [], {}
    try:
        with tempfile.TemporaryDirectory(prefix='olmck_yuv_limits_recapture_') as directory:
            temp = Path(directory)
            exe = owner.compile_public(temp / 'production', source)
            for name, fixture in definitions:
                base_path = owner.ROOT / f'reports/colorkey_{name}_baseline_20261001.json'
                dependencies.append(base_path)
                base = json.loads(base_path.read_text())
                owner.fixture = fixture
                selected = []
                for old in base['cases']:
                    old_results = old['results'] if name == 'rgb_hsv_yuv_boundary' else old['results']['production']
                    if not all(old_results[r]['exact'] for r in ('classic', 'smart')):
                        selected.append(old)
                groups[name] = len(selected)
                for old in selected:
                    case = copy.deepcopy(old)
                    raw, _ = fixture(case['fixture'], case['depth'])
                    assert owner.sha(raw) == old['input_sha256']
                    native, frame, payload, close = owner.native_render(args.worker, temp, case)
                    assert owner.sha(native) == old['actual_sha256'], case['label']
                    assert payload == old['parameter_payload'], case['label']
                    case.update(baseline_report=str(base_path.relative_to(owner.ROOT)),
                                baseline_results=old['results'], frame_done=frame,
                                session_clean=close['session_clean'], unsupported_suite_calls=close['unsupported_suite_calls'],
                                results=independent.compare(exe, temp, case, native))
                    cases.append(case)
                print('YUV_LIMITS_RECAPTURE', name, len(selected), flush=True)
    finally:
        owner.fixture = saved_fixture
    report = {'schema': 'olmcolorkey.yuv-limits-recapture/1', 'case_count': len(cases),
              'groups': groups, 'source_sha256': owner.sha(source.encode()),
              'summary': {r: sum(c['results'][r]['exact'] for c in cases) for r in ('classic', 'smart')},
              'dependencies_sha256': {str(p.relative_to(owner.ROOT)): owner.sha(p.read_bytes()) for p in dependencies},
              'aex_sha256': owner.sha(owner.AEX.read_bytes()), 'frozen_worker_sha256': boundary.FROZEN_SHA,
              'input_settings_native_hashes_preserved': True, 'cases': cases,
              'claims_not_made': ['Historical counterexample recapture, not full input/state verification',
                                  'Third-threshold negative controls are outside normal UI range',
                                  'Local exported AEX owner is not native Windows UCRT/AE']}
    head = dict(report)
    del head['cases']
    text = json.dumps(head, sort_keys=True, indent=2)[:-2] + ',\n  "cases": [\n'
    text += ',\n'.join('    ' + json.dumps(c, sort_keys=True) for c in cases) + '\n  ]\n}\n'
    args.report.write_text(text)
    assert json.loads(text) == report
    print('RESULT', report['summary'], flush=True)


if __name__ == '__main__':
    main()
