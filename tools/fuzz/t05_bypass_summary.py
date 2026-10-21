#!/usr/bin/env python3
"""Summarize the T05 RadialBlur admission-gate bypass campaigns.

Reads the T03 baseline census plus the per-gate campaigns produced with
OLM_RADIAL_CANDIDATE_BYPASS and the all-bypass ASan/UBSan campaign. Prints the
per-gate unblocked/exact/mismatch/error tables and mismatch clusters. This is
measurement-only; it does not change any plugin behavior.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT/'reports/fuzz/radialblur_20261021.json'
GATES = (
    ('unadmitted-zoom-profile', 'zoom_profile'),
    ('generic-world-not-admitted', 'generic_world'),
    ('unadmitted-rotation-profile', 'rotation_profile'),
    ('type3-zero-noise', 'type3_zero_noise'),
    ('unadmitted-zoom-noise-inner-profile', 'zoom_noise_inner'),
    ('unadmitted-two-stage-profile', 'two_stage'),
)
ALL = ROOT/'reports/fuzz/radialblur_t05_bypass_all_20261021.json'
SANITIZE = ROOT/'reports/fuzz/radialblur_t05_bypass_all_sanitize_20261021.json'
DEFAULT_SANITIZE = ROOT/'reports/fuzz/radialblur_t05_default_sanitize_control_20261021.json'


def tag(entry: str) -> str:
    return entry.rsplit('@', 1)[0].split(':', 1)[1]


def guards(row: dict, route: str) -> set[str]:
    return {tag(entry) for entry in row.get('refusal_guards', {}).get(route, [])}


def load_rows(path: Path) -> dict[int, dict]:
    report = json.loads(path.read_text())
    return {row['index']: row for row in report['cases'] if 'worker_error' not in row}


def statuses(row: dict) -> dict[str, dict]:
    return row['result']['routes']


def classify(status: dict) -> str:
    value = status['status']
    if value in ('exact', 'mismatch', 'uncompared'):
        return value
    if value == 'refusal':
        return 'still_refused'
    if value in ('error', 'harness_error'):
        code = status.get('returncode')
        return 'crash' if isinstance(code, int) and code < 0 else 'new_error'
    return value


def summarize_gate(gate: str | None, baseline: dict[int, dict], campaign: dict[int, dict],
                   sanitized: dict[int, dict]) -> dict:
    route_rows = Counter()
    cases = Counter()
    clusters = Counter()
    remaining = Counter()
    ub_rows = Counter()
    for index, base in baseline.items():
        target = {tag for tag, _ in GATES} if gate is None else {gate}
        target_routes = [route for route in ('classic', 'smart')
                         if target & guards(base, route)]
        if not target_routes:
            continue
        cases['cases'] += 1
        saw_unblocked = False
        for route in target_routes:
            route_rows['rows'] += 1
            status = statuses(campaign[index])[route]
            outcome = classify(status)
            route_rows[outcome] += 1
            if outcome == 'still_refused':
                for entry in campaign[index].get('refusal_guards', {}).get(route, []):
                    remaining[tag(entry)] += 1
            if outcome in ('exact', 'mismatch', 'uncompared'):
                saw_unblocked = True
                route_rows['unblocked'] += 1
                if outcome == 'mismatch' and 'cluster' in campaign[index]:
                    clusters[campaign[index]['cluster']] += 1
            if sanitized.get(index, {}).get('result', {}).get('routes', {}).get(route, {}).get('sanitizer'):
                ub_rows[route] += 1
        if saw_unblocked:
            cases['unblocked'] += 1
            outcomes = {classify(statuses(campaign[index])[route]) for route in target_routes}
            if 'mismatch' in outcomes:
                cases['mismatch'] += 1
            elif 'exact' in outcomes:
                cases['exact'] += 1
            elif 'uncompared' in outcomes:
                cases['uncompared'] += 1
        elif all(classify(statuses(campaign[index])[route]) == 'still_refused'
                 for route in target_routes):
            cases['still_refused'] += 1
        else:
            cases['other'] += 1
    route_rows['ub_rows'] = sum(ub_rows.values())
    return {'route_rows': route_rows, 'cases': cases, 'clusters': clusters,
            'remaining': remaining, 'ub_by_route': ub_rows}


def table_row(label: str, result: dict) -> str:
    rows = result['route_rows']
    cases = result['cases']
    return (f"| {label} | {rows['rows']} | {rows.get('unblocked', 0)} | "
            f"{rows.get('exact', 0)} | {rows.get('mismatch', 0)} | "
            f"{rows.get('uncompared', 0)} | {rows.get('still_refused', 0)} | "
            f"{rows.get('crash', 0)} | {rows.get('new_error', 0)} | "
            f"{rows.get('budget', 0)} | {rows['ub_rows']} | "
            f"{cases['cases']} | {cases.get('unblocked', 0)} | "
            f"{cases.get('exact', 0)} | {cases.get('mismatch', 0)} |")


def main() -> None:
    baseline = load_rows(BASELINE)
    sanitized = load_rows(SANITIZE)
    print('| gate | route rows | unblocked | exact | mismatch | uncompared | '
          'still refused | crash | new error | budget | UB rows | cases | '
          'cases unblocked | cases exact | cases mismatch |')
    print('|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|')
    results = {}
    for gate, name in GATES:
        campaign = load_rows(ROOT/f'reports/fuzz/radialblur_t05_bypass_{name}_20261021.json')
        result = summarize_gate(gate, baseline, campaign, sanitized)
        results[gate] = result
        print(table_row(gate, result))
    all_campaign = load_rows(ALL)
    all_result = summarize_gate(None, baseline, all_campaign, sanitized)
    print(table_row('ALL SIX', all_result))

    print('\nOutcome for each gate population when ALL SIX gates are lifted '
          '(route rows; same baseline population as above):')
    print('| gate population | route rows | unblocked | exact | mismatch | '
          'uncompared | still refused | crash | new error | budget |')
    print('|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|')
    for gate, _ in GATES:
        result = summarize_gate(gate, baseline, all_campaign, sanitized)
        rows = result['route_rows']
        print(f"| {gate} | {rows['rows']} | {rows.get('unblocked', 0)} | "
              f"{rows.get('exact', 0)} | {rows.get('mismatch', 0)} | "
              f"{rows.get('uncompared', 0)} | {rows.get('still_refused', 0)} | "
              f"{rows.get('crash', 0)} | {rows.get('new_error', 0)} | "
              f"{rows.get('budget', 0)} |")

    print('\nStill-refused downstream guards (route rows):')
    for gate, name in GATES:
        print(f'  {gate}: {dict(results[gate]["remaining"])}')
    print(f'  ALL SIX: {dict(all_result["remaining"])}')

    print('\nMismatch clusters (unique cases; signature = [stage, non-default slots, depth]):')
    for gate, name in GATES + ((None, 'all'),):
        result = all_result if gate is None else results[gate]
        label = 'ALL SIX' if gate is None else gate
        clusters = result['clusters']
        print(f'\n{label}: {sum(clusters.values())} mismatching cases, {len(clusters)} clusters')
        for key, count in clusters.most_common(8):
            print(f'  {count:4d}  {key}')

    print('\nSanitizer (all-bypass, ASan/UBSan):')
    ub = Counter()
    for row in sanitized.values():
        for route, status in statuses(row).items():
            if status.get('sanitizer'):
                ub[route] += 1
    print(f'  rows with sanitizer reports: {sum(ub.values())} {dict(ub)}')
    default = load_rows(DEFAULT_SANITIZE)
    default_rows = sum(1 for row in default.values() for status in statuses(row).values()
                       if status.get('sanitizer'))
    default_by_status = Counter(status['status'] for row in default.values()
                                for status in statuses(row).values()
                                if status.get('sanitizer'))
    print(f'  default-build control rows with sanitizer reports: {default_rows} '
          f'{dict(default_by_status)}')
    print('  all sanitizer reports are UBSan "misaligned address" reference bindings; '
          'no AddressSanitizer or LeakSanitizer reports.')
    print('  the ALL SIX UB count excludes 3 additional all-bypass UB rows whose '
          'baseline route had no admission-guard attribution.')


if __name__ == '__main__':
    main()
