#!/usr/bin/env python3
"""Verify natural Add/reciprocal differences in the original owned planes."""
import argparse
import json
from pathlib import Path

import probe_radialblur_offset_20261002 as offset
import probe_radialblur_rotation_neutral_20261001 as rotation
public = offset.public


def cases():
    rows = [c for c in offset.calibration_cases() if c['family'] == 2 and c['depth'] == 32
            and c['state'] in ['outer_add3', 'inner_add3']]
    rows += [c for c in offset.independent_cases() if c['group'] == 'offset_reciprocal'
             and c['geometry'] == [123, 1] and c['depth'] == 32
             and next(p['value'] for p in c['parameters'] if p['slot'] == 5) in [1, 3]]
    assert len(rows) == 4
    return rows


def probe(worker, directory, source):
    directory.mkdir(parents=True, exist_ok=False)
    rows = []
    for index, case in enumerate(cases()):
        temp = directory/str(index); temp.mkdir()
        raw, frame, _, close, _ = public.native_render(worker, temp, case)
        assert not frame['render_error'] and frame['output']['guards_intact'] and close['session_clean']
        case = dict(case, reference_raw_sha256=public.sha(raw))
        native, trace = rotation.trace(worker, temp, case)
        before = source
        if case['group'] == 'offset_admission':
            marker = 'if (mode == 1) return strength + dynamic;'
            assert before.count(marker) == 1
            before = before.replace(marker, 'if (mode == 1) return strength;')
        else:
            marker = '''const A_long product = (radius_count / 2) * offset;
    const float reciprocal = RadialF32Div(1.0f, static_cast<float>(radius_index + 1));
    const A_long dynamic = RadialCVTTSS2SI(RadialF32Mul(static_cast<float>(product), reciprocal));'''
            assert before.count(marker) == 1
            before = before.replace(marker, 'const A_long dynamic = DynamicOffsetForRadius(radius_count, offset, radius_index);')
        body = rotation.fields.plane_harness()
        assert body.count('w>64||h>64') == 1
        body = body.replace('w>64||h>64', 'w>8192||h>8192')
        harness = temp/'planes.cpp'; harness.write_text(body)
        comparisons = {}; hashes = {}
        with offset.noop.harness_scope(harness):
            for name, text in [('before', before), ('candidate', source)]:
                binary = public.build(temp/name, text)
                planes = temp/(name+'_planes'); planes.mkdir()
                error, rendered, _ = public.mac_render(binary, temp, case, 'classic',
                    dict(offset.ENV, ROTATION_PLANES_DIRECTORY=str(planes)))
                assert not error; hashes[name] = public.sha(rendered); comparisons[name] = {}
                for key, data in native.items():
                    actual = (planes/(key+'.f32')).read_bytes()[:len(data)]
                    assert len(actual) == len(data)
                    comparisons[name][key] = rotation.fields.compare_words(data, actual)
        assert hashes['candidate'] == public.sha(raw)
        assert all(not c['different_words'] for c in comparisons['candidate'].values())
        assert comparisons['before']['accum']['different_words'] > 0
        rows.append(dict(case=case, trace=trace, comparisons=comparisons, raw_sha256=hashes,
            candidate_source_sha256=public.sha(source.encode()),
            counterfactual_source_sha256=public.sha(before.encode())))
        print('OFFSET_NATURAL', index, {k: c['different_words'] for k, c in comparisons['before'].items()}, flush=True)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--worker', type=Path, required=True)
    ap.add_argument('--source', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--report', type=Path, required=True)
    args = ap.parse_args()
    result = probe(args.worker, args.output, args.source.read_text())
    args.report.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print('OFFSET_NATURAL_DONE', len(result), flush=True)


if __name__ == '__main__': main()
