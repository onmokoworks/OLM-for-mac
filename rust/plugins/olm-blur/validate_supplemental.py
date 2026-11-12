#!/usr/bin/env python3
"""Untouched defaults and full-frame SmartPreRender regression via the owned-job oracle."""
from pathlib import Path
import argparse
import concurrent.futures
import importlib.util
import json

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('olm_oracle', ROOT / 'rust/tools/oracle/olm_oracle.py')
oracle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(oracle)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    identities = {'harness': oracle.identity(oracle.DEFAULT_HARNESS),
                  'reference': oracle.identity(args.reference),
                  'candidate': oracle.identity(args.candidate),
                  'tool': oracle.identity(oracle.__file__), 'corpus': oracle.identity(__file__)}
    inv = {side: oracle.inspect(oracle.DEFAULT_HARNESS, Path(identities[side]['path']), 60)
           for side in ('reference', 'candidate')}
    cases = []
    for index in range(6):
        cases.append({'index': index, 'size': [11, 7], 'input_seed': 0xB10B + index,
                      'downsample': ['1', '1/2', '1/4'][index % 3],
                      'assignments': [] if index < 3 else [{'slot': 1, 'value': 17.25},
                          {'slot': 2, 'value': 31.875}, {'slot': 3, 'value': 4},
                          {'slot': 4, 'value': 2}, {'slot': 5, 'value': index % 2}],
                      'unassigned': list(range(1,6)) if index < 3 else [],
                      'label': 'untouched-defaults' if index < 3 else 'cropped-demand'})
    oracle.write_json(out/'cases.json', cases)
    routes = ['smart8', 'smart16', 'smart32']
    summary = {**identities, 'cases': len(cases), 'jobs': 3, 'timeout_seconds': 120,
               'render_environment_overrides': oracle.frame_deadline_environment(120),
               'inventory_diff': oracle.inventory_diff(inv['reference'], inv['candidate']),
               'results': [], 'complete': False}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(oracle.run_case, out, case, route, identities, (),
                    None if case['index'] < 3 else [1,1,6,5], 120)
                   for case in cases for route in routes]
        for future in concurrent.futures.as_completed(futures):
            summary['results'].append(future.result())
            summary['routes'] = oracle.summarize(summary['results'], {r: None for r in routes})
            oracle.write_json(out/'summary.json', summary)
    summary['complete'] = True
    summary['exit_code'] = oracle.exit_code(summary)
    oracle.write_json(out/'summary.json', summary)
    oracle.print_table(summary)
    return summary['exit_code']

if __name__ == '__main__':
    raise SystemExit(main())
