#!/usr/bin/env python3
"""Original legal Offset admission and Rotation arithmetic restoration.

Private frames/traces stay outside the repository. The existing Blur resource
limits remain unresolved compatibility boundaries, separate from numerical
restoration. The current NoOp capture and core epoch remain immutable.
"""
import argparse
import contextlib
import copy
import json
from pathlib import Path
import subprocess

import probe_radialblur_noop_20261002 as noop
public = noop.public
ENV = noop.ENV
BEFORE = public.ROOT/'reports/radialblur_noop_public_20261002.json'
BEFORE_REVISION = 'c841d478bf7b4ee7d1c29ccffef091d127bd40bb'


def before_source():
    source = subprocess.check_output(['git', 'show', BEFORE_REVISION+':mac/OLMRadialBlur/OLMRadialBlur.cpp'], cwd=public.ROOT).decode()
    assert public.sha(source.encode()) == json.loads(BEFORE.read_text())['source_sha256']
    return source


def candidate_source(source, budget=True):
    old = '''\tconst bool outer_offset_supported =
\t\t(info.outer_offset_mode == 1 && info.outer_offset == 0) ||
\t\t((info.outer_offset_mode == 2 || info.outer_offset_mode == 3) &&
\t\t (info.outer_offset == 2 || info.outer_offset == 4));
\tconst bool inner_offset_supported =
\t\t(info.inner_offset_mode == 1 && info.inner_offset == 0) ||
\t\t(info.blur_type == 2 && (info.inner_offset_mode == 2 || info.inner_offset_mode == 3) &&
\t\t (info.inner_offset == 2 || info.inner_offset == 4));'''
    new = '''\tconst bool outer_offset_supported = info.outer_offset_mode >= 1 && info.outer_offset_mode <= 3 &&
        info.outer_offset >= 0 && info.outer_offset <= 500;
\tconst bool inner_offset_supported = info.inner_offset_mode >= 1 && info.inner_offset_mode <= 3 &&
        info.inner_offset >= 0 && info.inner_offset <= 500;'''
    assert source.count(old) == 1; source = source.replace(old, new)
    helper = '''// Original 24c0 uses DIVSS -> MULSS -> CVTTSS2SI for the radius Offset.
// 1c90 then applies Add/Max/Override before its separate 3000 cap.
static A_long RotationResolvedSpanForRadius(A_long strength, A_long offset,
    A_long mode, A_long radius_count, A_long radius_index)
{
    const A_long product = (radius_count / 2) * offset;
    const float reciprocal = RadialF32Div(1.0f, static_cast<float>(radius_index + 1));
    const A_long dynamic = RadialCVTTSS2SI(RadialF32Mul(static_cast<float>(product), reciprocal));
    if (mode == 1) return strength + dynamic;
    if (mode == 2) return std::max(strength, dynamic);
    if (mode == 3) return dynamic;
    return strength;
}

'''
    marker = 'template <typename PixelT>\nstruct RadialZoomPixelTraits;'
    assert source.count(marker) == 1; source = source.replace(marker, helper+marker)
    for side in ['outer', 'inner']:
        old = f'''? (info.{side}_offset_mode == 3 ? DynamicOffsetForRadius(radius_count, native_quality_control(info.{side}_offset), ri)
\t\t\t\t   : (info.{side}_offset_mode == 2 ? std::max(native_quality_control(info.{side}_strength), DynamicOffsetForRadius(radius_count, native_quality_control(info.{side}_offset), ri)) : native_quality_control(info.{side}_strength)))'''
        new = f'? RotationResolvedSpanForRadius(native_quality_control(info.{side}_strength), native_quality_control(info.{side}_offset), info.{side}_offset_mode, radius_count, ri)'
        assert source.count(old) == 1; source = source.replace(old, new)
    if budget:
        marker = 'static bool CheckedRadialGenericBudget('
        declaration = '''static A_long RotationResolvedSpanForRadius(A_long strength, A_long offset,
    A_long mode, A_long radius_count, A_long radius_index);

'''
        assert source.count(marker) == 1; source = source.replace(marker, declaration+marker)
        old = 'const uint64_t work = polar * (strength + 8);'
        new = '''uint64_t work = polar * (strength + 8);
    if (bytes <= kMaxBytes && info.blur_type == 2 && (info.outer_offset != 0 || info.inner_offset != 0)) {
        // Bound the added radius-dependent scatter with the same resolved spans
        // as the render path. Retain the previous estimate as a lower bound.
        // The full-polar occupancy estimate is conservative; its rejection is
        // still a compatibility limitation, not proof of a Windows limit.
        const auto scaled_control = [&](A_long value) {
            return static_cast<A_long>(static_cast<double>(value) * budget_quality_scale);
        };
        const A_long outer = scaled_control(info.outer_strength);
        const A_long inner = scaled_control(info.inner_strength);
        const A_long outer_offset = scaled_control(info.outer_offset);
        const A_long inner_offset = scaled_control(info.inner_offset);
        const uint64_t fade = static_cast<uint64_t>(scaled_control(info.outer_edge_fade)) +
            static_cast<uint64_t>(scaled_control(info.inner_edge_fade));
        if (radius > static_cast<uint64_t>(std::numeric_limits<A_long>::max())) return false;
        uint64_t offset_work = 0;
        for (uint64_t ri = 0; ri < radius; ++ri) {
            const A_long outer_span = RotationResolvedSpanForRadius(outer, outer_offset,
                info.outer_offset_mode, static_cast<A_long>(radius), static_cast<A_long>(ri));
            const A_long inner_span = RotationResolvedSpanForRadius(inner, inner_offset,
                info.inner_offset_mode, static_cast<A_long>(radius), static_cast<A_long>(ri));
            const uint64_t spans = static_cast<uint64_t>(std::min<A_long>(outer_span, 3000)) +
                static_cast<uint64_t>(std::min<A_long>(inner_span, 3000));
            if (spans > UINT64_MAX - fade - 8 || angular > UINT64_MAX / (spans + fade + 8)) return false;
            const uint64_t row_work = angular * (spans + fade + 8);
            if (offset_work > UINT64_MAX - row_work) return false;
            offset_work += row_work;
        }
        work = std::max(work, offset_work);
    }'''
        assert source.count(old) == 1; source = source.replace(old, new)
    return source


