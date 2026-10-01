#!/usr/bin/env python3
"""Reclassify retained public discrepancies after a witnessed reference correction.

Reacquire both references from the unchanged AEX. Scalar Windows records prove
only their captured inputs; public replay still uses controlled host imports.
"""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile

import probe_radialblur_public_aligned_20261001 as public

ROOT = public.ROOT
SCALAR = ROOT/'tools/emulation/radialblur_atan2_axis_harness_20261001.rs'
NATIVE = ROOT/'refs/conformance/olmradialblur_strength290_native_ucrt_exported_public_boundary_20260815.json'
NATIVE_ROWS_SHA = '52bf76720eef963c77db0a9325f3902bbc9986ad9ce853930ca6f7ad0854d2bd'
CAPTURES = {
    'getters': ROOT/'reports/radialblur_public_getters_angle_fixed_20261001.json',
    'topology': ROOT/'reports/radialblur_public_topology_aligned_20261001.json',
    'typed': ROOT/'reports/radialblur_typed_angle_public_route_20261001.json',
}


def bindings(paths):
    return {str(p.relative_to(ROOT)): public.sha(p.read_bytes()) for p in paths}


def scalar_probe(temp):
    capture = json.loads(NATIVE.read_text())
    native_rows = capture['native_rows']
    assert public.sha(json.dumps(native_rows, sort_keys=True, separators=(',', ':')).encode()) == NATIVE_ROWS_SHA
    cases = [r for r in native_rows if r['function'] == 'atan2f']
    binary = temp/'atan2-scalar'
    subprocess.run(['rustc', '-O', str(SCALAR), '-o', str(binary)], check=True)
    payload = ''.join(f"{r['left_bits'][2:]} {r['right_bits'][2:]}\n" for r in cases)
    run = subprocess.run([str(binary)], input=payload, text=True, capture_output=True, check=True)
    outputs = run.stdout.splitlines()
    assert len(outputs) == len(cases) == 576
    rows = []
    for case, output in zip(cases, outputs):
        host, axis, double = ['0x'+v for v in output.split()]
        is_axis = case['left_bits'] == '0x00000000' and int(case['right_bits'], 16) > 0x80000000
        rows.append(dict(case, host_f32_bits=host, corrected_reference_bits=axis,
                         double_cast_f32_bits=double, corrected_axis=is_axis))
        assert is_axis or axis == host
    axis_rows = [r for r in rows if r['corrected_axis']]
    assert axis_rows and all(r['native_ucrt_result_bits'] == r['corrected_reference_bits'] == '0x40490fdb'
                             for r in axis_rows)
    summary = {key: sum(r[field] == r['native_ucrt_result_bits'] for r in rows)
               for key, field in [('host_f32_exact', 'host_f32_bits'),
                                  ('corrected_reference_exact', 'corrected_reference_bits'),
                                  ('double_cast_exact', 'double_cast_f32_bits')]}
    summary.update(vector_count=len(rows), corrected_axis_count=len(axis_rows),
                   corrected_axis_native_exact=len(axis_rows),
                   nonaxis_unchanged=sum(not r['corrected_axis'] for r in rows))
    return {'schema': 'radialblur.atan2-axis-scalar/1', 'summary': summary,
            'native_rows_sha256': NATIVE_ROWS_SHA, 'rows': rows,
            'native_ucrt_identity': capture['native_return'].get('ucrtbase'),
            'evidence_kind': 'retained Windows scalar records, not a new Windows execution',
            'dependencies_sha256': bindings([Path(__file__), SCALAR, NATIVE]),
            'claims_not_made': ['Captured finite vectors do not prove all-input UCRT equivalence',
                               'Double-cast agreement is a diagnostic, not a general implementation proof']}


