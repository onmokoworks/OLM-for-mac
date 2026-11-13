"""Serial fresh-sequence AEX benchmark; original binaries always stay external."""
from __future__ import annotations

import argparse
import ctypes
import json
import math
import os
from pathlib import Path
import platform
import statistics
import sys
import time

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'oracle'))
import olm_oracle as o
import oracle_resident as resident

BASE = Path(r'D:\Projects\01_Project\04_Tools\olm for mac')
STAGED = Path(r'C:\Users\optim\AppData\Local\Temp\claude\d399b726667e509a\f4e88ce9-5b8e-4d58-b1e2-473311555016\scratchpad\olm-stage-20261113121904')
HEAVY = {
    'ColorKeep': {1: 32},
    'DistanceGradation': {2: 3, 3: 64, 4: 64, 9: 4, 10: 2.25, 11: 3, 12: 12},
    'OLMBlur': {1: 40, 3: 6},
    'OLMColorKey': {2: .15, 5: 4, 14: 8, 15: 3, 18: 8, 19: 3, 22: 8},
    'OLMDirectionalBlur': {1: 35, 5: 80, 10: 40},
    'OLMKiraKira': {2: 3, 10: 100, 16: 100, 22: 100, 28: 100, 34: 12},
    'OLMRadialBlur': {1: 2, 4: 30, 10: 15, 20: 10},
    'OLMSmoother': {3: 64},
    'OLMSmoother2': {5: 50, 6: 20, 7: 3},
    'OLMToonDilate': {1: 8},
    'OLMUVMap': {3: 1},
    'OLMAntiAntiAlias': {1: 32},
}
NEW = {'ColorKeep', 'DistanceGradation', 'OLMColorKey', 'OLMSmoother2', 'OLMUVMap', 'OLMAntiAntiAlias'}
CPU_RECORDS = []


class AccountingJob(o.WindowsJob):
    """Keep oracle ownership/cleanup; collect coarse whole-batch CPU before close."""
    def attach_resume(self, process):
        self.k.SetPriorityClass.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
        if not self.k.SetPriorityClass(int(process._handle), 0x20):
            raise ctypes.WinError(ctypes.get_last_error())
        super().attach_resume(process)

    def close(self):
        buf = ctypes.create_string_buffer(48)
        if self.k.QueryInformationJobObject(self.handle, 1, buf, 48, None):
            CPU_RECORDS.append(sum(int.from_bytes(buf.raw[i:i+8], 'little') for i in (0, 8)) / 1e7)
        super().close()


def stats(values):
    values = list(values)
    if not values or any(not math.isfinite(v) or v < 0 for v in values):
        raise ValueError('expected finite nonnegative samples')
    return {'n': len(values), 'median_ms': statistics.median(values), 'min_ms': min(values)}


def parse_report(report, manifest, digest):
    entries = [{'id': c['id'], 'side': 'reference',
                'manifest': {'route': manifest['route'], 'reference': {'sha256': digest}}}
               for c in manifest['cases']]
    mapped = resident.map_report(report, entries)
    samples = []
    for case in manifest['cases']:
        r = mapped[case['id']]
        if not r.get('passed'):
            raise ValueError('unsuccessful case: ' + str(r.get('outcome')))
        p = r['performance_diagnostics']
        sample = {k: p[k] / 1e6 for k in ('render_selector_ns', 'worker_render_ns', 'broker_frame_wall_ns')}
        if any(not math.isfinite(v) or v < 0 for v in sample.values()):
            raise ValueError('invalid timing')
        samples.append(sample)
    return samples


def assignments(name, preset):
    result = [{'slot': k, 'value': v} for k, v in (HEAVY[name] if preset == 'heavy' else {}).items()]
    if name == 'OLMDirectionalBlur' and preset == 'heavy':
        result[0] = {'slot': 1, 'components': [HEAVY[name][1]]}
    if preset == 'heavy' and name in ('ColorKeep', 'OLMAntiAntiAlias', 'OLMColorKey'):
        count = 8 if name == 'OLMColorKey' else 32
        for i in range(count):
            slot = 26 + i * 8 if name == 'OLMColorKey' else (2 if name == 'ColorKeep' else 7) + i
            result.append({'slot': slot, 'color': [255, (i * 71) % 256, (i * 113) % 256, (i * 173) % 256]})
    return result


