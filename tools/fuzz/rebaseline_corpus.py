#!/usr/bin/env python3
"""Refresh saved results in a fuzz corpus from a replay report.

A replay report is produced by run.py --replay. This tool changes only the
recorded `result` and `provenance` of cases whose measured outcome differs from
the saved one; case inputs, operations and reductions stay untouched. A route
that was exact may not become non-exact, and a measured mismatch may not become
a refusal, so an ordinary re-baseline cannot hide a regression. The explicit
--route-correction migration allows changed Classic verdicts with identical
candidate bytes/metadata and retains the previous result for audit.
The explicit --production-rebaseline migration additionally permits mismatch
to refusal, preserves history, and rejects changed exact hashes or oracle drift.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]


def load(path):
    return json.loads(path.read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plugin', required=True)
    parser.add_argument('--corpus', type=Path, required=True,
                        help='Corpus directory. Paths recorded in the report must be inside it')
    parser.add_argument('--report', type=Path, required=True,
                        help='Replay report produced by run.py --replay')
    parser.add_argument('--route-correction', action='store_true',
                        help='Allow comparator-only changes with identical candidate hashes; preserve previous results')
    parser.add_argument('--production-rebaseline', metavar='TICKET',
                        help='Apply the production transition policy and retain previous result/provenance')
    args = parser.parse_args()
    if args.production_rebaseline and args.route_correction:
        raise SystemExit('production rebaseline and route correction are separate migrations')

    report = load(args.report)
    if report.get('plugin') != args.plugin:
        raise SystemExit(f"report plugin {report.get('plugin')!r} != {args.plugin!r}")
    if report.get('status') != 'replay_complete' or not report.get('replays') or report.get('completed') != report.get('requested'):
        raise SystemExit('need a complete, nonempty replay report')
    paths = [Path(row['path']).resolve() for row in report['replays']]
    if len(paths) != report['completed'] or len(set(paths)) != len(paths):
        raise SystemExit('replay count mismatch or duplicate case paths')
    corpus = args.corpus.resolve()
    provenance = report.get('provenance')
    if provenance is None and not report.get('replay_groups'):
        raise SystemExit('replay report has no provenance')
    transitions = Counter()
    changed = 0
    updates = []
    for row in report.get('replays', []):
        path = Path(row['path']).resolve()
        if not path.is_relative_to(corpus):
            raise SystemExit(f'{path} is outside {corpus}')
        data = load(path)
        if data.get('plugin') != args.plugin:
            raise SystemExit(f'{path} plugin {data.get("plugin")!r} != {args.plugin!r}')
        saved, observed = data['result'], row['result']
        row_provenance = provenance
        if report.get('replay_groups'):
            group = report['replay_groups'][row['group']]
            if str(path) not in [str(Path(p).resolve()) for p in group['paths']]:
                raise SystemExit(f'{path.name}: replay group does not own this case')
            row_provenance = group['provenance']
        if args.production_rebaseline:
            if saved['oracle'] != observed['oracle']:
                raise SystemExit(f'{path.name}: primary oracle drift')
            if 'oracles' in saved and saved['oracles'] != observed.get('oracles'):
                raise SystemExit(f'{path.name}: route oracle drift')
            if saved['routes'].keys() != observed['routes'].keys():
                raise SystemExit(f'{path.name}: route set changed')
        for route, before in saved['routes'].items():
            after = observed['routes'][route]
            transitions[(route, before['status'], after['status'])] += 1
            correction = False
            if args.route_correction:
                if 'oracles' not in observed or row_provenance.get('oracle_routes', {}).get(route) != route:
                    raise SystemExit(f'{path.name}: missing matching-route provenance')
                if before.get('raw_sha256') != after.get('raw_sha256'):
                    raise SystemExit(f'{path.name}: candidate bytes changed on {route}; not comparator-only')
                candidate_before = {k:v for k,v in before.items() if k not in ('status','diff')}
                candidate_after = {k:v for k,v in after.items() if k not in ('status','diff')}
                if candidate_before != candidate_after or (not before.get('raw_sha256') and before != after):
                    raise SystemExit(f'{path.name}: candidate metadata/status changed on {route}')
                new_oracle = observed['oracles'][route]
                correction = (route == 'classic' and 'oracles' not in saved)
                if not correction and before != after:
                    raise SystemExit(f'{path.name}: unchanged-owner {route} result drift')
                if new_oracle['status'] in ('budget', 'harness_error'):
                    raise SystemExit(f'{path.name}: cannot baseline transient/invalid {route} oracle')
            if not correction and before['status'] == 'exact' and after['status'] != 'exact':
                raise SystemExit(f'{path.name} loses exact {route}: {before["status"]} -> {after["status"]}')
            if args.production_rebaseline and before != after:
                start, end = before['status'], after['status']
                allowed = (end == 'exact' or (start, end) in
                           {('mismatch', 'mismatch'), ('mismatch', 'refusal'), ('refusal', 'refusal')})
                if start == end and start in ('exact', 'refusal') and before.get('raw_sha256') != after.get('raw_sha256'):
                    allowed = False
                if not allowed:
                    raise SystemExit(f'{path.name}: forbidden production transition on {route}: {start} -> {end}')
            if not args.production_rebaseline and before['status'] == 'mismatch' and after['status'] == 'refusal':
                raise SystemExit(f'{path.name} regresses {route}: mismatch -> refusal')
        if saved != observed:
            if args.route_correction:
                data['route_oracle_update'] = {'ticket':'F17-fuzz-per-route-oracle', 'previous_result':saved}
            if args.production_rebaseline:
                data.setdefault('rebaseline_history', []).append({
                    'ticket': args.production_rebaseline,
                    'previous_result': saved,
                    'previous_provenance': data.get('provenance'),
                })
            data['result'] = observed
            data['provenance'] = row_provenance
            updates.append((path, data))
            changed += 1

    # Validate the entire replay before mutating any corpus entry.
    for path, data in updates:
        path.write_text(json.dumps(data, sort_keys=True, indent=2) + '\n')

    table = [{'route': route, 'before': before, 'after': after, 'cases': count}
             for (route, before, after), count in sorted(transitions.items())]
    print(json.dumps({'plugin': args.plugin, 'corpus': str(corpus), 'changed': changed,
                      'transitions': table}, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    sys.exit(main())