def summarize(rows):
    return {'case_count': len(rows),
            'parent_reacquired_hash_exact': sum(r['parent_reacquired_hash_exact'] for r in rows),
            'reference_raw_changed': sum(r['parent_raw_sha256'] != r['corrected_raw_sha256'] for r in rows),
            'both_commands_exact': sum(all(x['corrected_raw_exact'] for x in r['results'].values()) for r in rows),
            'parent_both_commands_exact': sum(all(x['parent_raw_exact'] for x in r['results'].values()) for r in rows),
            'mac_rejected': sum(bool(r['results']['classic']['error']) for r in rows),
            'different': sum(not r['results']['classic']['error'] and not r['results']['classic']['corrected_raw_exact'] for r in rows),
            'became_exact': sum(not r['results']['classic']['parent_raw_exact'] and r['results']['classic']['corrected_raw_exact'] for r in rows),
            'lost_exact': sum(r['results']['classic']['parent_raw_exact'] and not r['results']['classic']['corrected_raw_exact'] for r in rows)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--parent-worker', type=Path, required=True)
    parser.add_argument('--worker', type=Path, required=True)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--scalar-report', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    build = json.loads(args.build.read_text())
    assert public.sha(args.worker.read_bytes()) == build['worker_sha256']
    assert public.sha(args.parent_worker.read_bytes()) == build['parent_worker_sha256']
    assert build['parent_source_and_worker_unchanged']
    assert public.sha(public.initial.AEX.read_bytes()) == public.initial.AEX_SHA
    source = public.SOURCE.read_text()
    rows = []
    with tempfile.TemporaryDirectory(prefix='radial_axis_replay_') as directory:
        temp = Path(directory)
        scalar = scalar_probe(temp)
        args.scalar_report.write_text(json.dumps(scalar, sort_keys=True, indent=2)+'\n')
        print('AXIS_SCALAR', scalar['summary'], flush=True)
        binaries = {'o2': public.build(temp/'o2', source),
                    'sanitizer': public.build(temp/'sanitizer', source, sanitize=True)}
        for matrix, path in CAPTURES.items():
            capture = json.loads(path.read_text())
            cases = capture['rows'] if matrix == 'typed' else capture['cases']
            for index, retained in enumerate(cases):
                spec = {k: retained[k] for k in ('depth', 'family', 'geometry', 'pattern', 'state', 'parameters')}
                input_sha = public.sha(public.fixture(spec))
                assert input_sha == retained['input_sha256']
                parent, parent_frame, _, parent_close, _ = public.native_render(args.parent_worker, temp, spec)
                assert public.sha(parent) == retained['native_raw_sha256'], (matrix, index, 'parent drift')
                corrected, frame, payload, close, _ = public.native_render(args.worker, temp, spec)
                assert parent_close['session_clean'] and close['session_clean']
                assert not parent_close['unsupported_suite_calls'] and not close['unsupported_suite_calls']
                results = {}
                for build_name, binary in binaries.items():
                    for command in ('classic', 'smart'):
                        error, raw, metadata = public.mac_render(binary, temp, spec, command)
                        result = {'error': error, 'raw_sha256': public.sha(raw) if not error else None,
                                  'parent_raw_exact': not error and raw == parent,
                                  'corrected_raw_exact': not error and raw == corrected,
                                  'different_bytes': sum(a != b for a, b in zip(raw, corrected)) if not error else None,
                                  'metadata': metadata}
                        if build_name == 'o2':
                            results[command] = result
                        else:
                            assert result == results[command], (matrix, index, command, 'sanitizer drift')
                rows.append(dict(spec, matrix=matrix, row_index=index, input_sha256=input_sha,
                                 parent_raw_sha256=public.sha(parent), corrected_raw_sha256=public.sha(corrected),
                                 parent_reacquired_hash_exact=True, results=results,
                                 frame_done=frame, parent_frame_done=parent_frame,
                                 session_clean=True, unsupported_suite_calls=[], parameter_payload=payload,
                                 native_api_parameters=public.native_case(spec)['parameters']))
                if len(rows) % 12 == 0:
                    print('AXIS_PUBLIC', len(rows), summarize(rows)['both_commands_exact'], flush=True)
    assert public.sha(args.parent_worker.read_bytes()) == build['parent_worker_sha256']
    deps = [Path(__file__), SCALAR, NATIVE, public.SOURCE, public.SOURCE.parent/'OLMRadialBlur.h',
            public.initial.HARNESS, Path(public.__file__), Path(public.initial.__file__),
            ROOT/'core/dblur_noise.h', ROOT/'core/olm_sha256_rows.h', *CAPTURES.values()]
    report = {'schema': 'radialblur.axis-reference-public/1', 'rows': rows,
              'summary': summarize(rows),
              'matrix_summaries': {m: summarize([r for r in rows if r['matrix'] == m]) for m in CAPTURES},
              'builds': ['o2', 'asan-ubsan'], 'public_replay_count': 4*len(rows),
              'native_reacquisition_count': 2*len(rows),
              'source_sha256': public.sha(source.encode()), 'aex_sha256': public.initial.AEX_SHA,
              'parent_worker_sha256': build['parent_worker_sha256'], 'worker_sha256': build['worker_sha256'],
              'axis_build_sha256': public.sha(args.build.read_bytes()),
              'scalar_report_sha256': public.sha(args.scalar_report.read_bytes()),
              'dependencies_sha256': bindings(deps),
              'production_source_changed': False,
              'claims_not_made': ['References still use controlled imports outside the witnessed axis',
                                 'Reference correction is not a production numerical fix',
                                 'No installed/native AE or general Windows UCRT compatibility',
                                 'No all-ten/all-input/settings/UI/save/ROI/downsample completion']}
    args.report.write_text(json.dumps(report, sort_keys=True, indent=2)+'\n')
    print('AXIS_RESULT', report['matrix_summaries'], flush=True)


if __name__ == '__main__':
    main()
