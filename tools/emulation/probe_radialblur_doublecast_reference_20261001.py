#!/usr/bin/env python3
"""Reclassify retained public rows using a separately calibrated reference.

The scalar Windows census is retained evidence, not a new Windows execution.
Production source and each parent reference remain unchanged.
"""
import argparse
import json
import os
from pathlib import Path
import tempfile

import probe_radialblur_public_aligned_20261001 as public
import probe_radialblur_noise_offset_counterfactual_20261001 as offset

CAPTURE = public.ROOT/'reports/radialblur_noise_offset_counterfactual_20261001.json'
SCALAR = public.ROOT/'reports/radialblur_atan2_axis_scalar_20261001.json'


def summarize(rows):
    return {'case_count': len(rows),
            'parent_reacquired_hash_exact': sum(r['parent_reacquired_hash_exact'] for r in rows),
            'reference_raw_changed': sum(r['parent_raw_sha256'] != r['reference_raw_sha256'] for r in rows),
            'parent_both_commands_exact': sum(all(x['parent_raw_exact'] for x in r['results'].values()) for r in rows),
            'both_commands_exact': sum(all(x['raw_exact'] for x in r['results'].values()) for r in rows),
            'different': sum(not r['results']['classic']['error'] and not r['results']['classic']['raw_exact'] for r in rows),
            'mac_rejected': sum(bool(r['results']['classic']['error']) for r in rows),
            'became_exact': sum(not r['results']['classic']['parent_raw_exact'] and r['results']['classic']['raw_exact'] for r in rows),
            'lost_exact': sum(r['results']['classic']['parent_raw_exact'] and not r['results']['classic']['raw_exact'] for r in rows)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--parent-worker', type=Path, required=True)
    ap.add_argument('--worker', type=Path, required=True)
    ap.add_argument('--build', type=Path, required=True)
    ap.add_argument('--report', type=Path, required=True)
    args = ap.parse_args()
    build = json.loads(args.build.read_text())
    assert public.sha(args.worker.read_bytes()) == build['worker_sha256']
    assert public.sha(args.parent_worker.read_bytes()) == build['parent_worker_sha256']
    capture = json.loads(CAPTURE.read_text())
    assert public.sha(public.SOURCE.read_bytes()) == capture['candidate_source_sha256']
    assert public.sha(offset.HEADER.read_bytes()) == capture['candidate_header_sha256']
    scalar = json.loads(SCALAR.read_text())
    assert scalar['summary']['double_cast_exact'] == scalar['summary']['vector_count'] == 576
    assert public.sha(public.initial.AEX.read_bytes()) == public.initial.AEX_SHA
    env = dict(os.environ, ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',
               UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
    rows = []
    with tempfile.TemporaryDirectory(prefix='radial_doublecast_public_') as directory:
        temp = Path(directory)
        binaries = {'o2': public.build(temp/'o2', public.SOURCE.read_text()),
                    'sanitizer': public.build(temp/'san', public.SOURCE.read_text(), sanitize=True)}
        for index, old in enumerate(capture['rows']):
            spec = {k: old[k] for k in ('family', 'geometry', 'depth', 'pattern', 'state', 'parameters')}
            parent, parent_frame, _, parent_close, _ = public.native_render(args.parent_worker, temp, spec)
            assert public.sha(parent) == old['native_raw_sha256'], ('parent drift', index)
            reference, frame, payload, close, _ = public.native_render(args.worker, temp, spec)
            assert close['session_clean'] and parent_close['session_clean']
            assert not close['unsupported_suite_calls'] and not parent_close['unsupported_suite_calls']
            results = {}
            for build_name, binary in binaries.items():
                for command in ('classic', 'smart'):
                    error, raw, metadata = public.mac_render(binary, temp, spec, command, env)
                    before = old['results']['getter_and_profiles'][command]
                    assert error == before['error'] and metadata == before['metadata']
                    assert (public.sha(raw) if not error else None) == before['raw_sha256']
                    result = {'error': error, 'raw_sha256': public.sha(raw) if not error else None,
                              'parent_raw_exact': not error and raw == parent,
                              'raw_exact': not error and raw == reference, 'metadata': metadata,
                              'different_bytes': sum(a != b for a, b in zip(raw, reference)) if not error else None}
                    if build_name == 'o2': results[command] = result
                    else: assert result == results[command], ('sanitizer drift', index, command)
            rows.append(dict(spec, group=old['group'], matrix=old['matrix'], row_index=old['row_index'],
                             input_sha256=old['input_sha256'], parent_raw_sha256=public.sha(parent),
                             reference_raw_sha256=public.sha(reference), parent_reacquired_hash_exact=True,
                             session_clean=True, unsupported_suite_calls=[], parameter_payload=payload,
                             parent_frame_done=parent_frame, frame_done=frame, results=results))
            if (index+1) % 24 == 0: print('DOUBLECAST_PUBLIC', index+1, summarize(rows)['both_commands_exact'], flush=True)
    deps = [Path(__file__), CAPTURE, SCALAR, public.SOURCE, offset.HEADER,
            Path(public.__file__), Path(public.initial.__file__), public.initial.HARNESS,
            public.ROOT/'core/dblur_noise.h', public.ROOT/'core/olm_sha256_rows.h']
    report = {'schema': 'radialblur.doublecast-reference-public/1', 'rows': rows,
              'summary': summarize(rows),
              'group_summaries': {g: summarize([r for r in rows if r['group'] == g]) for g in ('retained', 'independent')},
              'matrix_summaries': {m: summarize([r for r in rows if r['matrix'] == m])
                                   for m in ('getters', 'topology', 'typed', 'independent')},
              'builds': ['o2', 'asan-ubsan-strict-halt'], 'public_replay_count': 4*len(rows),
              'controlled_reacquisition_count': 2*len(rows),
              'source_sha256': capture['candidate_source_sha256'], 'header_sha256': capture['candidate_header_sha256'],
              'aex_sha256': public.initial.AEX_SHA, 'worker_sha256': build['worker_sha256'],
              'parent_worker_sha256': build['parent_worker_sha256'], 'build_sha256': public.sha(args.build.read_bytes()),
              'reference_kind': build['reference_math'], 'production_source_changed': False,
              'dependencies_sha256': {str(p.relative_to(public.ROOT)): public.sha(p.read_bytes()) for p in deps},
              'claims_not_made': ['Controlled DOUBLE atan2 is not a general Windows UCRT implementation',
                                 'Native scalar coverage is limited to the retained finite arguments',
                                 'New exact rows classify reference differences, not production kernel fixes',
                                 'No installed/native AE or all-input/settings/UI/save/ROI/downsample/all-ten completion']}
    args.report.write_text(json.dumps(report, sort_keys=True, indent=2)+'\n')
    print('DOUBLECAST_RESULT', report['matrix_summaries'], flush=True)


if __name__ == '__main__':
    main()
