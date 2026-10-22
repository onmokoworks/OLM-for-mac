#!/usr/bin/env python3
"""Promote the measured RadialBlur Offset restoration onto current production.

The 2026-10-02 candidate was built from BEFORE_REVISION. Production later gained
refusal-attribution instrumentation (T03), and the F08/T05 changes. This runner validates the supplied production
source without replacing any newer work.
Before the candidate is trusted, the rebuilt reference worker is calibrated
against native output hashes recorded by earlier probes.
"""
import os
import argparse
import contextlib
from concurrent.futures import ProcessPoolExecutor
from collections import Counter, deque
import multiprocessing
import shutil
import tempfile
import json
from pathlib import Path

import probe_radialblur_offset_20261002 as offset
public = offset.public
noop = offset.noop
ENV = offset.ENV
MAIN_ROOT = Path('/Users/onmk/Documents/Projects/Personal/OLM as')
CALIBRATION_REPORTS = [
    'radialblur_strength_public_20261002.json',
    'radialblur_rotation_neutral_public_20261001.json',
    'radialblur_gain_public_20261002.json',
]


def resolve_aex():
    if public.initial.AEX.is_file():
        return public.initial.AEX
    path = MAIN_ROOT/'aex/OLMRadialBlur/Plugins/64/2025/OLMRadialBlur.aex'
    assert path.is_file(), path
    public.initial.AEX = path
    return path


def worker_calibration(worker, directory):
    directory.mkdir(parents=True, exist_ok=True)
    rows = []
    for report_name in CALIBRATION_REPORTS:
        previous = json.loads((public.ROOT/'reports'/report_name).read_text())
        assert public.sha(public.initial.AEX.read_bytes()) == previous['aex_sha256'], report_name
        cases = previous['rows']
        selected = [next(row for row in cases if row['family'] == family and row['depth'] == depth)
                    for family in [1, 2] for depth in [8, 16, 32]]
        for index, case in enumerate(selected):
            temp = directory/(report_name[:16]+'_'+str(index))
            temp.mkdir()
            raw, frame, _, close, _ = public.native_render(worker, temp, case)
            row = dict(report=report_name, family=case['family'], depth=case['depth'],
                geometry=case['geometry'], pattern=case['pattern'],
                reference_raw_sha256=case['reference_raw_sha256'], native_raw_sha256=public.sha(raw),
                exact=not frame['render_error'] and close['session_clean'] and
                    public.sha(raw) == case['reference_raw_sha256'])
            assert row['exact'], row
            rows.append(row)
            print('OFFSET_PROMOTE_CALIBRATION', len(rows), row['exact'], flush=True)
    return rows


def generated_calibration(worker, directory):
    directory.mkdir(parents=True, exist_ok=True)
    rows = []
    for index, case in enumerate(offset.calibration_cases()):
        temp = directory/str(index)
        temp.mkdir()
        native, frame, _, close, _ = public.native_render(worker, temp, case)
        assert not frame['render_error'] and frame['output']['guards_intact'] and close['session_clean']
        assert not close['unsupported_suite_calls']
        row = dict(case, reference_raw_sha256=public.sha(native),
            input_sha256=public.sha(public.fixture(case)))
        rows.append(row)
    return dict(schema='radialblur.offset-calibration/1',
        worker_sha256=public.sha(worker.read_bytes()), rows=rows)


