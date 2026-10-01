#!/usr/bin/env python3
"""Separate the SDK phase conversion from the old 0/1 noise admission rule."""
import argparse
import copy
import json
from pathlib import Path
import re
import subprocess
import tempfile

import probe_radialblur_public_aligned_20261001 as public
import probe_radialblur_noise_offset_field_20261001 as field

BASELINE = public.ROOT/'reports/radialblur_axis_reference_public_20261001.json'
FIELD = public.ROOT/'reports/radialblur_noise_offset_field_20261001.json'
HEADER = public.SOURCE.parent/'OLMRadialBlur.h'


def candidate_sources(source, header):
    helper = '''static float RadialNoiseOffsetRadians(PF_Fixed raw_angle)
{
\t// Native a2b0: signed AD -> DOUBLE multiply -> FLOAT32 phase.
\treturn (float)((double)raw_angle * 2.663161090079238e-7);
}

'''
    anchor = 'static int32_t RadialAngleFixedRadians(PF_FpLong angle_degrees)\n'
    assert source.count(anchor) == 1
    source = source.replace(anchor, helper+anchor)
    old = 'info.noise_offset = params[OLMRADIALBLUR_NOISE_OFFSET]->u.sd.value;'
    assert source.count(old) == 1
    source = source.replace(old, 'info.noise_offset = RadialNoiseOffsetRadians(\n\t\tparams[OLMRADIALBLUR_NOISE_OFFSET]->u.ad.value);')
    assert header.count('\tA_long noise_offset;') == 1
    header = header.replace('\tA_long noise_offset;', '\tfloat noise_offset;')
    getter_only = source
    old = '''\tif (info.noise_variation != 25.0 && info.noise_variation != 100.0) return false;
\tif (info.noise_type == 1 && info.quality == 5.0) {
\t\treturn (info.seed == 1 && info.noise_offset == 0 && info.thickness == 3.0) ||
\t\t\t(info.seed == 2 && info.noise_offset == 1 && info.thickness == 10.0) ||
\t\t\t(info.seed == 1 && info.noise_offset == 1 && info.thickness == 3.0) ||
\t\t\t(info.seed == 2 && info.noise_offset == 0 && info.thickness == 10.0);
\t}
\tif (info.noise_type == 2 && info.seed == 1 && info.noise_offset == 0) {'''
    new = '''\tif (info.noise_variation != 25.0 && info.noise_variation != 100.0) return false;
\t// Nonnegative phases from the full signed AD range keep table indices valid.
\t// Negative phases can address before the native random table; still unverified.
\tif (!std::isfinite(info.noise_offset) || info.noise_offset < 0.0f ||
\t\tinfo.noise_offset > RadialNoiseOffsetRadians(std::numeric_limits<PF_Fixed>::max())) return false;
\tif (info.noise_type == 1 && info.quality == 5.0) {
\t\treturn (info.seed == 1 && info.thickness == 3.0) ||
\t\t\t(info.seed == 2 && info.thickness == 10.0);
\t}
\tif (info.noise_type == 2 && info.seed == 1) {'''
    assert source.count(old) == 1
    return getter_only, source.replace(old, new), header


def independent_cases():
    for geometry in field.GEOMETRIES:
        for family in (1, 2):
            for depth in (8, 16, 32):
                for noise_type, seed, thickness in [(1, 1, 3.0), (1, 2, 10.0), (2, 1, 3.0), (2, 1, 10.0)]:
                    for variation in (25, 100):
                        for raw in (0, 65536, 5898240, 23592960):
                            yield field.case_for(family, geometry, depth, noise_type, seed, thickness, raw, variation)


def summary(rows, variant):
    selected = [r['results'][variant] for r in rows]
    return {'case_count': len(rows),
            'both_commands_exact': sum(all(x['raw_exact'] for x in r.values()) for r in selected),
            'different': sum(not r['classic']['error'] and not r['classic']['raw_exact'] for r in selected),
            'mac_rejected': sum(bool(r['classic']['error']) for r in selected)}


