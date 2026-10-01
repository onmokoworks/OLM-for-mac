#!/usr/bin/env python3
"""Independent Size100/Noise combinations on two new geometries and three depths."""
import argparse
import copy
import json
import os
from pathlib import Path

import probe_radialblur_rotation_size_noise_20261001 as restoration
public = restoration.public


def cases():
    seed = next(row for row in json.loads(restoration.BEFORE.read_text())['rows']
                if row['matrix'] == 'topology' and row['family'] == 2 and row['depth'] == 32 and row['row_index'] == 17)
    rows = []
    for geometry in [[23, 13], [19, 17]]:
        for pattern in ['islands', 'ring', 'diagonal', 'opaque']:
            for noise_type, noise in [(1, 25), (1, 100), (2, 25), (2, 100)]:
                for depth in [8, 16, 32]:
                    case = {key: copy.deepcopy(seed[key]) for key in ['family', 'parameters']}
                    case.update(geometry=geometry, pattern=pattern, depth=depth,
                                state=f'size100_noise{noise}_type{noise_type}', row_index=len(rows))
                    for q in case['parameters']:
                        if q['slot'] == 2: q['value'] = [geometry[0]//2, geometry[1]//2]
                        if q['slot'] == 24: q['value'] = noise
                        if q['slot'] == 25: q['value'] = noise_type
                    case['input_sha256'] = public.sha(public.fixture(case)); rows.append(case)
    assert len(rows) == 96
    return rows


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--parent-worker', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True); ap.add_argument('--report', type=Path, required=True)
    args = ap.parse_args(); args.output.mkdir(exist_ok=False, parents=True)
    source = restoration.before_source(); candidate = restoration.candidate_source(source)
    start_source = public.sha(public.SOURCE.read_bytes()); before = json.loads(restoration.BEFORE.read_text())
    assert public.sha(args.parent_worker.read_bytes()) == before['controlled_worker_sha256']
    assert public.sha(public.initial.AEX.read_bytes()) == before['aex_sha256']
    binaries = {'before': public.build(args.output/'before', source), 'o2': public.build(args.output/'o2', candidate),
                'san': public.build(args.output/'san', candidate, True)}
    env = dict(os.environ, ASAN_OPTIONS='detect_leaks=0:halt_on_error=1', UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
    rows = []
    for case in cases():
        native, frame, _, close, _ = public.native_render(args.parent_worker, args.output, case)
        assert not frame['render_error'] and frame['output']['guards_intact']
        assert close['session_clean'] and not close['unsupported_suite_calls']
        before_error, before_raw, before_meta = public.mac_render(binaries['before'], args.output, case, 'classic', env)
        results = {}
        for name in ['o2', 'san']:
            for command in ['classic', 'smart']:
                error, raw, metadata = public.mac_render(binaries[name], args.output, case, command, env)
                result = {'error': error, 'raw_sha256': public.sha(raw) if not error else None,
                          'raw_exact': not error and raw == native, 'metadata': metadata}
                if name == 'o2': results[command] = result
                else: assert result == results[command]
        row = dict(case, reference_raw_sha256=public.sha(native),
                   before={'error': before_error, 'raw_sha256': public.sha(before_raw) if not before_error else None,
                           'raw_exact': not before_error and before_raw == native, 'metadata': before_meta}, results=results)
        rows.append(row)
        if len(rows) % 24 == 0: print('SIZE_NOISE_INDEPENDENT', len(rows), sum(all(q['raw_exact'] for q in r['results'].values()) for r in rows), flush=True)
    assert public.sha(public.SOURCE.read_bytes()) == start_source
    summary = {'case_count': 96, 'both_commands_exact': sum(all(q['raw_exact'] for q in r['results'].values()) for r in rows),
               'mac_rejected': sum(any(q['error'] for q in r['results'].values()) for r in rows),
               'before_classic_exact': sum(r['before']['raw_exact'] for r in rows),
               'became_exact': sum(not r['before']['raw_exact'] and all(q['raw_exact'] for q in r['results'].values()) for r in rows)}
    report = {'schema': 'radialblur.rotation-size-noise-independent/1', 'source_before_sha256': before['source_sha256'],
              'source_sha256': public.sha(candidate.encode()), 'header_sha256': before['header_sha256'], 'aex_sha256': before['aex_sha256'],
              'controlled_worker_sha256': before['controlled_worker_sha256'], 'before_revision': restoration.BEFORE_REVISION,
              'probe_start_source_sha256': start_source, 'production_source_changed_during_probe': False,
              'summary': summary, 'rows': rows, 'candidate_public_replay_count': 384, 'before_public_replay_count': 96,
              'dependencies_sha256': {str(p.relative_to(public.ROOT)): public.sha(p.read_bytes()) for p in [Path(__file__), Path(restoration.__file__), restoration.BEFORE, public.initial.HARNESS]},
              'claims_not_made': ['Independent finite geometry/settings do not prove all combinations, Size25, arbitrary typed values, Windows CPU/UCRT/AE/UI/save/ROI/downsample or all-ten completion.']}
    args.report.write_text(json.dumps(report, sort_keys=True, indent=2)+'\n'); print('SIZE_NOISE_INDEPENDENT_DONE', summary, flush=True)


if __name__ == '__main__':
    main()
