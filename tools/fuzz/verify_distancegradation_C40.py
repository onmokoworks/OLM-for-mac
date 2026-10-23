#!/usr/bin/env python3
"""Replay candidate against hash-bound, unshrunk C40 baseline campaign oracles.

The baseline files are ordinary run.py n300 reports (optionally gzip compressed).
No oracle is inferred from the old Mac result: classification uses each original
AEX route's SHA-256, after regenerating and checking the input SHA-256.
"""
import argparse
from collections import Counter
import gzip
import json
import os
from pathlib import Path
import tempfile
import time
from types import SimpleNamespace

from adapters.olmdistancegradation import Adapter, SOURCE
from core import sha
from run import main_checkout, default_worker


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline-dir', type=Path, required=True)
    parser.add_argument('--scratch', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--source', type=Path, help='Optional scratch admission candidate')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    scratch = args.scratch.resolve()
    if not scratch.is_relative_to(root/'orchestra/state/C40-dg-seed45-mismatch'):
        parser.error('scratch must be under this ticket state directory')
    scratch.mkdir(parents=True, exist_ok=True)
    os.environ.update(TMPDIR=str(scratch), TMP=str(scratch), TEMP=str(scratch))
    deadline = time.monotonic() + 1800
    adapter = Adapter(SimpleNamespace(main=main_checkout(), worker=default_worker(),
                                     max_size=256, case_timeout=60))
    report = {'schema': 'olm-C40-cached-oracle/1', 'seeds': [],
              'source_sha256': sha((args.source or SOURCE).read_bytes()),
              'comparison': 'candidate bytes SHA256 versus original AEX SHA256; input regenerated and hash checked'}
    with tempfile.TemporaryDirectory(dir=scratch, prefix='verify_') as name:
        directory = Path(name)
        if args.source:
            from verify_distancegradation_smart_C08 import variant
            adapter = variant(adapter, directory/'build', deadline, args.source.read_text())
        else:
            adapter.binary, _ = adapter.build(directory, deadline)
        for seed in (1, 44, 45, 46):
            path = args.baseline_dir/f'baseline-{seed}.json'
            if path.exists():
                data = path.read_bytes()
            else:
                path = path.with_suffix('.json.gz')
                data = gzip.decompress(path.read_bytes())
            baseline = json.loads(data)
            assert baseline['status'] == 'complete' and baseline['completed'] == 300
            assert baseline['seed'] == seed and baseline['plugin'] == adapter.name
            assert baseline['generator_version'] == adapter.generator_version
            counts, old_counts, losses, changes, rows = Counter(), Counter(), [], [], []
            for old in baseline['cases']:
                case = adapter.generate(seed, old['index'])
                assert sha(case['pixels']) == old['input_sha256']
                for key in ('parameters', 'geometry', 'depth', 'input_padding', 'output_padding', 'profile'):
                    assert case[key] == old[key], (seed, old['index'], key)
                result = {}
                for route in adapter.routes:
                    value, raw, guards = adapter.candidate(case, directory, route, deadline)
                    oracle = old['result']['oracles'][route]
                    if value['status'] == 'ok':
                        value['raw_sha256'] = sha(raw)
                        value['status'] = ('exact' if value['raw_sha256'] == oracle['raw_sha256'] else 'mismatch') if oracle['status'] == 'ok' else 'uncompared'
                    previous = old['result']['routes'][route]
                    counts[route+'_'+value['status']] += 1
                    old_counts[route+'_'+previous['status']] += 1
                    if previous['status'] == 'exact' and value['status'] != 'exact':
                        losses.append({'index': old['index'], 'route': route, 'to': value['status']})
                    if previous['status'] != value['status']:
                        changes.append({'index': old['index'], 'route': route, 'from': previous['status'], 'to': value['status'], 'guards': guards})
                    result[route] = value
                rows.append({'index': old['index'], 'input_sha256': old['input_sha256'], 'routes': result})
            item = {'seed': seed, 'completed': len(rows), 'baseline_sha256': sha(data),
                    'baseline_summary': dict(old_counts), 'summary': dict(counts),
                    'exact_losses': losses, 'transitions': changes, 'cases': rows}
            report['seeds'].append(item)
            print(seed, json.dumps({k:v for k,v in item.items() if k != 'cases'}), flush=True)
    report['acceptance_met'] = all(not row['exact_losses'] and
                                   row['summary'].get('smart_mismatch', 0) == 0
                                   for row in report['seeds'])
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, sort_keys=True, indent=2)+'\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
