#!/usr/bin/env python3
"""Replay retained exported Smart gamma compositions against current source."""
import argparse
import json
import os
import tempfile
from pathlib import Path

import probe_olmsmoother2_gamma_composition_20261001 as probe

CAPTURES = {matrix: probe.ROOT / 'reports' / file for matrix, file in (
    ('hdr', 'olmsmoother2_gamma_hdr_composition_baseline_20261001.json'),
    ('tolerance', 'olmsmoother2_membership_tolerance_baseline_20261001.json'))}


def replay(source):
    rows = []
    with tempfile.TemporaryDirectory(prefix='sm2_gamma_composition_replay_') as directory:
        temp = Path(directory)
        for sanitize in (False, True):
            binary = probe.base.compile_public(temp / ('san' if sanitize else 'o2'), source, sanitize)
            env = dict(os.environ, ASAN_OPTIONS='detect_leaks=0:halt_on_error=1', UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
            for matrix, path in CAPTURES.items():
                data = json.loads(path.read_text()); expected = list(probe.specifications(matrix))
                assert data['case_count'] == len(expected) == len(data['cases'])
                assert data['aex_sha256'] == probe.base.retained.native_identity.AEX_SHA256
                assert data['frozen_worker_sha256'] == probe.base.retained.FROZEN_SHA
                for dependency, sha in data['dependencies_sha256'].items():
                    assert probe.base.sha((probe.ROOT / dependency).read_bytes()) == sha, dependency
                for index, (case, specification) in enumerate(zip(data['cases'], expected)):
                    assert all(case[key] == value for key, value in specification.items())
                    raw, _ = probe.fixture(case['fixture'], case['depth'])
                    assert probe.base.sha(raw) == case['input_sha256']
                    assert case['frame_done']['status'] == 'ok' and case['frame_done']['output']['guards_intact']
                    assert case['session_clean'] is True and case['unsupported_suite_calls'] == []
                    error, output, callbacks = probe.mac_render(binary, temp, case, env)
                    assert callbacks == [1, 1, 1, 15, 15, 1], (matrix, index, callbacks)
                    output_sha = probe.base.sha(output) if not error else None
                    rows.append({'matrix': matrix, 'case_index': index, 'build': 'asan-ubsan' if sanitize else 'o2',
                                 'mac_error': error, 'production_raw_sha256': output_sha,
                                 'raw_exact': not error and output_sha == case['native_raw_sha256']})
                print('SM2_GAMMA_COMPOSITION_REPLAY', 'san' if sanitize else 'o2', matrix,
                      data['case_count'], sum(r['raw_exact'] for r in rows), flush=True)
    deps = [Path(__file__), Path(probe.__file__), Path(probe.base.__file__), probe.base.HARNESS, *CAPTURES.values()]
    return {'schema': 'olmsmoother2.gamma-composition-replay/1', 'source_sha256': probe.base.sha(source.encode()),
            'case_count': 2280, 'render_count': len(rows), 'summary': {'raw_exact_count': sum(r['raw_exact'] for r in rows)},
            'dependencies_sha256': {str(p.relative_to(probe.ROOT)): probe.base.sha(p.read_bytes()) for p in deps}, 'rows': rows,
            'claims_not_made': json.loads(CAPTURES['hdr'].read_text())['claims_not_made']}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, default=probe.SOURCE)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    report = replay(args.source.read_text())
    args.report.write_text(json.dumps(report, sort_keys=True, indent=2) + '\n')
    assert report['render_count'] == report['summary']['raw_exact_count'] == 4560, report['summary']
    print('RESULT', report['summary'], flush=True)


if __name__ == '__main__':
    main()
