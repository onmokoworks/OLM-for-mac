"""Derive tables and fixed-cost sensitivity estimates from saved observations."""
import argparse
import json
from pathlib import Path

from bench import o, stats

METRIC = 'render_selector_ns'


def adjusted(values, baseline):
    """Subtract a fixed control median; negatives mean unresolved, never clamp."""
    differences = [v - baseline for v in values]
    return stats(differences) if all(v >= 0 for v in differences) else None


def augment(data):
    controls = {(r['plugin'], r['depth'], r['preset']): r for r in data['cells'] if r['size'] == [1, 1]}
    for row in data['cells']:
        control = controls.get((row['plugin'], row['depth'], row['preset']))
        if row['size'] == [1, 1] or not control:
            continue
        for side in ('original', 'rust'):
            if row.get(side, {}).get('status') != 'ok' or control.get(side, {}).get('status') != 'ok':
                continue
            base = control[side]['statistics'][METRIC]['median_ms']
            row[side]['control_median_ms'] = base
            row[side]['adjusted'] = adjusted([s[METRIC] for s in row[side]['samples_ms']], base)
        a, b = (row.get(s, {}).get('adjusted') for s in ('original', 'rust'))
        if a and b and a['median_ms'] > 0:
            row['adjusted_ratio'] = b['median_ms'] / a['median_ms']
    return data


def annotate_failures(rows):
    for row in rows:
        for side in ('original', 'rust'):
            result = row.get(side, {})
            if result.get('status') != 'incomplete':
                continue
            raw = result['raw_report']
            path = Path(raw['path'])
            if o.sha256(path) != raw['sha256']:
                raise ValueError('raw failure report changed')
            process = json.loads(path.read_text(encoding='utf-8'))
            result['cap_hit'] = process['timeout'] or 'frame_deadline' in process['stdout']
            try:
                report = json.loads(process['stdout'])
                result['reported_errors'] = ([report['error']] if 'error' in report else []) + [
                    r['error'] for r in report.get('cases', []) if r.get('error')]
            except ValueError:
                result['reported_errors'] = [process['stderr'][:1000]]


def table(data, size):
    lines = ['| Plug-in | bpc | Preset | Original ms | Rust ms | Rust/original | Adjusted O / R ms | Adjusted ratio | Sanity |',
             '|---|---:|---|---:|---:|---:|---:|---:|---|']
    for row in data['cells']:
        if row['size'] != list(size):
            continue
        def raw(side):
            st = row.get(side, {}).get('statistics', {}).get(METRIC)
            return f"{st['median_ms']:.2f} ({st['min_ms']:.2f})" if st else '—'
        a, b = (row.get(s, {}).get('adjusted') for s in ('original', 'rust'))
        adj = f"{a['median_ms']:.2f} / {b['median_ms']:.2f}" if a and b else '—'
        ratio = f"{row['ratio']:.3f}" if 'ratio' in row else '—'
        ar = f"{row['adjusted_ratio']:.3f}" if 'adjusted_ratio' in row else '—'
        lines.append(f"| {row['plugin']} | {row['depth']} | {row['preset']} | {raw('original')} | {raw('rust')} | {ratio} | {adj} | {ar} | {row['status']} |")
    return '\n'.join(lines)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('evidence', type=Path)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--replacement', type=Path, action='append', default=[],
                   help='replace entire named plugin campaigns; retain superseded observations')
    args = p.parse_args()
    data = json.loads(args.evidence.read_text(encoding='utf-8'))
    data['campaigns'] = [o.identity(args.evidence)]
    for row in data['cells']:
        row['limits'] = {k: data[k] for k in ('frame_cap_s', 'batch_cap_s')}
    for path in args.replacement:
        replacement = json.loads(path.read_text(encoding='utf-8'))
        for row in replacement['cells']:
            row['limits'] = {k: replacement[k] for k in ('frame_cap_s', 'batch_cap_s')}
        if data['harness'] != replacement['harness'] or data['worker_file'] != replacement['worker_file']:
            raise ValueError('replacement executable identities differ')
        names = set(replacement['plugins'])
        old = [r for r in data['cells'] if r['plugin'] in names]
        old_keys = {(r['plugin'], tuple(r['size']), r['depth'], r['preset']) for r in old}
        new_keys = {(r['plugin'], tuple(r['size']), r['depth'], r['preset']) for r in replacement['cells']}
        if old_keys != new_keys:
            raise ValueError('replacement must cover the entire plugin matrix')
        data.setdefault('superseded', []).append({'cells': old, 'replacement': o.identity(path),
                                                 'runner': replacement['runner']})
        mapping = {(r['plugin'], tuple(r['size']), r['depth'], r['preset']): r for r in replacement['cells']}
        data['cells'] = [mapping.get((r['plugin'], tuple(r['size']), r['depth'], r['preset']), r) for r in data['cells']]
        data['plugins'].update(replacement['plugins'])
        data['elapsed_s'] += replacement['elapsed_s']
        data['campaigns'].append(o.identity(path))
    data['complete'] = all(r['status'] == 'exact' for r in data['cells'])
    annotate_failures(data['cells'])
    for superseded in data.get('superseded', []):
        annotate_failures(superseded['cells'])
    data = augment(data)
    args.out.write_text(json.dumps(data, separators=(',', ':'), ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
    print(table(data, (1920, 1080)))
    print('\n540p sanity check\n')
    print(table(data, (960, 540)))


if __name__ == '__main__':
    main()
