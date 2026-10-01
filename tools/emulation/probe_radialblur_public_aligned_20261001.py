#!/usr/bin/env python3
"""SDK public RadialBlur comparisons with the fixture host's percent Point API.

The initial probe is retained verbatim as historical evidence. Its Point values
were pixels on Mac but percentages on AEXCompat, so its raw mismatches cannot
be attributed to the numerical port. Here both APIs materialize the same fixed
pixel coordinate. The worker's typed Angle API already uses degrees.
"""
import argparse
import copy
import json
from pathlib import Path
import tempfile

import probe_radialblur_topology_20261001 as initial

ROOT = initial.ROOT
SOURCE = initial.SOURCE
sha = initial.sha
fixture = initial.fixture
specifications = initial.specifications
build = initial.build
mac_render = initial.mac_render


def native_case(case):
    converted = copy.deepcopy(case)
    w, h = case['geometry']
    for parameter in converted['parameters']:
        if parameter['kind'] == 'p':
            x, y = parameter['value']
            parameter['value'] = [100.0*x/w, 100.0*y/h]
    return converted


def native_render(worker, directory, case):
    return initial.native_render(worker, directory, native_case(case))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--worker', type=Path, required=True)
    parser.add_argument('--controlled-build', type=Path, required=True)
    parser.add_argument('--matrix', choices=('getters', 'topology'), required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    controlled = json.loads(args.controlled_build.read_text())
    assert sha(initial.AEX.read_bytes()) == initial.AEX_SHA
    assert sha(args.worker.read_bytes()) == controlled['controlled_worker_sha256']
    assert controlled['frozen_worker_sha256'] == initial.WORKER_SHA
    assert controlled['frozen_source_and_worker_unchanged']
    for field, name in [('patch_sha256', 'aexcompat_radial_controlled_math_20261001.patch'),
                        ('builder_sha256', 'build_radialblur_controlled_math_worker_20261001.py')]:
        assert controlled[field] == sha(Path(__file__).with_name(name).read_bytes())
    source = SOURCE.read_text()
    cases = []
    with tempfile.TemporaryDirectory(prefix='radial_aligned_') as directory:
        temp = Path(directory)
        binary = build(temp/'o2', source)
        for spec in specifications(args.matrix):
            native, frame, payload, close, declarations = native_render(args.worker, temp, spec)
            results = {}
            for route in ('classic', 'smart'):
                error, raw, metadata = mac_render(binary, temp, spec, route)
                results[route] = {
                    'error': error, 'raw_sha256': sha(raw) if not error else None,
                    'raw_exact': not error and raw == native,
                    'different_bytes': sum(a != b for a, b in zip(native, raw)) if not error else None,
                    'first_differences': [{'offset': i, 'aex': a, 'mac': b}
                                          for i, (a, b) in enumerate(zip(native, raw)) if a != b][:12]
                                         if not error else [],
                    'metadata': metadata,
                }
            case = dict(spec, input_sha256=sha(fixture(spec)), native_raw_sha256=sha(native),
                        frame_done=frame, parameter_payload=payload,
                        native_api_parameters=native_case(spec)['parameters'],
                        session_clean=close['session_clean'],
                        unsupported_suite_calls=close['unsupported_suite_calls'], results=results)
            cases.append(case)
            if len(cases) % 12 == 0:
                print('RADIAL_ALIGNED', args.matrix, len(cases),
                      sum(all(r['raw_exact'] for r in c['results'].values()) for c in cases), flush=True)
    dependencies = [Path(__file__), Path(initial.__file__), initial.HARNESS, SOURCE,
                    SOURCE.parent/'OLMRadialBlur.h', SOURCE.parent/'OLMRadialBlur_Strings.cpp',
                    SOURCE.parent/'OLMRadialBlur_Strings.h', ROOT/'core/dblur_noise.h',
                    ROOT/'core/olm_sha256_rows.h', ROOT/'Util/AEGP_SuiteHandler.cpp',
                    ROOT/'Util/MissingSuiteError.cpp']
    report = {
        'schema': 'radialblur.aligned-public/1', 'matrix': args.matrix, 'case_count': len(cases),
        'source_sha256': sha(source.encode()), 'aex_sha256': initial.AEX_SHA,
        'worker_sha256': sha(args.worker.read_bytes()), 'frozen_worker_sha256': initial.WORKER_SHA,
        'controlled_build_sha256': sha(args.controlled_build.read_bytes()),
        'reference_kind': 'controlled-power2-log2f-and-host-atan2f',
        'point_api': {'mac': 'fixed pixel coordinates', 'worker': 'percent of frame extent',
                      'conversion': '100 * requested pixels / extent'},
        'summary': {'both_cmd_exact_count': sum(all(r['raw_exact'] for r in c['results'].values())
                                              for c in cases)},
        'native_parameter_declarations': declarations, 'cases': cases,
        'dependencies_sha256': {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in dependencies},
        'claims_not_made': [
            'Initial unaligned captures do not prove a numerical port mismatch',
            'Controlled imports do not prove native Windows UCRT equivalence',
            'Fake SDK hosts do not prove installed/native AE behavior',
            'No all-input/settings/topology/UI/save/ROI/downsample or all-ten completion',
        ],
    }
    args.report.write_text(json.dumps(report, sort_keys=True, indent=2)+'\n')
    print('RESULT', report['summary'], flush=True)


if __name__ == '__main__':
    main()
