#!/usr/bin/env python3
"""Summarize completed Round-6 evidence without changing expected results."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT/'orchestra/reports'
CORPUS_REVISION = 'f842ed7d'


def load(suffix):
    return json.loads((REPORTS/('T01-round6-'+suffix+'.json')).read_text())


def routes(comparison):
    result = []
    for route in ['classic', 'smart']:
        before, after = Counter(), Counter()
        for row in comparison['transitions']:
            if row['route'] == route:
                before[row['before']] += row['count']
                after[row['after']] += row['count']
        result.append(dict(route=route, before=dict(before), after=dict(after)))
    return result


def main():
    gates = load('gates')
    assert gates['independent_summary']['both_commands_exact'] == 390
    assert gates['retained_case_count'] == 9645 and gates['retained_replay_count'] == 57870
    suites = {}
    for row in gates['retained_suites']:
        suites.setdefault(row['matrix'], []).append(row)
    retained = []
    for name, rows in suites.items():
        assert len(rows) == 6 and len({r['exact'] for r in rows}) == 1
        retained.append(dict(suite=name, conditions=rows[0]['exact'], public_replays=sum(r['exact'] for r in rows)))
    saved_transitions = Counter()
    changed_paths = []
    for row in load('corpus-after')['replays']:
        path = Path(row['path'])
        relative = path.resolve().relative_to(ROOT)
        saved = json.loads(subprocess.check_output(
            ['git', 'show', CORPUS_REVISION+':'+str(relative)], cwd=ROOT))['result']
        actual = row['result']
        if saved != actual:
            changed_paths.append(str(path))
        for route, before in saved['routes'].items():
            after = actual['routes'][route]
            saved_transitions[(route, before['status'], after['status'])] += 1
            if before['status'] == 'exact':
                assert after['status'] == 'exact' and before['raw_sha256'] == after['raw_sha256']
    comparisons = {label: load(label+'-comparison') for label in ['seed1', 'seed2', 'corpus']}
    result = dict(schema='radialblur.T01-round6/1',
        production_source_sha256=gates['source_sha256'], calibration_exact=gates['calibration_replay_exact'],
        offset=gates['independent_summary'], retained=retained,
        retained_conditions=gates['retained_case_count'], retained_public_replays=gates['retained_replay_count'],
        route_tables={label: routes(value) for label, value in comparisons.items()},
        forbidden={label: value['forbidden'] for label, value in comparisons.items()},
        unlisted={label: value['unlisted'] for label, value in comparisons.items()},
        policy={label: value['policy'] for label, value in comparisons.items()},
        pf8_outer_offset={label: value['pf8_outer_offset'] for label, value in comparisons.items() if label != 'corpus'},
        corpus_saved_to_candidate=[dict(route=r, before=b, after=a, count=n)
                                   for (r,b,a),n in sorted(saved_transitions.items())],
        corpus_before_revision=CORPUS_REVISION,
        corpus_changed_entries=len(changed_paths), tests=load('tests'))
    result['artifacts'] = {str(p.relative_to(ROOT)): dict(bytes=p.stat().st_size,
        sha256=hashlib.sha256(p.read_bytes()).hexdigest())
        for p in sorted(REPORTS.glob('T01-round6-*')) if p.name != 'T01-round6-summary.json' and p.is_file()}
    assert all(v['bytes'] < 2_000_000 for v in result['artifacts'].values())
    output = REPORTS/'T01-round6-summary.json'
    output.write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
    print('SUMMARY', result['retained_conditions'], result['retained_public_replays'],
          'FORBIDDEN', sum(len(v) for v in result['forbidden'].values()),
          'UNLISTED', sum(len(v) for v in result['unlisted'].values()))


if __name__ == '__main__':
    main()
