#!/usr/bin/env python3
"""Replay exported AEX captures through the actual Mac public Smart chain."""
import argparse
import json
import os
import tempfile
from pathlib import Path

import probe_olmsmoother2_exported_color_weight_20261001 as owner

ROOT = owner.campaign.ROOT
CAPTURE = ROOT / 'reports/olmsmoother2_exported_color_weight_baseline_20261001.json'


def replay(source, capture=CAPTURE):
    data = json.loads(capture.read_text())
    assert data['case_count'] == len(data['cases']) == 252
    assert data['aex_sha256'] == owner.native_identity.AEX_SHA256
    assert data['frozen_worker_sha256'] == owner.FROZEN_SHA
    expected = list(owner.specifications())
    rows = []
    with tempfile.TemporaryDirectory(prefix='sm2_exported_replay_') as directory:
        for sanitize in (False, True):
            binary = owner.compile_public(Path(directory) / ('san' if sanitize else 'o2'), source, sanitize)
            env = dict(os.environ, ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',
                       UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
            for index, (case, specification) in enumerate(zip(data['cases'], expected)):
                for key in specification:
                    assert case[key] == specification[key], (index, key)
                assert case['parameters'] == owner.parameters(case)
                assert case['session_clean'] is True and case['unsupported_suite_calls'] == []
                frame = case['frame_done']
                assert frame['status'] == 'ok', frame
                raw, _ = owner.source_fixture(case['fixture'], case['depth'])
                assert owner.campaign.retained.sha(raw) == case['input_sha256']
                error, output, callbacks = owner.mac_render(binary, case, env)
                sha = owner.campaign.retained.sha(output) if not error else None
                exact = error == 0 and sha == case['native_raw_sha256']
                assert callbacks == [1, 1, 1, 15, 15], (index, callbacks)
                rows.append({'case_index': index, 'build': 'asan-ubsan' if sanitize else 'o2',
                             'mac_error': error, 'mac_callbacks': callbacks,
                             'production_raw_sha256': sha, 'raw_exact': exact})
            print('SM2_EXPORTED_REPLAY', 'san' if sanitize else 'o2', len(data['cases']),
                  sum(r['raw_exact'] for r in rows), flush=True)
    deps = [Path(__file__), Path(owner.__file__), owner.HARNESS, capture,
            Path(owner.campaign.__file__), Path(owner.geometry.__file__),
            Path(owner.campaign.retained.__file__),
            ROOT / 'cli/OLMSmoother2/shim/OLMSmoother2.h',
            owner.campaign.SOURCE.parent / 'OLMSmoother2_decode_lut_10000.h',
            owner.campaign.SOURCE.parent / 'OLMSmoother2_encode_lut_10000.h']
    return {'schema': 'olmsmoother2.exported-color-weight-replay/1',
            'source_sha256': owner.campaign.retained.sha(source.encode()),
            'dependencies_sha256': {str(p.relative_to(ROOT)): owner.campaign.retained.sha(p.read_bytes()) for p in deps},
            'case_count': data['case_count'], 'render_count': len(rows),
            'summary': {'raw_exact_count': sum(r['raw_exact'] for r in rows)}, 'rows': rows,
            'claims_not_made': data['claims_not_made']}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, default=owner.campaign.SOURCE)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    report = replay(args.source.read_text())
    args.report.write_text(json.dumps(report, sort_keys=True, indent=2) + '\n')
    assert report['summary']['raw_exact_count'] == report['render_count'] == 504, report['summary']
    print('RESULT', report['summary'], flush=True)


if __name__ == '__main__':
    main()
