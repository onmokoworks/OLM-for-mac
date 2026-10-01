#!/usr/bin/env python3
"""Test the temporary YUV limit restoration against retained native boundaries."""
import argparse
import json
import os
import tempfile
from pathlib import Path

import probe_olmcolorkey_typed_controls_20261001 as owner
import probe_olmcolorkey_rgb_hsv_yuv_boundary_20261001 as campaign
from colorkey_yuv_threshold_candidate_20261001 import candidate_source

BASE = owner.ROOT / 'reports/colorkey_rgb_hsv_yuv_boundary_baseline_20261001.json'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    base = json.loads(BASE.read_text())
    source = owner.SOURCE.read_text()
    assert owner.sha(source.encode()) == base['source_sha256']
    candidate = candidate_source(source)
    saved_fixture = owner.fixture
    owner.fixture = campaign.fixture
    rows, counts = [], {}
    env = dict(os.environ, ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',
               UBSAN_OPTIONS='halt_on_error=1')
    try:
        with tempfile.TemporaryDirectory(prefix='olmck_yuv_threshold_candidate_') as directory:
            temp = Path(directory)
            for sanitize, name in ((False, 'o2'), (True, 'asan_ubsan')):
                exe = owner.compile_public(temp / name, candidate, sanitize)
                exact = 0
                for case in base['cases']:
                    raw, _ = campaign.fixture(case['fixture'], case['depth'])
                    assert owner.sha(raw) == case['input_sha256']
                    for route in (0, 1):
                        error, out = owner.mac_render(exe, temp, case, route, env if sanitize else None)
                        match = error == 0 and owner.sha(out) == case['actual_sha256']
                        exact += match
                        rows.append({'label': case['label'], 'depth': case['depth'], 'build': name,
                                     'route': route, 'error': error, 'exact': match,
                                     'candidate_sha256': owner.sha(out), 'actual_sha256': case['actual_sha256']})
                counts[name] = {'render_count': 2 * len(base['cases']), 'exact_count': exact}
                print('YUV_THRESHOLD_CANDIDATE', name, counts[name], flush=True)
    finally:
        owner.fixture = saved_fixture
    dependencies = (Path(__file__), Path(owner.__file__), Path(campaign.__file__),
                    Path(__file__).with_name('colorkey_yuv_threshold_candidate_20261001.py'),
                    owner.HARNESS, BASE)
    report = {'schema': 'olmcolorkey.yuv-threshold-candidate-replay/1', 'summary': counts,
              'source_sha256': owner.sha(source.encode()), 'candidate_source_sha256': owner.sha(candidate.encode()),
              'dependencies_sha256': {str(p.relative_to(owner.ROOT)): owner.sha(p.read_bytes()) for p in dependencies},
              'cases': rows,
              'claims_not_made': ['Temporary candidate, not production change',
                                  'Frozen local AEX owner is not native Windows UCRT/AE',
                                  'No all-input, threshold, palette, geometry or state completion']}
    head = dict(report)
    del head['cases']
    text = json.dumps(head, sort_keys=True, indent=2)[:-2] + ',\n  "cases": [\n'
    text += ',\n'.join('    ' + json.dumps(c, sort_keys=True) for c in rows) + '\n  ]\n}\n'
    args.report.write_text(text)
    assert json.loads(text) == report


if __name__ == '__main__':
    main()