def independent_task(task):
    index, case, worker, directory, binaries, before_binary, recorded = task
    resolve_aex()
    # Each process owns its config/native sidecars. Process isolation also keeps
    # the retained NoOp fixture_scope monkeypatch out of other cases.
    with tempfile.TemporaryDirectory(prefix=f'independent_{index}_', dir=directory) as name:
        temp = Path(name)
        native, frame, _, close, _ = public.native_render(worker, temp, case)
        assert not frame['render_error'] and frame['output']['guards_intact'] and close['session_clean']
        assert not close['unsupported_suite_calls']
        if case['group'] == 'offset_admission':
            assert public.sha(native) == recorded['rows'][case['row_index']]['reference_raw_sha256']
        old_error, old_raw, _ = public.mac_render(before_binary, temp, case, 'classic', ENV)
        results = {}
        for build, binary in binaries.items():
            for route in ['classic', 'smart']:
                error, raw, metadata = public.mac_render(binary, temp, case, route, ENV)
                assert not error and raw == native, dict(case=case, build=build, route=route,
                    error=error, expected_sha256=public.sha(native), actual_sha256=public.sha(raw),
                    first_byte=next((i for i, (a, b) in enumerate(zip(native, raw)) if a != b), None))
                result = dict(error=error, raw_sha256=public.sha(raw), raw_exact=True, metadata=metadata)
                if build == 'o2': results[route] = result
                else: assert result == results[route]
        return dict(case, input_sha256=public.sha(public.fixture(case)),
            reference_raw_sha256=public.sha(native), results=results,
            before_error=old_error, before_raw_exact=not old_error and old_raw == native)


def retained_task(task):
    cases, directory, binaries = task
    counts = Counter()
    with tempfile.TemporaryDirectory(prefix='retained_', dir=directory) as name:
        temp = Path(name)
        for case in cases:
            with noop.fixture_scope(case) if case.get('matrix') == 'noop' else contextlib.nullcontext():
                for build, binary in binaries.items():
                    for route in ['classic', 'smart']:
                        error, raw, metadata = public.mac_render(binary, temp, case, route, ENV)
                        expected = case['results'][route]
                        assert error == expected['error'] and public.sha(raw) == expected['raw_sha256'] and metadata == expected['metadata'], dict(
                            case=case, build=build, route=route, error=error,
                            actual_sha256=public.sha(raw), actual_metadata=metadata)
                        counts[(case.get('matrix', 'rotation_size_noise_independent'), build, route)] += 1
    return counts


