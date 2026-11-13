"""Fixed three-repeat, per-process triage for completed performance campaigns.

Resident mismatches use their saved per-process authority as the baseline.
Exclusion requires changing original output, constant candidate output, all
successful renders and an exact pair. Directional uses its existing stricter
three original-vs-original pairs plus exact zero-offset control rule.
Other failures stay unresolved.
"""
import argparse
import importlib.util
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "olm-directional-blur"))
from perf_storage import purge


def replay(source, target, module, directional, extra_repeats):
    row = module.one(source, target, None, 3)
    row['qualified_exclusion'] = (row['reference_unique'] > 1 and row['candidate_unique'] == 1
        and row['all_replays_succeeded'] and row['has_exact_replay'])
    manifest = json.loads((source / 'case.json').read_text(encoding='utf-8'))
    if Path(manifest['reference']['path']).stem == 'OLMDirectionalBlur':
        control = directional.diagnose(source, target / 'directional-controls')
        row['directional_controls'] = control
        row['qualified_exclusion'] = (row['reference_unique'] > 1 and row['candidate_unique'] == 1
            and row['all_replays_succeeded'] and control['reference_nondeterminism_proven']
            and control['zero_offset_control']['status'] == 'exact'
            and all(r['processes'][side]['ok'] for r in control['repeats'] for side in ['reference', 'candidate']))
    if (not row['qualified_exclusion'] and extra_repeats
            and Path(manifest['reference']['path']).stem == 'OLMRadialBlur'):
        extra = target / 'additional-fixed-replays'
        extra.mkdir()
        additional = module.one(source, extra, None, extra_repeats)
        row['additional_fixed_replays'] = additional
        row['qualified_exclusion'] = (
            row['all_replays_succeeded'] and additional['all_replays_succeeded']
            and len(set(row['reference_output_hashes'] + additional['reference_output_hashes'])) > 1
            and len(set(row['candidate_output_hashes'] + additional['candidate_output_hashes'])) == 1
            and (row['has_exact_replay'] or additional['has_exact_replay']))
    purge(target)
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('campaigns', type=Path, nargs='+')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--jobs', type=int, choices=[1, 2], default=2)
    parser.add_argument('--extra-repeats', type=int, choices=[0,10], default=0,
                        help='predeclared fixed ten-pair follow-up for unresolved Radial cases')
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location('repeatability', Path(__file__).with_name('triage.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    control_path = Path(__file__).parent.parent / 'olm-directional-blur/classify_mismatches.py'
    control_spec = importlib.util.spec_from_file_location('directional_controls', control_path)
    directional = importlib.util.module_from_spec(control_spec)
    control_spec.loader.exec_module(directional)
    args.out.mkdir(parents=True, exist_ok=False)
    tasks, failures = [], []
    for campaign in args.campaigns:
        data = json.loads((campaign / 'summary.json').read_text(encoding='utf-8'))
        if not data.get('complete'):
            raise RuntimeError('incomplete campaign: ' + str(campaign))
        for row in data['results']:
            authority = row.get('per_process_authority', row)
            source = campaign / row['directory']
            if 'per_process_authority' in row:
                source /= 'per-process-authority'
            if authority['status'] == 'mismatched':
                target = args.out / (campaign.name + '-' + row['directory'])
                target.mkdir()
                tasks.append((source, target))
            elif authority['status'] != 'exact':
                failures.append({'source': str(source), 'status': authority['status']})
    print('mismatches to replay:', len(tasks), flush=True)
    report = {'results': [], 'unreplayed_failures': failures, 'complete': False,
              'jobs': args.jobs, 'fixed_repeats': 3, 'additional_fixed_repeats': args.extra_repeats, 'directional_original_pairs': 3}
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = [pool.submit(replay, source, target, module, directional, args.extra_repeats) for source, target in tasks]
        for future in as_completed(futures):
            row = future.result()
            report['results'].append(row)
            print(row['source'], row['classification'], 'qualified', row['qualified_exclusion'], flush=True)
            module.oracle.write_json(args.out / 'summary.json', report)
    report['complete'] = True
    module.oracle.write_json(args.out / 'summary.json', report)
    return 0 if not failures and all(r['qualified_exclusion'] for r in report['results']) else 1


if __name__ == '__main__':
    raise SystemExit(main())