def result(error, raw, metadata, native_sha):
    return {'error': error, 'raw_sha256': public.sha(raw) if not error else None,
            'raw_exact': not error and public.sha(raw) == native_sha, 'metadata': metadata}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--worker', type=Path, required=True)
    ap.add_argument('--build', type=Path, required=True)
    ap.add_argument('--report', type=Path, required=True)
    args = ap.parse_args()
    build = json.loads(args.build.read_text())
    assert public.sha(args.worker.read_bytes()) == build['worker_sha256']
    assert public.sha(public.initial.AEX.read_bytes()) == public.initial.AEX_SHA
    baseline = json.loads(BASELINE.read_text())
    source, header = public.SOURCE.read_text(), HEADER.read_text()
    assert public.sha(source.encode()) == baseline['source_sha256']
    native_field = json.loads(FIELD.read_text())
    assert native_field['summary']['plane_raw_exact'] == native_field['case_count'] == 96
    getter, candidate, candidate_header = candidate_sources(source, header)
    rows = []
    with tempfile.TemporaryDirectory(prefix='radial_offset_counterfactual_') as directory:
        temp = Path(directory)
        hp = temp/'candidate.h'
        hp.write_text(re.sub(r'^#include "([^"]+)"',
                            lambda m: ('#include "'+str((HEADER.parent/m.group(1)).resolve())+'"')
                            if (HEADER.parent/m.group(1)).is_file() else m.group(0),
                            candidate_header, flags=re.MULTILINE))
        binaries = {'before': public.build(temp/'before', source)}
        for name, text in [('getter_only', getter), ('getter_and_profiles', candidate)]:
            text = text.replace('#include "OLMRadialBlur.h"', '#include "'+str(hp)+'"')
            try:
                binaries[name] = public.build(temp/name, text)
            except subprocess.CalledProcessError as error:
                print(error.stderr.decode(), flush=True)
                raise
        for old in baseline['rows']:
            spec = {k: old[k] for k in ('family', 'geometry', 'depth', 'pattern', 'state', 'parameters')}
            before = {command: {k: old['results'][command][k] for k in ('error', 'raw_sha256', 'metadata')}
                      | {'raw_exact': old['results'][command]['corrected_raw_exact']} for command in ('classic', 'smart')}
            rows.append(dict(spec, group='retained', matrix=old['matrix'], row_index=old['row_index'],
                             input_sha256=old['input_sha256'], native_raw_sha256=old['corrected_raw_sha256'],
                             native_reacquired=False, results={'before': before}))
        for index, spec in enumerate(independent_cases()):
            raw, frame, payload, close, _ = public.native_render(args.worker, temp, spec)
            assert close['session_clean'] and not close['unsupported_suite_calls']
            native_sha = public.sha(raw)
            before = {command: result(*public.mac_render(binaries['before'], temp, spec, command), native_sha)
                      for command in ('classic', 'smart')}
            rows.append(dict(spec, group='independent', matrix='independent', row_index=index,
                             input_sha256=public.sha(public.fixture(spec)), native_raw_sha256=native_sha,
                             native_reacquired=True, frame_done=frame, parameter_payload=payload,
                             session_clean=True, results={'before': before}))
            if (index+1) % 24 == 0: print('OFFSET_NATIVE', index+1, flush=True)
        for index, row in enumerate(rows):
            for variant in ('getter_only', 'getter_and_profiles'):
                row['results'][variant] = {command: result(*public.mac_render(binaries[variant], temp, row, command),
                                                          row['native_raw_sha256']) for command in ('classic', 'smart')}
            if (index+1) % 48 == 0: print('OFFSET_CANDIDATE', index+1, flush=True)
    assert public.SOURCE.read_text() == source and HEADER.read_text() == header
    deps = [Path(__file__), Path(field.__file__), field.HARNESS, FIELD, BASELINE, Path(public.__file__),
            Path(public.initial.__file__), public.initial.HARNESS, public.ROOT/'core/dblur_noise.h']
    report = {'schema': 'radialblur.noise-offset-counterfactual/1', 'rows': rows,
              'source_before_sha256': public.sha(source.encode()), 'header_before_sha256': public.sha(header.encode()),
              'getter_only_source_sha256': public.sha(getter.encode()), 'candidate_source_sha256': public.sha(candidate.encode()),
              'candidate_header_sha256': public.sha(candidate_header.encode()),
              'aex_sha256': public.initial.AEX_SHA, 'worker_sha256': build['worker_sha256'],
              'summaries': {v: summary(rows, v) for v in binaries},
              'group_summaries': {g: {v: summary([r for r in rows if r['group'] == g], v) for v in binaries}
                                  for g in ('retained', 'independent')},
              'mac_public_replay_count': 2*384+4*len(rows), 'native_reacquisition_count': 384,
              'production_source_and_header_unchanged': True,
              'dependencies_sha256': {str(p.relative_to(public.ROOT)): public.sha(p.read_bytes()) for p in deps},
              'claims_not_made': ['This run changes disposable source copies only',
                                 'Remaining pixel mismatches are unresolved, including Rotation',
                                 'Negative phase, arbitrary seed/thickness/noise variation, native AE/UCRT remain open']}
    args.report.write_text(json.dumps(report, sort_keys=True, indent=2)+'\n')
    print('OFFSET_COUNTERFACTUAL_RESULT', report['group_summaries'], flush=True)


if __name__ == '__main__':
    main()
