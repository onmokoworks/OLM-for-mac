#!/usr/bin/env python3
"""Serial F53/T24 live-capture replay, preserving reports and worker artifacts."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

sys.dont_write_bytecode = True
from replay_aex import replay, sha_file

ROOT = Path(__file__).resolve().parents[2]
TICKET = 'T24-aexcompat-worker-32bpc-arena'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--captures', type=Path, default=Path.home()/'Downloads/olm_mac_check_20261105')
    parser.add_argument('--scratch', type=Path, default=ROOT/'orchestra/state'/TICKET/'live')
    parser.add_argument('--worker', type=Path, default=Path.home()/'.cache/olm-emu/worker-T24-arena/aex-guest-worker')
    parser.add_argument('--main', type=Path, default=ROOT.parent.parent)
    args = parser.parse_args()
    args.scratch = args.scratch.resolve()
    args.scratch.mkdir(parents=True, exist_ok=True)
    old = Path.home()/'.cache/olm-emu/worker-F53-geom/aex-guest-worker'
    records = []
    expected_blocked = {'OLMRadialBlur-smart-G66uct', 'OLMRadialBlur-smart-GrJ092'}
    compare_keys = ('status', 'different_words', 'different_pixels', 'max_diff', 'first',
                    'aex_output_sha256', 'mac_output_sha256')
    for ticket in ('T22', 'T23'):
        root = args.captures/f'live_capture_{ticket}'
        for capture in sorted((root/'caps').iterdir()):
            if not (capture/'capture.json').is_file():
                continue
            free = int(re.search(r'System-wide memory free percentage: (\d+)%',
                                 subprocess.check_output(['memory_pressure'], text=True))[1])
            assert free >= 30, f'Memory pressure: {free}% free'
            record = dict(ticket=ticket, capture=capture.name, capture_metadata_sha256=sha_file(capture/'capture.json'),
                          memory_free_percent=free)
            for label, worker in (('old', old), ('new', args.worker)):
                directory = args.scratch/capture.name/label
                directory.mkdir(parents=True, exist_ok=True)
                try:
                    result = replay(capture, directory, worker, args.main, timeout=1200)
                except Exception as exc:
                    result = dict(status='unsupported_or_error', error=str(exc))
                (directory/'result.json').write_text(json.dumps(result, indent=2)+'\n')
                record[label] = result
                print(capture.name, label, result['status'], result.get('different_words'), flush=True)
            before, after = record['old'], record['new']
            if capture.name in expected_blocked:
                record['passes'] = before['status'] == 'unsupported_or_error' and after['status'] in ('exact', 'mismatch')
            else:
                record['passes'] = before['status'] in ('exact', 'mismatch') and all(before.get(k) == after.get(k) for k in compare_keys)
            saved = root/'replay'/(capture.name+'.log')
            if saved.is_file():
                prior = json.loads(saved.read_text())
                # Existing logs predate max_ulp / numeric first-value reporting.
                record['matches_saved_log'] = all(before.get(k) == prior.get(k) for k in compare_keys)
                record['passes'] &= record['matches_saved_log']
            records.append(record)
            (args.scratch/'summary.json').write_text(json.dumps(records, indent=2)+'\n')
    passed = sum(r['passes'] for r in records)
    print(f'{passed}/{len(records)} live checks passed', flush=True)
    return 0 if passed == len(records) else 1


if __name__ == '__main__':
    sys.exit(main())
