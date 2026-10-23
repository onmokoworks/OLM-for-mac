#!/usr/bin/env python3
"""Validate and compact the four-seed C20 Smart-route census."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIAGNOSTIC = ('aex_guest_error: selector SMART_RENDER failed in guest: unsupported '
              'Win64 import: api-ms-win-crt-math-l1-1-0.dll!atan2f\n')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--scratch', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    historical = json.loads((ROOT/'reports/fuzz/colorkey_F20.json').read_text())
    campaigns = []
    for seed, exact in enumerate((299, 293, 292, 291), 1):
        plain_path = args.scratch/f'seed{seed}.json'
        sanitized_path = args.scratch/f'sanitize{seed}.json'
        plain = json.loads(plain_path.read_text())
        sanitized = json.loads(sanitized_path.read_text())
        for report in (plain, sanitized):
            assert report['status'] == 'complete'
            assert report['completed'] == report['requested'] == 300
            assert report['seed'] == seed and report['jobs'] == 1
            assert not report['deadline_reached']
        assert sanitized['provenance']['triage']['sanitizers']
        assert not plain['provenance']['triage']['sanitizers']
        rows = []
        for a, b in zip(plain['cases'], sanitized['cases']):
            assert (a['index'], a['input_sha256'], a['parameters']) == (b['index'], b['input_sha256'], b['parameters'])
            assert a['result'] == b['result'], (seed, a['index'], 'sanitized output changed')
            assert not any(r.get('sanitizer') for r in b['result']['routes'].values())
            smart = a['result']['routes']['smart']
            oracle = a['result']['oracles']['smart']
            assert smart['status'] in ('exact', 'uncompared')
            if smart['status'] == 'uncompared':
                assert oracle == {'status':'reject', 'returncode':1, 'diagnostic':DIAGNOSTIC}
            else:
                assert oracle['status'] == 'ok'
                assert oracle['raw_sha256'] == smart['raw_sha256']
            if seed == 1:
                old = historical['campaign_cases'][a['index']]
                assert old['input_sha256'] == a['input_sha256']
                assert old['after']['routes']['smart'] == smart
                assert old['after']['oracles']['smart'] == oracle
            rows.append({k:a[k] for k in ('index','input_sha256','depth','geometry','profile')} |
                        dict(oracle=oracle, smart=smart,
                             classifier_controls={str(p['slot']):p['value']
                                 for p in a['parameters'] if p['slot'] in (5,8)}))
        counts = dict(Counter(r['smart']['status'] for r in rows))
        assert counts == {'exact':exact, 'uncompared':300-exact}
        campaigns.append(dict(seed=seed, counts=counts, sanitizer_affected_routes=0,
            sanitized_result_dictionaries_unchanged=300, cases=rows,
            provenance=plain['provenance'], sanitizer_provenance=sanitized['provenance'],
            framework_sha256=plain['framework_sha256'], generator_version=plain['generator_version'],
            report_sha256=digest(plain_path), sanitizer_report_sha256=digest(sanitized_path)))
    replay = json.loads((args.scratch/'replay.json').read_text())
    assert replay['status'] == 'replay_complete'
    assert replay['requested'] == replay['completed'] == 3
    assert all(r['matches_saved'] and r['result']['routes']['smart']['status']=='exact'
               for r in replay['replays'])
    result = dict(schema='olm-colorkey-C20/1', campaigns=campaigns, replay=replay,
        f20_seed1_smart_results_unchanged=300, smart_exact=1175, smart_uncompared=25,
        smart_mismatch=0, smart_refusal=0, sanitizer_affected_routes=0,
        limitations=['25 original Smart calls reject unsupported atan2f; no output exists to compare.',
                     'CPU emulation/fake SDK host only; no native Windows UCRT or AE claim.',
                     'Leak checking disabled; no worker rebuilt; no production change.'])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
    print('C20: 1175 Smart exact; 25 atan2f oracle rejects; 0 mismatch/refusal; '
          '2400 sanitized route executions clean; F20 seed1 unchanged 300/300; corpus 3/3 unchanged')


if __name__ == '__main__':
    main()
