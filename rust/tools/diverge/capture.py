"""Replay a saved oracle/minimize case and localize its captured mapped stages.

Uses the public oracle process/render APIs and witness APIs. No original hooks,
recording backend, host installation, or changes to the finished tools.
"""
import argparse
import copy
import os
from pathlib import Path
import shutil
import struct
import sys
import olm_diverge as d
import stage_maps
sys.path.insert(0, str(d.HERE.parent/'oracle'))
import olm_oracle as oracle


def from_capture(path, original, candidate, inject):
    meta = d.load_json(path/'stage.json')
    plugin = meta['plugin']
    angle = struct.unpack('<f', struct.pack('<I', meta.get('angle_bits', 0)))[0]
    injection = inject if plugin == 'distance' or meta['ordinal'] == 0 else -1
    case = stage_maps.build(plugin, original, candidate, w=meta['width'], h=meta['height'],
                            kx=meta.get('kx', 11), ky=meta.get('ky', 11), angle=angle,
                            inject=injection, historical=not meta.get('native', True), source=(path/'input.bin').read_bytes())
    if plugin == 'directional':
        initial = (path/'initial.bin').read_bytes()
        for side in ('reference', 'candidate'):
            spec = case[side]['witness']
            spec['buffers']['middle']['hex'] = initial.hex()
            spec['calls'] = spec['calls'][:1]
        case['candidate']['return_bits'] = {'0': '00000000'}
        case['stages'] = case['stages'][:2]
        case['stages'][1]['id'] = f"rotate[{meta['ordinal']}]"
        case['scope'] = 'same-input replay of captured rotation; upstream/intervening pipeline stages unmapped'
    return case, meta


def capture(case_dir, candidate, out, *, inject=-1, historical=False, harness=None, timeout=120):
    case_dir, candidate, out = Path(case_dir).resolve(), Path(candidate).resolve(), Path(out).resolve()
    original_manifest = d.load_json(case_dir/'case.json')
    manifest = copy.deepcopy(original_manifest)
    original = Path(manifest['reference']['path'])
    if d.witness.sha256(original) != manifest['reference']['sha256']:
        raise ValueError('original identity changed')
    plugin = next((p for p, pin in stage_maps.PINS.items() if pin[1] == d.witness.sha256(original)), None)
    if plugin is None:
        raise ValueError('no grounded stage map for this original')
    if historical and plugin != 'distance':
        raise ValueError('historical SSE override requires DistanceGradation')
    d.export_rva(candidate, 'olm_stage_gaussian_v1' if plugin == 'distance' else 'olm_stage_rotate_v1')
    if harness is not None:
        manifest['harness'] = oracle.identity(Path(harness).resolve())
    elif d.witness.sha256(manifest['harness']['path']) != manifest['harness']['sha256']:
        raise ValueError('historical harness changed; select --harness explicitly to bind a new run')
    out.mkdir(parents=True, exist_ok=False)
    render, captures = out/'render', out/'captures'
    render.mkdir()
    captures.mkdir()
    for relative, expected in manifest['assets'].items():
        source = (case_dir/relative).resolve(strict=True)
        if not source.is_relative_to(case_dir) or d.witness.sha256(source) != expected:
            raise ValueError('invalid/changed oracle input asset '+relative)
        destination = render/relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    # One owned copy of our diagnostic DLL avoids Cargo's hardlinked DLL closure
    # rejection. Original .aex is never copied.
    diagnostic = out/'diagnostic.aex'
    shutil.copyfile(candidate, diagnostic)
    manifest['candidate'] = oracle.identity(diagnostic)
    d.write_json(render/'case.json', manifest)
    overrides = {'OLM_STAGE_DUMP_DIR': str(captures), 'OLM_STAGE_FAULT_INDEX': str(inject) if inject >= 0 else None,
                 'OLM_STAGE_HISTORICAL_SSE': '1' if historical else None}
    saved = {k: os.environ.get(k) for k in overrides}
    try:
        for key, value in overrides.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        row = oracle.evaluate_case(render, manifest, timeout)
    finally:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
    summary = {'schema_version': 1, 'source_case': str(case_dir), 'source_case_sha256': d.witness.sha256(case_dir/'case.json'),
               'candidate_sha256': d.witness.sha256(diagnostic), 'render': row, 'diagnostic_overrides': overrides,
               'coverage': 'same-input replay at mapped boundaries; unmapped stages can contain an earlier divergence',
               'first_divergent_mapped_stage': None, 'captures': [], 'classification': 'unlocalized'}
    try:
        paths = sorted(captures.glob('*/stage.json'), key=lambda p: d.load_json(p)['ordinal'])
        for index, metadata in enumerate(paths):
            path = metadata.parent
            case, meta = from_capture(path, original, diagnostic, inject)
            replay_dir = out/f'stage-{index:03}'
            report = d.run(case, replay_dir, timeout=timeout)
            binding = {'metadata': meta, 'directory': str(path.relative_to(out)), 'replay': replay_dir.name,
                       'report_sha256': d.witness.sha256(replay_dir/'report.json'),
                       'classification': report['classification'], 'first_divergent_stage': report['first_divergent_stage']}
            summary['captures'].append(binding)
            if report['classification'] == 'incomplete':
                raise RuntimeError('stage replay incomplete: '+str(replay_dir))
            # The re-executed Rust stage must reproduce actual render intermediates.
            pairs = [('middle.bin', 1), ('output.bin', 2)] if plugin == 'distance' else [('output.bin', 1)]
            binding['capture_equals_replay'] = {}
            for filename, stage_index in pairs:
                equal = d.witness.sha256(path/filename) == report['stages'][stage_index]['candidate_sha256']
                binding['capture_equals_replay'][filename] = equal
                if not equal:
                    raise RuntimeError('Rust stage replay differs from actual render capture')
            if report['first_divergent_stage'] and summary['first_divergent_mapped_stage'] is None:
                summary['first_divergent_mapped_stage'] = {'capture': index, 'stage': report['first_divergent_stage'],
                    'reproducer': str((replay_dir/'reproducer.json').relative_to(out))}
        if not paths:
            summary['reason'] = 'render never executed a mapped stage'
        elif summary['first_divergent_mapped_stage']:
            summary['classification'] = 'localized_within_mapped_stages'
        elif row['status'] == 'exact':
            summary['classification'] = 'render_and_mapped_stages_exact'
        else:
            summary['reason'] = 'mapped stages match on supplied inputs; inspect unmapped upstream/downstream stages'
    except Exception as error:
        summary['classification'] = 'incomplete'
        summary['error'] = f'{type(error).__name__}: {error}'
    finally:
        d.write_json(out/'capture-report.json', summary)
    return summary


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('case_dir', type=Path, help='oracle case directory, including minimized oracle cases')
    p.add_argument('--candidate', required=True, type=Path, help='stage-dump feature build')
    p.add_argument('--out', required=True, type=Path)
    p.add_argument('--harness', type=Path)
    p.add_argument('--inject', type=int, default=-1)
    p.add_argument('--historical-sse', action='store_true')
    p.add_argument('--timeout', type=float, default=120)
    a = p.parse_args()
    r = capture(a.case_dir, a.candidate, a.out, inject=a.inject, historical=a.historical_sse, harness=a.harness, timeout=a.timeout)
    print(r['classification'], r['first_divergent_mapped_stage'])
    raise SystemExit(0 if r['classification'] == 'render_and_mapped_stages_exact' else 1 if r['classification'] == 'localized_within_mapped_stages' else 2)
