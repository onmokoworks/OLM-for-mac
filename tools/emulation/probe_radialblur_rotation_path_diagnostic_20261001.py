#!/usr/bin/env python3
"""Test, without changing production, whether baseline two-stage routing is enough."""
import argparse
import json
from pathlib import Path
import tempfile

import probe_radialblur_public_aligned_20261001 as public


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--report', type=Path, required=True)
    args = ap.parse_args()
    source = public.SOURCE.read_text()
    old = '''const bool use_generic_two_stage = use_generic_baseline &&
		(info.inner_strength != 0 || info.outer_edge_fade != 0 || info.inner_edge_fade != 0 ||
		 info.outer_offset_mode != 1 || info.inner_offset_mode != 1 ||
		 info.noise_variation != 0.0 || info.size_variation != 0.0);'''
    assert source.count(old) == 1
    variant = source.replace(old, 'const bool use_generic_two_stage = use_generic_baseline;')
    typed = public.ROOT/'reports/radialblur_typed_angle_public_route_20261001.json'
    topology = public.ROOT/'reports/radialblur_public_topology_aligned_20261001.json'
    cases = json.loads(typed.read_text())['rows'] + json.loads(topology.read_text())['cases']
    rows = []
    with tempfile.TemporaryDirectory(prefix='radial_rotation_path_diagnostic_') as directory:
        temp = Path(directory)
        binary = public.build(temp/'o2', variant)
        for index, case in enumerate(cases):
            if case['family'] != 2: continue
            error, raw, _ = public.mac_render(binary, temp, case, 'classic')
            rows.append({'combined_row_index': index, 'input_sha256': case['input_sha256'],
                         'native_raw_sha256': case['native_raw_sha256'], 'error': error,
                         'raw_sha256': public.sha(raw) if not error else None,
                         'raw_exact': not error and public.sha(raw) == case['native_raw_sha256']})
    summary = {'cases': len(rows), 'exact': sum(r['raw_exact'] for r in rows),
               'different': sum(not r['error'] and not r['raw_exact'] for r in rows),
               'mac_rejected': sum(bool(r['error']) for r in rows)}
    assert summary == {'cases': 140, 'exact': 12, 'different': 84, 'mac_rejected': 44}
    dependencies = [Path(__file__), public.SOURCE, public.initial.HARNESS,
                    Path(public.__file__), Path(public.initial.__file__), typed, topology]
    report = {'schema': 'radialblur.rotation-path-diagnostic/1', 'summary': summary, 'rows': rows,
              'source_sha256': public.sha(source.encode()), 'disposable_variant_sha256': public.sha(variant.encode()),
              'production_changed_by_experiment': False,
              'conclusion': 'Routing all generic baselines to two-stage is insufficient; compare intermediate fields/samplers before changing production',
              'dependencies_sha256': {str(p.relative_to(public.ROOT)): public.sha(p.read_bytes()) for p in dependencies},
              'claims_not_made': ['No accepted pixel mismatch or full compatibility proof',
                                 'No native Windows UCRT/AE or production variant admission']}
    args.report.write_text(json.dumps(report, sort_keys=True, indent=2)+'\n')
    print('RESULT', summary, 'production unchanged', flush=True)


if __name__ == '__main__':
    main()
