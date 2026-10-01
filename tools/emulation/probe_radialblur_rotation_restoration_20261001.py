#!/usr/bin/env python3
"""Replay the complete public matrix before promoting the Rotation restoration."""
import argparse
import copy
import json
import os
from pathlib import Path
import subprocess

import probe_radialblur_rotation_inverse_20261001 as inverse
import probe_radialblur_pf8_writer_20261001 as writer
public = inverse.public
BEFORE = public.ROOT/'reports/radialblur_pf8_writer_public_20261001.json'
BEFORE_REVISION = '6d0904f8ea86d2deb572aa4ddb4c2aca2c5ba61c'
SOURCE_PATH = 'mac/OLMRadialBlur/OLMRadialBlur.cpp'


def before_source():
    source = subprocess.check_output(['git', 'show', BEFORE_REVISION+':'+SOURCE_PATH], cwd=public.ROOT).decode()
    assert public.sha(source.encode()) == json.loads(BEFORE.read_text())['source_sha256']
    return source


def restored_source():
    source = inverse.candidate_inverse_source(before_source())
    source = source.replace('// Disposable diagnostic: AEX 1ebc0 Gaussian-domain polynomial.',
                            '// AEX FUN_18001ebc0 vector Gaussian-domain polynomial.')
    source = source.replace('// The AEX builds its 30,000-entry table from a float32 exponent,\n\t\t// then rounds the imported expf result once to float.',
                            '// The AEX vector path builds its 30,000-entry table from a\n\t\t// FLOAT32 exponent using the embedded SIMD exp polynomial.')
    return source


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--report', type=Path, required=True); args = ap.parse_args()
    args.output.mkdir(exist_ok=False, parents=True)
    before = json.loads(BEFORE.read_text()); source = before_source()
    live_source = public.SOURCE.read_text()
    assert live_source in (source, restored_source())
    candidate = restored_source(); (args.output/'candidate.cpp').write_text(candidate)
    env = dict(os.environ, ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',
               UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
    binaries = {'o2': public.build(args.output/'o2', candidate),
                'san': public.build(args.output/'san', candidate, sanitize=True)}
    rows = []
    for index, case in enumerate(before['rows']):
        results = {}
        for name, binary in binaries.items():
            for command in ['classic', 'smart']:
                error, raw, metadata = public.mac_render(binary, args.output, case, command, env)
                old = case['results'][command]
                assert error == old['error'] and metadata == old['metadata'], (index, name, command)
                result = {'error': error, 'raw_sha256': public.sha(raw) if not error else None,
                          'raw_exact': not error and public.sha(raw) == case['reference_raw_sha256'],
                          'metadata': metadata, 'before_raw_exact': old['raw_exact'],
                          'before_raw_unchanged': (public.sha(raw) if not error else None) == old['raw_sha256']}
                if name == 'o2': results[command] = result
                else: assert result == results[command], (index, command)
        row = {k: copy.deepcopy(case[k]) for k in ['family', 'geometry', 'depth', 'pattern', 'state', 'parameters',
               'group', 'matrix', 'row_index', 'input_sha256', 'reference_raw_sha256', 'parent_raw_sha256']}
        row['results'] = results; rows.append(row)
        if (index+1) % 128 == 0: print('ROTATION_RESTORATION_PUBLIC', index+1, flush=True)
    assert public.SOURCE.read_text() == live_source
    report = {'schema': 'radialblur.rotation-restoration-public/1', 'source_before_sha256': before['source_sha256'],
              'source_sha256': public.sha(candidate.encode()), 'header_sha256': before['header_sha256'],
              'counterfactual_source_sha256': public.sha(inverse.candidate_inverse_source(source).encode()),
              'production_comment_cleanup_only': True,
              'probe_start_source_sha256': public.sha(live_source.encode()),
              'before_revision': BEFORE_REVISION, 'aex_sha256': before['aex_sha256'],
              'controlled_worker_sha256': before['controlled_worker_sha256'], 'rows': rows,
              'summary': writer.summarize(rows),
              'matrix_summaries': {m: writer.summarize([r for r in rows if r['matrix'] == m]) for m in before['matrix_summaries']},
              'public_replay_count': len(rows)*4, 'builds': ['o2', 'asan-ubsan-strict-halt'],
              'dependencies_sha256': {str(p.relative_to(public.ROOT)): public.sha(p.read_bytes()) for p in
                                      [Path(__file__), Path(inverse.__file__), Path(inverse.fields.__file__), BEFORE,
                                       public.SOURCE.with_suffix('.h'), public.initial.HARNESS]},
              'production_source_changed_during_probe': False,
              'claims_not_made': ['Finite fixtures do not prove all settings, geometry or all inputs.',
                                 'Controlled reference atan2, native Windows ISA and approximate RCPPS remain unproved.',
                                 'Extra radius row ownership and scalar expf branch remain open.',
                                 'No native AE/UI/save/installed/ROI/downsample or all-ten completion.']}
    args.report.write_text(json.dumps(report, sort_keys=True, indent=2)+'\n')
    print('ROTATION_RESTORATION_DONE', report['summary'], flush=True)


if __name__ == '__main__':
    main()