def legal_matrix_cases():
    cases = []
    values = [0, 1, 2, 3, 7, 31, 250, 499, 500]
    for side in ['outer', 'inner']:
        for mode in [1, 2, 3]:
            for index, value in enumerate(values):
                for family in [1, 2]:
                    for depth in [8, 16, 32]:
                        geometry = [9, 7] if index % 2 == 0 else [17, 11]
                        pattern = ['diagonal', 'ring', 'islands'][index % 3]
                        params = public.initial.settings(family, *geometry)
                        changes = ({5: mode, 6: value} if side == 'outer' else {4: 0, 10: 7, 11: mode, 12: value})
                        changes[20] = ([1, 3.4, 5][index % 3] if value >= 250 else [1, 3.4, 5, 10, 50][index % 5])
                        if index % 2:
                            changes.update({7: 37, 13: 31, 21: 2.25, 22: 37.5, 24: 33.3,
                                            25: 2, 27: 53, 29: 3.4, 17: 2.5, 18: 17})
                        for param in params:
                            if param['slot'] in changes: param['value'] = changes[param['slot']]
                        cases.append(dict(family=family, depth=depth, geometry=geometry, pattern=pattern,
                            state=side+'_mode'+str(mode)+'_offset'+str(value), parameters=params,
                            group='legal_offset', matrix='offset', row_index=len(cases)))
    assert len(cases) == 324
    return cases


