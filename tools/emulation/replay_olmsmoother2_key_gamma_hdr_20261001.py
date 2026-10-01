#!/usr/bin/env python3
"""Replay key/gamma and typed-HDR public owner captures without changing oracle hashes."""
import argparse
import json
import os
import tempfile
from pathlib import Path

import probe_olmsmoother2_key_gamma_hdr_20261001 as probe

CAPTURES = {matrix: probe.ROOT / 'reports' / filename for matrix, filename in (
    ('controls', 'olmsmoother2_public_key_gamma_baseline_20261001.json'),
    ('hdr', 'olmsmoother2_public_typed_hdr_baseline_20261001.json'))}


def replay(source):
    rows = []; captures = {matrix: json.loads(path.read_text()) for matrix, path in CAPTURES.items()}
    env = dict(os.environ, ASAN_OPTIONS='detect_leaks=0:halt_on_error=1', UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
    with tempfile.TemporaryDirectory(prefix='sm2_key_gamma_hdr_replay_') as directory:
        temp = Path(directory)
        for sanitize in (False, True):
            binary = probe.compile_public(temp / ('san' if sanitize else 'o2'), source, sanitize)
            for matrix, data in captures.items():
                specifications = list(probe.specifications(matrix))
                assert data['case_count'] == len(data['cases']) == len(specifications)
                assert data['aex_sha256'] == probe.retained.native_identity.AEX_SHA256
                assert data['frozen_worker_sha256'] == probe.retained.FROZEN_SHA
                for dependency, expected in data['dependencies_sha256'].items():
                    assert probe.sha((probe.ROOT / dependency).read_bytes()) == expected, dependency
                for index, (case, specification) in enumerate(zip(data['cases'], specifications)):
                    assert all(case[key] == value for key, value in specification.items())
                    raw, _ = probe.fixture(case['fixture'], case['depth'])
                    assert probe.sha(raw) == case['input_sha256']
                    assert case['frame_done']['status'] == 'ok' and case['frame_done']['render_error'] == 0
                    assert case['frame_done']['output']['guards_intact'] is True
                    assert case['session_clean'] is True and case['unsupported_suite_calls'] == []
                    error, output, callbacks = probe.mac_render(binary, temp, case, env)
                    assert callbacks == [1, 1, 1, 15, 15, 1], (matrix, index, callbacks)
                    output_sha = probe.sha(output) if not error else None
                    rows.append({'matrix': matrix, 'case_index': index, 'build': 'asan-ubsan' if sanitize else 'o2',
                                 'mac_error': error, 'mac_callbacks': callbacks, 'production_raw_sha256': output_sha,
                                 'raw_exact': not error and output_sha == case['native_raw_sha256']})
                print('SM2_KEY_GAMMA_HDR_REPLAY', 'san' if sanitize else 'o2', matrix,
                      data['case_count'], sum(r['raw_exact'] for r in rows), flush=True)
    deps = [Path(__file__), Path(probe.__file__), probe.HARNESS, *CAPTURES.values()]
    return {'schema': 'olmsmoother2.public-key-gamma-hdr-replay/1', 'source_sha256': probe.sha(source.encode()),
            'dependencies_sha256': {str(p.relative_to(probe.ROOT)): probe.sha(p.read_bytes()) for p in deps},
            'case_count': sum(c['case_count'] for c in captures.values()), 'render_count': len(rows),
            'summary': {'raw_exact_count': sum(r['raw_exact'] for r in rows)}, 'rows': rows,
            'claims_not_made': captures['controls']['claims_not_made']}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, default=probe.SOURCE)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    report = replay(args.source.read_text())
    args.report.write_text(json.dumps(report, sort_keys=True, indent=2) + '\n')
    assert report['render_count'] == report['summary']['raw_exact_count'] == 3384, report['summary']
    print('RESULT', report['summary'], flush=True)


if __name__ == '__main__':
    main()
