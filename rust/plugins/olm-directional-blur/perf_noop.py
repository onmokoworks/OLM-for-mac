"""Targeted no-op controls and cropped demands, using per-process authority."""
from pathlib import Path
import argparse
import sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'rust/tools/oracle'))
import olm_oracle as o


from perf_storage import install, purge
install(o)

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--staged', type=Path, required=True)
    p.add_argument('--originals', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--scaled-only', action='store_true', help='18 Directional nonzero-length identity checks')
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    rows = []
    for name in (['OLMDirectionalBlur'] if args.scaled_only else ['OLMDirectionalBlur', 'OLMRadialBlur']):
        out = args.out / name
        out.mkdir()
        ids = {'reference': o.identity(args.originals / (name + '.aex')),
               'candidate': o.identity(args.staged / (name + '.aex')),
               'harness': o.identity(o.DEFAULT_HARNESS), 'tool': o.identity(__file__)}
        for index in (range(9,15) if args.scaled_only else range(9)):
            edits = []
            if index >= 3:
                if name == 'OLMDirectionalBlur':
                    edits = [{'slot': 1, 'components': [360]}, {'slot': 2, 'value': 10},
                             {'slot': 3, 'value': 100}, {'slot': 7, 'value': 100}, {'slot': 12, 'value': 100}]
                else:
                    edits = [{'slot': 1, 'value': 2}, {'slot': 21, 'value': 10},
                             {'slot': 22, 'value': 100}, {'slot': 20, 'value': 50}]
            if args.scaled_only:
                length = 3 if (index-9)%3 == 2 else 1
                edits = [{'slot':slot,'value':length} for slot in [5,6,10,11]]
            case = {'index': index, 'size': [11, 7], 'input_seed': 15901 + index,
                    'downsample': (['1/2','1/4','1/4'][(index-9)%3] if args.scaled_only else ['1', '1/2', '1/4'][index % 3]), 'assignments': edits}
            for route in ['smart8', 'smart16', 'smart32']:
                row = o.run_case(out, case, route, ids, (), [1, 1, 6, 5] if (index >= 12 if args.scaled_only else index >= 6) else None, 120)
                rows.append({'plugin': name, **row})
                print(name, index, route, row['status'], flush=True)
                o.write_json(args.out / 'summary.json', {'results': rows})
    if not args.scaled_only: rows.extend(fixtures(args))
    o.write_json(args.out / 'summary.json', {'results': rows})
    return 0 if all(row['status'] == 'exact' for row in rows) else 1



def fixtures(args):
    rows = []
    for name in ['OLMDirectionalBlur', 'OLMRadialBlur']:
        parameters = o.harness_json(o.DEFAULT_HARNESS, ['--inspect-experimental', args.originals / (name + '.aex')], 60)
        for depth, fmt, bpp in [(8, 'argb8', 4), (16, 'argb16', 8), (32, 'argb32f', 16)]:
            for cropped in [False, True]:
                folder = args.out / f'fixture-{name}-{depth}-{cropped}'
                folder.mkdir()
                o.Image.fromarray(o.input_pixels(11, 7, 15901)).save(folder / 'input.png')
                fixture = {'schema': 'aexcompat.render_fixture', 'schema_version': 2,
                    'primary_layer': 'input.png', 'parameters': parameters,
                    'pixel_format': fmt, 'render_path': 'smart', 'premultiplication': 'straight',
                    'timing': {'current_time': 0, 'time_step': 1, 'total_time': 1, 'time_scale': 1},
                    'final_artifact': 'raw', 'checkpoints': [{'id': 'output', 'stage': 'smart-output'}],
                    'worlds': {'primary': {'pixel_format': fmt, 'width': 11, 'height': 7,
                        'rowbytes': 13 * bpp, 'row_padding': 2 * bpp, 'padding_byte': 165,
                        'origin': {'x': 2, 'y': -1},
                        'extent': {'left': 1 if cropped else 0, 'top': 1 if cropped else 0,
                                   'right': 9 if cropped else 11, 'bottom': 6 if cropped else 7}},
                        'secondary': []}}
                o.write_json(folder / 'fixture.json', fixture)
                hashes = {}
                for side, plugin in [('reference', args.originals / (name + '.aex')), ('candidate', args.staged / (name + '.aex'))]:
                    result = o.run_process([o.DEFAULT_HARNESS, '--headless', '--render-fixture', plugin,
                        folder / 'fixture.json', folder / side], 120, env_overrides=o.frame_deadline_environment(120))
                    o.write_json(folder / (side + '.process.json'), result)
                    if result['returncode'] == 0 and not result['timeout']:
                        hashes[side] = {str(Path(*f.relative_to(folder / side).parts[2:])): o.sha256(f) for f in (folder / side).rglob('*.bin')}
                exact = len(hashes) == 2 and bool(hashes['reference']) and hashes['reference'] == hashes['candidate']
                row = {'plugin': name, 'fixture': str(folder), 'depth': depth, 'status': 'exact' if exact else 'incomplete_or_mismatched', 'hashes': hashes}
                rows.append(row)
                if exact: purge(folder)
                print(name, depth, 'fixture', cropped, row['status'], flush=True)
    return rows

if __name__ == '__main__':
    raise SystemExit(main())