def calibration_cases():
    cases = []
    states = [('outer_add3', {6: 3}), ('outer_max1', {5: 2, 6: 1}),
        ('outer_replace3', {5: 3, 6: 3}), ('outer_max7', {5: 2, 6: 7}),
        ('inner_add3', {10: 3, 12: 3}), ('inner_max3', {10: 3, 11: 2, 12: 3}),
        ('inner_replace7', {10: 3, 11: 3, 12: 7}),
        ('compound', {5: 2, 6: 5, 7: 37, 10: 3, 11: 3, 12: 3, 13: 31,
                      20: 10, 21: 2.25, 22: 37.5, 24: 25, 25: 2, 27: 53, 29: 3.4})]
    for state, changes in states:
        for family in [1, 2]:
            for depth in [8, 16, 32]:
                params = public.initial.settings(family, 9, 7)
                for param in params:
                    if param['slot'] in changes: param['value'] = changes[param['slot']]
                cases.append(dict(family=family, depth=depth, geometry=[9, 7], pattern='diagonal',
                    state=state, parameters=params, group='offset_admission', matrix='offset', row_index=len(cases)))
    return cases


def independent_cases():
    cases = legal_matrix_cases() + calibration_cases()
    for width in [125, 123]:
        for mode in [1, 2, 3]:
            for depth in [8, 16, 32]:
                params = public.initial.settings(2, width, 1)
                for param in params:
                    if param['slot'] in [5, 6, 20]: param['value'] = {5: mode, 6: 205, 20: 1}[param['slot']]
                cases.append(dict(family=2, depth=depth, geometry=[width, 1], pattern='opaque',
                    state='reciprocal_radius_boundary', parameters=params,
                    group='offset_reciprocal', matrix='offset', row_index=len(cases)))
    assert len(cases) == 390
    return cases


