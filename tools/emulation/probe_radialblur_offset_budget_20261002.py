#!/usr/bin/env python3
"""Measure actual Rotation fade/scatter iterations, then compare admission.

Counters are added only to a disposable source copy. The resulting frame must
match the uninstrumented renderer. Boundary rejections preserve the output and
callback balance through the public harness; no Windows resource limit is claimed.
"""
import argparse
import json
from pathlib import Path
import subprocess

import probe_radialblur_offset_20261002 as offset
public = offset.public


def instrument(source):
    source = 'static unsigned long long g_offset_work[4] = {};\n' + source
    for index, name in enumerate(['effective_outer_fade_span', 'effective_inner_fade_span',
                                  'effective_span', 'effective_inner_span']):
        marker = 'for (A_long offset = 1; offset < '+name+'; ++offset) {'
        assert source.count(marker) == 1, name
        source = source.replace(marker, marker+' ++g_offset_work['+str(index)+'];')
    harness = offset.noop.large_harness()
    marker = '    const auto info=InfoFromParams(params,w,h);'
    assert harness.count(marker) == 1
    harness = harness.replace(marker, marker+'''
    size_t budget_bytes=0;uint64_t budget_work=0;
    const bool budget_ok=CheckedRadialGenericBudget(w,h,depth,info,!strcmp(argv[4],"smart"),&budget_bytes,&budget_work);
    fprintf(stderr,"OFFSET_WORK %llu %llu %llu %llu\\nOFFSET_BUDGET %d %zu %llu\\n",
        g_offset_work[0],g_offset_work[1],g_offset_work[2],g_offset_work[3],
        (int)budget_ok,budget_bytes,(unsigned long long)budget_work);
''')
    return source, harness


def measure(binary, directory, case, route):
    config = directory/'parameters.txt'
    config.write_text(public.initial.config_text(case))
    run = subprocess.run([str(binary), *map(str, case['geometry']), str(case['depth']), route, str(config)],
        input=public.fixture(case), capture_output=True, check=True, env=offset.ENV)
    lines = dict(line.split(' ', 1) for line in run.stderr.decode().splitlines())
    error = int(lines['ERROR'])
    assert not error or not run.stdout
    counts = list(map(int, lines['OFFSET_WORK'].split()))
    admitted, byte_count, estimated_work = map(int, lines['OFFSET_BUDGET'].split())
    return dict(error=error, raw_sha256=public.sha(run.stdout),
        actual_loop_iterations=counts, actual_loop_sum=sum(counts),
        estimated_work=estimated_work, estimated_bytes=byte_count, admitted=bool(admitted),
        callback_counts=list(map(int, lines['COUNTS'].split()))), run.stdout


def boundary_case(width, quality):
    params = public.initial.settings(2, width, width)
    for param in params:
        if param['slot'] in [6, 20]: param['value'] = {6: 500, 20: quality}[param['slot']]
    return dict(family=2, depth=32, geometry=[width, width], pattern='opaque',
        parameters=params, state='offset500_budget_boundary', group='offset_budget', matrix='offset')


def probe(directory, source):
    directory.mkdir(parents=True, exist_ok=False)
    instrumented, body = instrument(source)
    harness = directory/'counter_harness.cpp'; harness.write_text(body)
    unbudgeted = offset.candidate_source(offset.before_source(), budget=False)
    old_instrumented = instrument(unbudgeted)[0]
    results = []
    with offset.noop.harness_scope(harness):
        binaries = {name: public.build(directory/name, instrumented, name == 'san') for name in ['o2', 'san']}
        old_binary = public.build(directory/'previous_estimate', old_instrumented)
    regular = offset.noop.build(directory/'regular', source)
    # Every mode/direction, reciprocal witness and compound Fade/Noise/Size.
    cases = [r for i, r in enumerate(offset.independent_cases()) if
             (i < 324 and i%18 in [0, 7, 17]) or i >= 372]
    for case in cases:
        row = dict(case=case, results={})
        for name, binary in binaries.items():
            for route in ['classic', 'smart']:
                actual, raw = measure(binary, directory, case, route)
                error, baseline, _ = public.mac_render(regular, directory, case, route, offset.ENV)
                assert not error and not actual['error'] and raw == baseline
                assert actual['actual_loop_sum'] <= actual['estimated_work']
                row['results'][name+'_'+route] = actual
        results.append(row)
    # These frames are rendered with the previous estimate in a private copy.
    # The correction may reject them before any loops or output commit.
    boundary = []
    for width, quality in [(128, 5), (256, 5), (512, 1), (512, 5)]:
        case = boundary_case(width, quality)
        row = dict(case=case, results={})
        old, raw = measure(old_binary, directory, case, 'classic')
        assert not old['error'] and old['actual_loop_sum'] > 0
        row['previous_estimate'] = old
        for name, binary in binaries.items():
            for route in ['classic', 'smart']:
                actual, updated = measure(binary, directory, case, route)
                if actual['admitted']:
                    assert not actual['error'] and updated == raw
                    assert actual['actual_loop_sum'] <= actual['estimated_work']
                else:
                    assert actual['error'] and not updated and actual['actual_loop_sum'] == 0
                    assert actual['estimated_work'] > 350_000_000
                row['results'][name+'_'+route] = actual
        boundary.append(row)
        print('OFFSET_BUDGET_BOUNDARY', width, quality, old['actual_loop_sum'],
              row['results']['o2_classic']['estimated_work'], flush=True)
    assert any(r['previous_estimate']['estimated_work'] < r['previous_estimate']['actual_loop_sum'] for r in boundary)
    assert any(not r['results']['o2_classic']['admitted'] for r in boundary)
    return dict(schema='radialblur.offset-budget/1', source_sha256=public.sha(source.encode()),
        instrumented_source_sha256=public.sha(instrumented.encode()),
        measurement_case_count=len(results), measurement_replay_count=4*len(results),
        rows=results, boundary_rows=boundary,
        claims_not_made=['Iteration counts cover fade/scatter loops, not whole render time or CPU instructions.',
                        'The retained 350M/1GiB budget and full-polar estimate remain compatibility limitations.'])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--report', type=Path, required=True)
    args = ap.parse_args()
    result = probe(args.output, args.source.read_text())
    args.report.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print('OFFSET_BUDGET_DONE', result['measurement_case_count'], flush=True)


if __name__ == '__main__': main()