def run_side(args, directory, side, plugin, route, input_path, request):
    manifest = {'schema': resident.SCHEMA, 'schema_version': 1, 'plugin': plugin['path'],
                'route': route, 'isolation': 'fresh_sequence', 'frame_deadline_ms': args.frame_cap * 1000,
                'cases': [{'id': str(i), 'input': str(input_path), 'request': str(request),
                           'output': str(directory / f'{side}-{i}.png')} for i in range(6)]}
    path = directory / f'{side}.manifest.json'
    o.write_json(path, manifest)
    before = len(CPU_RECORDS)
    proc = o.run_process([args.harness, '--headless', '--render-request-batch', path],
                         args.batch_cap, env_overrides=o.frame_deadline_environment(args.frame_cap))
    o.write_json(directory / f'{side}.process.json', proc)
    result = {'process': {k: proc[k] for k in ('pid', 'returncode', 'timeout', 'elapsed_seconds')},
              'raw_report': o.identity(directory / f'{side}.process.json'),
              'manifest': o.identity(path), 'cleanup': 'oracle private Job active count verified zero; child waited'}
    if len(CPU_RECORDS) > before:
        result['batch_cpu_seconds'] = CPU_RECORDS[-1]
        result['batch_cpu_over_wall'] = CPU_RECORDS[-1] / proc['elapsed_seconds']
    try:
        if proc['returncode'] or proc['timeout']:
            raise ValueError('batch failure/timeout (see raw report)')
        report = json.loads(proc['stdout'])
        samples = parse_report(report, manifest, plugin['sha256'])
        result.update(samples_ms=samples[1:], warmup_ms=samples[0],
                      statistics={k: stats(s[k] for s in samples[1:]) for k in samples[0]},
                      worker_sha256=report['cases'][0]['worker_sha256'])
        outputs = []
        for c in manifest['cases']:
            png = Path(c['output'])
            suffix = '.rgba16le' if route.endswith('16') else '.rgba32f-le' if route.endswith('32') else '.png'
            outputs.append({'png': o.sha256(png), 'native': o.sha256(png.with_suffix(suffix))})
        result['outputs'] = outputs
        result['status'] = 'ok'
    except (ValueError, KeyError, OSError) as exc:
        result.update(status='incomplete', error=str(exc))
    finally:
        if not getattr(args, 'keep_frames', False):
            result['frames_deleted'] = drop_frames(manifest)
    return result


FRAME_SUFFIXES = ('.png', '.rgba16le', '.rgba32f-le')