def retained_cases():
    return noop.retained_cases() + json.loads(BEFORE.read_text())['independent_rows']


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--worker', type=Path, required=True)
    ap.add_argument('--worker-build', type=Path, required=True)
    ap.add_argument('--calibration-report', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--report', type=Path, required=True)
    ap.add_argument('--pilot', action='store_true')
    args = ap.parse_args(); args.output.mkdir(parents=True, exist_ok=False)
    binding = json.loads(args.worker_build.read_text())
    assert public.sha(args.worker.read_bytes()) == binding['worker_sha256']
    assert binding['parent_source_and_worker_unchanged'] and not binding['original_aex_changed']
    assert binding['dimensions_memory_abi_math_and_copy_callbacks_unchanged']
    assert set(binding['changed']) == {'crates/aex-guest-worker/src/x64.rs'}
    calibration = json.loads(args.calibration_report.read_text())
    calibration_rows = calibration['rows']
    generated = calibration_cases()
    assert generated == [{k: row[k] for k in generated[0]} for row in calibration_rows]
    previous = json.loads(BEFORE.read_text())
    assert calibration['worker_sha256'] == previous['controlled_worker_sha256']
    assert binding['parent_worker_sha256'] == previous['window_worker_sha256']
    parent_build = public.ROOT/'reports/radialblur_readonly_windows_reference_build_20261001.json'
    assert public.sha(parent_build.read_bytes()) == binding['parent_build_sha256']
    assert json.loads(parent_build.read_text())['parent_worker_sha256'] == calibration['worker_sha256']
    source = before_source(); candidate = candidate_source(source)
    initial_source = public.sha(public.SOURCE.read_bytes())
    assert initial_source == previous['source_sha256']
    assert public.sha(public.initial.AEX.read_bytes()) == previous['aex_sha256']
    core = public.ROOT/'core/dblur_noise.h'; initial_core = public.sha(core.read_bytes())
    (args.output/'candidate.cpp').write_text(candidate)
    names = ['o2', 'san', 'default']
    binaries = {name: noop.build(args.output/name, candidate, name) for name in names}
    before_binary = noop.build(args.output/'before', source)
    rows = []; replays = 0; calibrated = 0
    for case in independent_cases():
        native, frame, _, close, _ = public.native_render(args.worker, args.output, case)
        assert not frame['render_error'] and frame['output']['guards_intact'] and close['session_clean']
        assert not close['unsupported_suite_calls']
        if case['group'] == 'offset_admission':
            assert public.sha(native) == calibration_rows[case['row_index']]['reference_raw_sha256']
            calibrated += 1
        old_error, old_raw, _ = public.mac_render(before_binary, args.output, case, 'classic', ENV)
        results = {}
        for name, binary in binaries.items():
            for route in ['classic', 'smart']:
                error, raw, metadata = public.mac_render(binary, args.output, case, route, ENV)
                assert not error and raw == native, (case, name, route, error)
                result = dict(error=error, raw_sha256=public.sha(raw), raw_exact=True, metadata=metadata)
                if name == 'o2': results[route] = result
                else: assert result == results[route]
                replays += 1
        rows.append(dict(case, input_sha256=public.sha(public.fixture(case)),
            reference_raw_sha256=public.sha(native), results=results,
            before_error=old_error, before_raw_exact=not old_error and old_raw == native))
        if len(rows)%12 == 0: print('OFFSET_INDEPENDENT', len(rows), 'REPLAYS', replays, flush=True)
    assert calibrated == 48
    retained = retained_cases(); assert len(retained) == 9645
    if not args.pilot:
        for name, binary in binaries.items():
            for case in retained:
                with noop.fixture_scope(case) if case['matrix'] == 'noop' else contextlib.nullcontext():
                    for route in ['classic', 'smart']:
                        error, raw, metadata = public.mac_render(binary, args.output, case, route, ENV)
                        expected = case['results'][route]
                        assert error == expected['error'] and public.sha(raw) == expected['raw_sha256'] and metadata == expected['metadata'], (case, name, route)
                        replays += 1
                if replays%1000 == 0: print('OFFSET_RETAINED', name, replays, flush=True)
    assert public.sha(public.SOURCE.read_bytes()) == initial_source and public.sha(core.read_bytes()) == initial_core
    result = dict(schema='radialblur.offset-public/1', pilot=args.pilot,
        source_before_sha256=initial_source, source_sha256=public.sha(candidate.encode()),
        header_sha256=previous['header_sha256'], core_sha256=initial_core, aex_sha256=previous['aex_sha256'],
        controlled_worker_sha256=previous['controlled_worker_sha256'], window_worker_sha256=previous['window_worker_sha256'],
        offset_worker_sha256=binding['worker_sha256'], offset_worker_build_sha256=public.sha(args.worker_build.read_bytes()),
        offset_reference_build=binding, reference_calibration_case_count=calibrated,
        calibration_parent_worker_sha256=calibration['worker_sha256'],
        summary=previous['summary'], rows=copy.deepcopy(previous['rows']), independent_rows=rows,
        independent_summary=dict(case_count=len(rows), both_commands_exact=len(rows),
            before_rejected=sum(bool(r['before_error']) for r in rows),
            before_different=sum(not r['before_error'] and not r['before_raw_exact'] for r in rows)),
        retained_case_count=len(retained), candidate_public_replay_count=replays,
        production_source_and_core_changed_during_probe=False,
        dependencies_sha256={str(path.relative_to(public.ROOT)): public.sha(path.read_bytes()) for path in
            [Path(__file__), Path(noop.__file__), BEFORE, public.SOURCE.with_suffix('.h'), core, public.initial.HARNESS]},
        claims_not_made=previous['claims_not_made']+['Legal Offset admission and bounded arithmetic witnesses do not close arbitrary inputs/settings, resource limits, Type3, native AE, ROI/downsample or all-ten completion.'])
    args.report.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print('OFFSET_PUBLIC_DONE', result['independent_summary'], 'REPLAYS', replays, flush=True)


if __name__ == '__main__': main()
