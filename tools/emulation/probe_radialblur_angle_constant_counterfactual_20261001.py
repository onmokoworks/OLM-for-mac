#!/usr/bin/env python3
"""Isolate the previous pi/order error after correcting the SDK AD read.

Build only a disposable source copy with the previous angle expression. No
native output or production file is changed to make an experiment agree.
"""
import argparse
import json
from pathlib import Path
import tempfile

import probe_radialblur_public_aligned_20261001 as public

RAW_BOUNDARIES = {-20564372, -7055345, 14253070, 20963609}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--report', type=Path, required=True)
    args = ap.parse_args()
    capture_path = public.ROOT/'reports/radialblur_typed_angle_public_route_20261001.json'
    current_path = public.ROOT/'reports/radialblur_typed_angle_mac_baseline_20261001.json'
    capture, current = json.loads(capture_path.read_text()), json.loads(current_path.read_text())
    source = public.SOURCE.read_text()
    original = 'return (int32_t)((angle_degrees * 65536.0) * 0.017453292500000002);'
    previous = 'return (int32_t)((angle_degrees * kPi / 180.0) * 65536.0);'
    assert source.count(original) == 1
    variant = source.replace(original, previous)
    rows = []
    with tempfile.TemporaryDirectory(prefix='radial_angle_counterfactual_') as directory:
        temp = Path(directory)
        binary = public.build(temp/'o2', variant)
        for index, case in enumerate(capture['rows']):
            angle = next(p['value'] for p in case['parameters'] if p['slot'] == 18)
            if round(angle*65536) not in RAW_BOUNDARIES: continue
            error, raw, metadata = public.mac_render(binary, temp, case, 'classic')
            assert error == 0 and metadata['angle'] == angle
            actual = current['rows'][index]['results']['classic']
            rows.append({'row_index': index, 'family': case['family'], 'angle': angle,
                         'native_angle_i32': case['angle_builder_i32'], 'raw_sha256': public.sha(raw),
                         'previous_order_native_exact': public.sha(raw) == case['native_raw_sha256'],
                         'restored_order_native_exact': actual['raw_exact'],
                         'previous_and_restored_outputs_equal': public.sha(raw) == actual['raw_sha256']})
    assert len(rows) == 8
    assert all(not r['previous_and_restored_outputs_equal'] for r in rows if r['family'] == 1)
    assert all(not r['previous_order_native_exact'] for r in rows)
    assert all(r['restored_order_native_exact'] for r in rows if r['family'] == 1)
    dependencies = [Path(__file__), capture_path, current_path, public.SOURCE,
                    public.initial.HARNESS, Path(public.__file__), Path(public.initial.__file__)]
    report = {'schema': 'radialblur.angle-constant-counterfactual/1', 'rows': rows,
              'source_sha256': public.sha(source.encode()), 'disposable_variant_sha256': public.sha(variant.encode()),
              'dependencies_sha256': {str(p.relative_to(public.ROOT)): public.sha(p.read_bytes()) for p in dependencies},
              'claims_not_made': ['Variant is an isolated experiment, not production or native code',
                                 'Rotation residuals and all-input/native Windows UCRT/AE compatibility remain open']}
    args.report.write_text(json.dumps(report, sort_keys=True, indent=2)+'\n')
    print('RESULT', len(rows), 'boundary rows differ with old angle order; 4 Zoom rows restored exact', flush=True)


if __name__ == '__main__':
    main()
