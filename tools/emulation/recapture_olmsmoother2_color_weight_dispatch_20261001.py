#!/usr/bin/env python3
"""Distinguish class-derived indices from dispatches actually executed by AEX."""
import argparse
import gc
import json
import tempfile
from pathlib import Path

import probe_olmsmoother2_color_weight_20261001 as campaign
import olmsmoother2_dispatch_observer_20261001 as observer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    matrix, instances = observer.native_setup()
    source = campaign.SOURCE.read_text()
    cases, dependencies = [], [Path(__file__), Path(campaign.__file__), Path(observer.__file__), campaign.HARNESS]
    with tempfile.TemporaryDirectory(prefix='sm2_dispatch_recapture_') as directory:
        binary = campaign.compile_harness(Path(directory) / 'production', source)
        for name in ('dispatch', 'controls'):
            path = campaign.ROOT / f'reports/olmsmoother2_color_weight_{name}_20261001.json'
            dependencies.append(path)
            baseline = json.loads(path.read_text())
            for old in baseline['cases']:
                pixels = campaign.fixture(old['target_index'], old['profile'])
                typed = campaign.retained.typed_input(pixels, old['depth'])
                assert campaign.retained.sha(typed) == old['input_sha256']
                current, class_plane, histogram = campaign.production(binary, old)
                native, plane, ci, wi = matrix.actual(old['depth'], old['version'], campaign.encoded(pixels, old['depth'], matrix),
                                                    matrix.DEPTHS[old['depth']][1], 4, 3, *old['smoothing'])
                audit = instances[-1]
                assert not audit.import_errors and not audit.dispatch_observer_errors
                assert campaign.retained.sha(native) == old['native_raw_sha256']
                assert campaign.retained.sha(plane) == old['native_class_plane_sha256']
                cases.append({'baseline': name, 'target_index': old['target_index'], 'profile': old['profile'],
                              'depth': old['depth'], 'version': old['version'], 'smoothing': old['smoothing'],
                              'input_sha256': old['input_sha256'], 'native_raw_sha256': old['native_raw_sha256'],
                              'production_raw_sha256': campaign.retained.sha(current),
                              'raw_exact': native == current, 'class_exact': plane == class_plane,
                              'actual_native_dispatch_histogram': dict(sorted(audit.executed_dispatch_histogram.items())),
                              'production_dispatch_histogram': histogram,
                              'actual_dispatch_exact': dict(audit.executed_dispatch_histogram) == histogram,
                              'baseline_class_derived_histogram': old['native_histogram'],
                              'executed_imports': sorted(audit.executed_imports),
                              'classifier_instructions': ci, 'worker_instructions': wi})
                instances.clear()
                if len(cases) % 8 == 0:
                    gc.collect()
                if len(cases) % 128 == 0:
                    print('SM2_OBSERVED_DISPATCH', len(cases), sum(c['actual_dispatch_exact'] for c in cases), flush=True)
    dependencies += [Path(campaign.retained.__file__), Path(matrix.__file__), Path(matrix.typed.__file__),
                     Path(matrix.v1.__file__), Path(matrix.v2.__file__), campaign.ROOT / 'tools/emulation/aex_loader.py']
    report = {'schema': 'olmsmoother2.actual-dispatch-recapture/1', 'source_sha256': campaign.retained.sha(source.encode()),
              'case_count': len(cases), 'aex_sha256': matrix.typed.AEX_SHA256,
              'dependencies_sha256': {str(p.relative_to(campaign.ROOT)): campaign.retained.sha(p.read_bytes()) for p in dependencies},
              'observer_rva': '0xc50a', 'observer_register': 'EAX',
              'summary': {name: sum(c[name] for c in cases) for name in ('raw_exact', 'class_exact', 'actual_dispatch_exact')},
              'input_and_native_hashes_preserved': True, 'cases': cases,
              'claims_not_made': ['Baseline native_histogram is class-derived, not executed dispatch evidence',
                                  'Read-only internal switch observation, not exported builder or native Windows/AE proof',
                                  'Version 2 still uses captured transfer LUTs', 'No arbitrary input/settings/state completion']}
    args.report.write_text(json.dumps(report, sort_keys=True, indent=2) + '\n')
    print('RESULT', report['summary'], flush=True)


if __name__ == '__main__':
    main()