def drop_frames(manifest):
    """Delete rendered frames after hashing; only their digests are evidence.

    1080p deep frames are several MB each, and a campaign renders thousands, so
    keeping them filled the disk. Pass --keep-frames to retain them for diagnosis.
    """
    deleted = 0
    for c in manifest['cases']:
        base = Path(c['output'])
        for suffix in FRAME_SUFFIXES:
            frame = base.with_suffix(suffix)
            try:
                frame.unlink()
                deleted += 1
            except FileNotFoundError:
                pass
    return deleted


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--staged', type=Path, default=STAGED)
    p.add_argument('--harness', type=Path, default=o.DEFAULT_HARNESS)
    p.add_argument('--only', nargs='+', choices=list(HEAVY))
    p.add_argument('--sizes', default='1x1,960x540,1920x1080')
    p.add_argument('--keep-frames', action='store_true',
                   help='keep rendered frames (default: delete after hashing to save disk)')
    p.add_argument('--frame-cap', type=int, default=10)
    p.add_argument('--batch-cap', type=int, default=70)
    p.add_argument('--budget', type=int, default=1680)
    p.add_argument('--radial-zoom', action='store_true',
                   help='use active Zoom strengths 80/40, quality 10 instead of Rotation')
    args = p.parse_args()
    if args.radial_zoom:
        HEAVY['OLMRadialBlur'] = {1: 1, 4: 80, 10: 40, 20: 10}
    if not 1 <= args.frame_cap <= 600 or args.batch_cap <= 0 or args.budget <= 0:
        p.error('invalid caps')
    args.out = args.out.resolve(); args.out.mkdir(parents=True, exist_ok=False)
    if os.name == 'nt':
        o.WindowsJob = AccountingJob
    start = time.monotonic()
    evidence = {'schema_version': 1, 'complete': False, 'harness': o.identity(args.harness),
                'worker_file': o.identity(args.harness.parents[3] / 'target/minihost-build/aex_worker.exe'),
                'runner': o.identity(__file__), 'oracle': o.identity(o.__file__),
                'resident_parser': o.identity(resident.__file__), 'platform': platform.platform(),
                'processor': platform.processor(), 'logical_cpus': os.cpu_count(),
                'seed': 20261113, 'jobs': 1, 'priority': 'NORMAL_PRIORITY_CLASS',
                'warmup': 1, 'timed_frames': 5, 'frame_cap_s': args.frame_cap,
                'batch_cap_s': args.batch_cap, 'budget_s': args.budget, 'plugins': {}, 'cells': []}
    sizes = [tuple(map(int, s.split('x'))) for s in args.sizes.split(',')]
    assets = {}
    for size in sizes:
        w, h = size
        for texture in (False, True):
            path = args.out / f'{w}x{h}-{texture}.png'
            Image.fromarray(o.input_pixels(w, h, 20261113 + int(texture))).save(path)
            assets[size, texture] = path
    evidence['inputs'] = [o.identity(path) for path in assets.values()]
    for name in args.only or HEAVY:
        matches = list((BASE / 'upstream_20261112/extracted').glob(f'*/*/Plugins/64/2025/{name}.aex')) if name in NEW else [BASE / 'ghidra_windows_aex' / f'{name}.aex']
        if len(matches) != 1:
            raise ValueError(f'ambiguous original: {name}')
        plugins = {'original': o.identity(matches[0]), 'rust': o.identity(args.staged / f'{name}.aex')}
        params = o.harness_json(args.harness, ['--inspect-experimental', matches[0]], 30)
        o.write_json(args.out / f'{name}-parameters.json', params)
        evidence['plugins'][name] = {**plugins, 'heavy': assignments(name, 'heavy'),
            'edited_parameter_metadata': [q for q in params if q['slot'] in {a['slot'] for a in assignments(name, 'heavy')}]}
        for size in sizes:
            for depth in ([8, 16] if name == 'OLMSmoother' else [8, 16, 32]):
                route = ('classic' if name == 'OLMSmoother' else 'smart') + str(depth)
                for preset in ('default', 'heavy'):
                    row = {'plugin': name, 'size': list(size), 'depth': depth, 'route': route, 'preset': preset}
                    evidence['cells'].append(row)
                    if time.monotonic() - start > args.budget:
                        row['status'] = 'budget_cap'; continue
                    directory = args.out / f'{name}-{size[0]}x{size[1]}-{route}-{preset}'
                    directory.mkdir()
                    edits = assignments(name, preset)
                    if name == 'OLMUVMap':
                        edits.append({'slot': 1, 'layer': str(assets[size, True])})
                    request = o.make_request({'assignments': edits, 'size': size, 'downsample': '1'}, route=route)
                    request_path = directory / 'request.json'; o.write_json(request_path, request)
                    row['request'] = request
                    order = ['original', 'rust'] if len(evidence['cells']) % 2 else ['rust', 'original']
                    row['order'] = order
                    for side in order:
                        row[side] = run_side(args, directory, side, plugins[side], route, assets[size, False], request_path)
                    good = all(row[s]['status'] == 'ok' for s in order)
                    row['status'] = ('exact' if row['original']['outputs'] == row['rust']['outputs'] else 'mismatch') if good else 'incomplete'
                    if good:
                        row['ratio'] = row['rust']['statistics']['render_selector_ns']['median_ms'] / row['original']['statistics']['render_selector_ns']['median_ms']
                    evidence['elapsed_s'] = time.monotonic() - start
                    o.write_json(args.out / 'evidence.json', evidence)
                    print(name, size, depth, preset, row['status'], round(row.get('ratio', 0), 3), flush=True)
    evidence['complete'] = all(r['status'] == 'exact' for r in evidence['cells'])
    evidence['elapsed_s'] = time.monotonic() - start
    o.write_json(args.out / 'evidence.json', evidence)
    return 0 if evidence['complete'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
