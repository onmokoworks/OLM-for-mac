"""Offline audit of benchmark identities, raw reports and every accepted artifact."""
import argparse
from collections import Counter
import json
from pathlib import Path

from bench import o, parse_report, stats


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('evidence', type=Path)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    data = json.loads(args.evidence.read_text(encoding='utf-8'))
    identities = [data['harness'], data['worker_file']]
    for plugin in data['plugins'].values():
        identities.extend(plugin[s] for s in ('original', 'rust'))
    for identity in identities:
        if o.sha256(identity['path']) != identity['sha256']:
            raise ValueError('executable changed: ' + identity['path'])
    counts = Counter()
    workers = set()
    for row in data['cells']:
        counts[row['status'] + '_cells'] += 1
        for side in ('original', 'rust'):
            result = row.get(side, {})
            if not result:
                continue
            raw = result['raw_report']
            if o.sha256(raw['path']) != raw['sha256']:
                raise ValueError('raw report changed')
            counts['raw_reports_verified'] += 1
            if result['status'] != 'ok':
                continue
            proc = json.loads(Path(raw['path']).read_text(encoding='utf-8'))
            report = json.loads(proc['stdout'])
            identity = result['manifest']
            if o.sha256(identity['path']) != identity['sha256']:
                raise ValueError('manifest changed')
            manifest = json.loads(Path(identity['path']).read_text(encoding='utf-8'))
            samples = parse_report(report, manifest, data['plugins'][row['plugin']][side]['sha256'])
            if samples[1:] != result['samples_ms']:
                raise ValueError('sample mapping changed')
            for field in samples[0]:
                if stats(s[field] for s in samples[1:]) != result['statistics'][field]:
                    raise ValueError('statistics differ')
            for i, case in enumerate(manifest['cases']):
                r = report['cases'][i]
                workers.add(r['worker_sha256'])
                if r['worker_sha256'] != data['worker_file']['sha256']:
                    raise ValueError('loaded worker differs')
                expected_format = {8: 'argb8', 16: 'argb16', 32: 'argb32f'}[row['depth']]
                if r['pixel_format'] != expected_format:
                    raise ValueError('actual dispatch depth differs: ' + r['pixel_format'])
                path = Path(case['output'])
                if result.get('frames_deleted') and not path.exists():
                    # Frames were deleted after hashing (default); the recorded
                    # digests are the evidence and the equality check below uses them.
                    counts['frames_deleted_digest_only'] += 1
                    continue
                if o.sha256(path) != result['outputs'][i]['png']:
                    raise ValueError('PNG changed')
                counts['png_files_verified'] += 1
                if row['depth'] != 8:
                    path = path.with_suffix('.rgba16le' if row['depth'] == 16 else '.rgba32f-le')
                    if path.stat().st_size != row['size'][0] * row['size'][1] * 4 * (row['depth'] // 8):
                        raise ValueError('deep output length differs')
                    if o.sha256(path) != result['outputs'][i]['native']:
                        raise ValueError('native output changed')
                    counts['deep_files_verified'] += 1
        if row['status'] == 'exact':
            if row['original']['outputs'] != row['rust']['outputs']:
                raise ValueError('equality claim differs')
            counts['exact_frame_pairs_including_warmup'] += 6
            counts['exact_timed_frame_pairs'] += 5
    result = {'evidence': o.identity(args.evidence), 'counts': dict(counts),
              'loaded_worker_hashes': sorted(workers), 'executables_unchanged': len(identities),
              'passed': True}
    args.out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
