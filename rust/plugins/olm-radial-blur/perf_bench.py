"""Bounded per-process Radial timing, avoiding the original's resident failure.

Each side receives one warmup and five measured fresh processes at each depth.
Use the same 1080p input and Rotation preset as tools/bench; hashes and full
process reports remain external under --out. The oracle owns and drains each
Windows Job. This transport does not expose a selector clock: primary timing is
oracle process wall time (including startup and PNG/deep output), reported
separately from the resident selector benchmark.
"""
import argparse
import json
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'rust/tools/bench'))
import bench

o = bench.o


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before', type=Path, help='optional preserved previous build')
    parser.add_argument('--after', type=Path, required=True)
    parser.add_argument('--original', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out = args.out.resolve()
    args.out.mkdir(parents=True, exist_ok=False)
    o.WindowsJob = bench.AccountingJob
    plugins = {key: o.identity(getattr(args, key).resolve()) for key in ('original', 'before', 'after') if getattr(args, key) is not None}
    image = args.out / 'input.png'
    bench.Image.fromarray(o.input_pixels(1920, 1080, 20261113)).save(image)
    report = {'plugins': plugins, 'harness': o.identity(o.DEFAULT_HARNESS),
              'input': o.identity(image), 'transport': 'per-process',
              'warmup': 1, 'measured': 5, 'clock': 'oracle elapsed_seconds including startup and IO', 'cells': []}
    for depth in (8, 16, 32):
        route = 'smart' + str(depth)
        request = args.out / f'request-{depth}.json'
        o.write_json(request, o.make_request({'assignments': bench.assignments('OLMRadialBlur', 'heavy'),
                                             'size': [1920, 1080], 'downsample': '1'}, route=route))
        cell = {'depth': depth, 'samples': {side: [] for side in plugins}, 'outputs': {side: [] for side in plugins}}
        report['cells'].append(cell)
        for iteration in range(6):
            sides = list(plugins) if iteration % 2 == 0 else list(reversed(plugins))
            for side in sides:
                output = args.out / f'{depth}-{iteration}-{side}.png'
                process = o.run_process([o.DEFAULT_HARNESS, '--headless', o.ROUTES[route][1],
                                         plugins[side]['path'], image, output, request], 120,
                                        env_overrides=o.frame_deadline_environment(120))
                process_path = output.with_suffix('.process.json')
                o.write_json(process_path, process)
                if process['returncode'] or process['timeout']:
                    raise RuntimeError(f'incomplete render: {process_path}')
                native = json.loads(process['stdout'])
                if not native.get('passed'):
                    raise RuntimeError(f'failed host contract: {process_path}')
                timings = [process['elapsed_seconds'] * 1000]
                suffix = {8: '.png', 16: '.rgba16le', 32: '.rgba32f-le'}[depth]
                cell['outputs'][side].append(o.sha256(output.with_suffix(suffix)))
                bench.drop_frames({'cases':[{'output':str(output)}]})
                if iteration:
                    cell['samples'][side].append(timings[0])
                print(depth, iteration, side, round(timings[0], 3), flush=True)
                o.write_json(args.out / 'evidence.json', report)
        cell['exact'] = len(set(sum(cell['outputs'].values(), []))) == 1
        cell['median_ms'] = {side: statistics.median(values) for side, values in cell['samples'].items()}
        if 'before' in plugins:
            cell['before_ratio'] = cell['median_ms']['before'] / cell['median_ms']['original']
        cell['after_ratio'] = cell['median_ms']['after'] / cell['median_ms']['original']
        o.write_json(args.out / 'evidence.json', report)
    image.unlink()
    return 0 if all(c['exact'] for c in report['cells']) else 1


if __name__ == '__main__':
    raise SystemExit(main())