def bounded_map(pool, function, tasks, jobs):
    tasks = iter(tasks)
    pending = deque(pool.submit(function, task) for task in [next(tasks, None) for _ in range(jobs)] if task is not None)
    while pending:
        yield pending.popleft().result()
        task = next(tasks, None)
        if task is not None:
            pending.append(pool.submit(function, task))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--worker', type=Path, required=True)
    ap.add_argument('--worker-build', type=Path, required=True)
    ap.add_argument('--source', type=Path, default=public.SOURCE)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--report', type=Path, required=True)
    ap.add_argument('--pilot', action='store_true')
    ap.add_argument('--jobs', type=int, default=2)
    ap.add_argument('--retained-limit', type=int, default=0)
    args = ap.parse_args()
    if args.jobs < 1: ap.error('--jobs must be positive')
    args.output = args.output.resolve()
    assert args.output.is_relative_to(public.ROOT/'orchestra/state/T01-radial-offset-promote')
    args.output.mkdir(parents=True, exist_ok=False)
    resolve_aex()
    binding = json.loads(args.worker_build.read_text())
    worker_sha = public.sha(args.worker.read_bytes())
    assert worker_sha == binding['worker_sha256']
    assert binding['parent_source_and_worker_unchanged'] and not binding['original_aex_changed']
    assert binding['dimensions_memory_abi_math_and_copy_callbacks_unchanged']
    assert set(binding['changed']) == {'crates/aex-guest-worker/src/x64.rs'}
    assert binding['timeout_microseconds_after'] > binding['timeout_microseconds_before']

    calibration = worker_calibration(args.worker, args.output/'calibration_replay')
    recorded = generated_calibration(args.worker, args.output/'calibration_cases')

    source = args.source.read_text()
    initial_source = public.sha(public.SOURCE.read_bytes())
    assert source.count('RotationResolvedSpanForRadius') == 6
    assert 'info.outer_offset >= 0 && info.outer_offset <= 500' in source
    core = public.ROOT/'core/dblur_noise.h'; initial_core = public.sha(core.read_bytes())
    (args.output/'candidate.cpp').write_text(source)
    names = ['o2'] if args.pilot else ['o2', 'san', 'default']
    binaries = {name: noop.build(args.output/name, source, name) for name in names}
    before_binary = noop.build(args.output/'before', offset.before_source())
    rows = []; replays = 0
    retained = offset.retained_cases(); assert len(retained) == 9645
    if args.retained_limit: retained = retained[:args.retained_limit]
    retained_counts = Counter()
    # Spawn avoids inheriting temporary fixture overrides. Only two independent
    # case tasks are active with --jobs 2; no shared writable render directory.
    with ProcessPoolExecutor(max_workers=min(args.jobs, int(os.environ.get("OLM_TEST_JOBS", "2"))), mp_context=multiprocessing.get_context('spawn')) as pool:
        tasks = [(index, case, args.worker, args.output, binaries, before_binary, recorded)
                 for index, case in enumerate(offset.independent_cases())]
        with (args.output/'independent.jsonl').open('w') as checkpoint:
            for row in bounded_map(pool, independent_task, tasks, args.jobs):
                rows.append(row); replays += 2 * len(binaries)
                checkpoint.write(json.dumps(row, sort_keys=True)+'\n'); checkpoint.flush()
                if len(rows) % 12 == 0 or len(rows) == 390:
                    print('OFFSET_PROMOTE_INDEPENDENT', len(rows), 'REPLAYS', replays, flush=True)
        assert len(rows) == 390
        if not args.pilot:
            tasks = [(retained[i:i+32], args.output, binaries) for i in range(0, len(retained), 32)]
            for counts in bounded_map(pool, retained_task, tasks, args.jobs):
                retained_counts.update(counts)
                print('OFFSET_PROMOTE_RETAINED', sum(retained_counts.values()), flush=True)
    retained_replays = sum(retained_counts.values())
    assert public.sha(public.SOURCE.read_bytes()) == initial_source and public.sha(core.read_bytes()) == initial_core
    result = dict(schema='radialblur.offset-promote/2', pilot=args.pilot, jobs=args.jobs,
        retained_suites=[dict(matrix=matrix, build=build, route=route, exact=count)
                         for (matrix, build, route), count in sorted(retained_counts.items())],
        source_sha256=public.sha(source.encode()), production_source_sha256=initial_source,
        header_sha256=public.sha(public.SOURCE.with_suffix('.h').read_bytes()),
        core_sha256=initial_core, aex_sha256=public.sha(public.initial.AEX.read_bytes()),
        offset_worker_sha256=worker_sha, offset_worker_build_sha256=public.sha(args.worker_build.read_bytes()),
        offset_reference_build=binding, calibration_replay=calibration,
        calibration_replay_count=len(calibration),
        calibration_replay_exact=sum(row['exact'] for row in calibration),
        calibration_cases_sha256=public.sha(json.dumps(recorded, sort_keys=True).encode()),
        independent_summary=dict(case_count=len(rows), both_commands_exact=len(rows),
            before_rejected=sum(bool(row['before_error']) for row in rows),
            before_different=sum(not row['before_error'] and not row['before_raw_exact'] for row in rows)),
        independent_rows=rows, retained_case_count=len(retained),
        retained_replay_count=retained_replays, candidate_public_replay_count=replays+retained_replays,
        production_source_and_core_changed_during_probe=False,
        dependencies_sha256={str(path.relative_to(public.ROOT)): public.sha(path.read_bytes()) for path in
            [Path(__file__), Path(offset.__file__), Path(noop.__file__), public.SOURCE.with_suffix('.h'), core, public.initial.HARNESS]},
        claims_not_made=['Legal Offset admission and bounded arithmetic witnesses do not close arbitrary inputs/settings, resource limits, Type3, native AE, ROI/downsample or all-ten completion.'])
    args.report.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    for name in [*names, 'before']:
        shutil.rmtree(args.output/name)
    print('OFFSET_PROMOTE_DONE', result['independent_summary'], 'RETAINED', retained_replays, flush=True)


if __name__ == '__main__': main()
