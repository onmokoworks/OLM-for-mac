#!/usr/bin/env python3
"""Compare legal Strength against unchanged original AEX public render routes.

Raw frames stay in the private output directory. Public reports record settings,
hashes and counts; controlled host imports are not general native UCRT proof.
"""
import argparse
import copy
import json
from pathlib import Path
import subprocess

import pefile
import probe_radialblur_gain_20261002 as gain

public = gain.public
profiles = gain.profiles
ENV = gain.ENV
BEFORE = public.ROOT/'reports/radialblur_gain_public_20261002.json'
BEFORE_REVISION = '47b8632a38a714e20de5983b4bf55be5444e76de'


def before_source():
    source = subprocess.check_output(['git', 'show', BEFORE_REVISION+':mac/OLMRadialBlur/OLMRadialBlur.cpp'], cwd=public.ROOT).decode()
    assert public.sha(source.encode()) == json.loads(BEFORE.read_text())['source_sha256']
    return source


def candidate_source(source):
    for side in ['outer', 'inner']:
        old = f'info.{side}_strength >= 0 && info.{side}_strength <= 64 &&'
        assert source.count(old) == 1
        source = source.replace(old, old.replace('<= 64', '<= 2000'))
    old = '? ZoomGaussianWeights(info.inner_strength)'
    new = '? (use_native_quality_setup ? RotationFadeGaussianWeights(info.inner_strength) : ZoomGaussianWeights(info.inner_strength))'
    assert source.count(old) == 1
    source = source.replace(old, new)
    old = 'polar, ZoomGaussianWeights(use_native_quality_setup ? info.outer_strength : ZoomEffectiveLength(worker_info)), polar_valid,'
    new = 'polar, (use_native_quality_setup ? RotationFadeGaussianWeights(info.outer_strength) : ZoomGaussianWeights(ZoomEffectiveLength(worker_info))), polar_valid,'
    assert source.count(old) == 1
    source = source.replace(old, new)
    for side in ['outer', 'inner']:
        old = f'std::max<A_long>(0, std::min<A_long>(\n\t\t\t\t\t(A_long)((float){side}_span * span_factor), 3000))'
        new = f'std::max<A_long>(0,\n\t\t\t\t\t(A_long)RadialF32Mul((float)std::min<A_long>({side}_span, 3000), span_factor))'
        assert source.count(old) == 1
        source = source.replace(old, new)
    old = '\t\tif (!admitted) return PF_Err_BAD_CALLBACK_PARAM;\n\t\tif (!CheckedRadialGenericBudget('
    new = '\t\tif (!admitted) return PF_Err_BAD_CALLBACK_PARAM;\n'+'\t\t// Original typed callers copy the world first and stop when all six\n\t\t// Strength, Offset and Fade integers are zero, regardless of Gain/Noise.\n\t\tif (info.outer_strength == 0 && info.inner_strength == 0 &&\n\t\t\tinfo.outer_offset == 0 && info.inner_offset == 0 &&\n\t\t\tinfo.outer_edge_fade == 0 && info.inner_edge_fade == 0) {\n\t\t\tconst size_t pixel_bytes = bitdepth == 8 ? sizeof(PF_Pixel8) :\n\t\t\t\tbitdepth == 16 ? sizeof(PF_Pixel16) : sizeof(PF_PixelFloat);\n\t\t\tfor (A_long y = 0; y < input->height; ++y) {\n\t\t\t\tstd::memcpy(reinterpret_cast<A_u_char *>(output->data) + (size_t)y * output->rowbytes,\n\t\t\t\t\treinterpret_cast<const A_u_char *>(input->data) + (size_t)y * input->rowbytes,\n\t\t\t\t\t(size_t)input->width * pixel_bytes);\n\t\t\t}\n\t\t\treturn PF_Err_NONE;\n\t\t}\n'+'\t\tif (!CheckedRadialGenericBudget('
    assert source.count(old) == 1
    source = source.replace(old, new)
    return source


def independent_cases():
    cases = []
    def add(family, strength, group, depth, quality=5, geometry=None, pattern=None):
        geometry = geometry or [9, 7]
        params = public.initial.settings(family, *geometry)
        changes = {4: 0 if group == 'inner' else strength,
                   10: 0 if group == 'outer' else strength, 20: quality}
        pattern = pattern or {'outer': 'diagonal', 'inner': 'ring', 'dual': 'islands'}[group]
        if group != 'outer':
            changes.update({7: 37, 13: 31, 21: 2.25, 22: 37.5, 24: 33.3,
                25: 2, 27: 53, 29: 3.4, 17: 2.5, 18: 17})
        for param in params:
            if param['slot'] in changes: param['value'] = changes[param['slot']]
        cases.append(dict(family=family, geometry=geometry, depth=depth, pattern=pattern,
            state='strength_'+group, parameters=params, group=group, matrix='strength', row_index=len(cases)))
    strengths = [0, 1, 2, 3, 4, 5, 17, 19, 31, 63, 64, 65, 66, 67, 68, 69, 70, 71,
        99, 100, 101, 127, 128, 129, 289, 290, 291, 499, 500, 501, 999, 1000, 1001,
        1499, 1500, 1501, 1999, 2000]
    for family in [1, 2]:
        for strength in strengths:
            for group in ['outer', 'inner', 'dual']:
                for depth in [8, 16, 32]: add(family, strength, group, depth, 5 if group == 'outer' else 3.4)
        for quality in [1, 10]:
            for strength in [65, 290, 1499, 1500, 1501, 2000]:
                for group in ['outer', 'inner', 'dual']:
                    for depth in [8, 16, 32]: add(family, strength, group, depth, quality)
        for strength in [65, 100]:
            for group in ['outer', 'inner', 'dual']:
                for depth in [8, 16, 32]: add(family, strength, group, depth, 50, [5, 3])
        for geometry in [[1, 1], [1, 7], [7, 1], [17, 11]]:
            for strength in [65, 2000]:
                for depth in [8, 16, 32]: add(family, strength, 'dual', depth, 1, geometry, 'opaque')
    for family in [1, 2]:
        for geometry in [[9, 7], [17, 11]]:
            for quality in [1, 3.4, 50]:
                for gain_value in [0, 10]:
                    for compound in [False, True]:
                        for depth in [8, 16, 32]:
                            params = public.initial.settings(family, *geometry)
                            changes = {4: 0, 10: 0, 20: quality, 21: gain_value}
                            if compound:
                                changes.update({22: 100, 24: 100, 25: 2, 27: 997,
                                    29: 3.4, 17: 2.5, 18: 17})
                            for param in params:
                                if param['slot'] in changes: param['value'] = changes[param['slot']]
                            cases.append(dict(family=family, geometry=geometry, depth=depth,
                                pattern='diagonal', state='strength_zero_copy', parameters=params,
                                group='zero_copy', matrix='strength', row_index=len(cases)))
    assert len(cases) == 1128
    return cases


def retained_cases():
    cases = gain.retained_cases()+json.loads(BEFORE.read_text())['independent_rows']
    assert len(cases) == 7741
    return cases


def original_rule():
    pe = pefile.PE(str(public.initial.AEX))
    return dict(zero_control_copy_branch_code_sha256={depth: public.sha(pe.get_data(rva, 0x28)) for depth, rva in [('8', 0x6e45), ('16', 0x7655), ('32', 0x7e65)]},
        zoom_table_setup_code_sha256=public.sha(pe.get_data(0x57a4, 0x5835-0x57a4)),
        gaussian_builder_code_sha256=public.sha(pe.get_data(0xb680, 0x135)),
        rotation_outer_cap_code_sha256=public.sha(pe.get_data(0x1cfb, 0x1d20-0x1cfb)),
        rule='Zoom B680 builds Strength weights with four-wide embedded exp and a scalar tail. Rotation 1c90 caps the raw span at 3000 before MULSS with the source scalar and CVTTSS2SI. Typed callers copy the world and skip all further processing when both Strengths, both Offsets and both Fades are zero. Existing scalar exp and ISA policy are unchanged.')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--parent-worker', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--report', type=Path, required=True)
    ap.add_argument('--pilot', action='store_true')
    args = ap.parse_args(); args.output.mkdir(parents=True, exist_ok=False)
    before = json.loads(BEFORE.read_text()); source = before_source(); candidate = candidate_source(source)
    start_source = public.sha(public.SOURCE.read_bytes()); start_core = public.sha(profiles.CORE.read_bytes())
    assert public.sha(args.parent_worker.read_bytes()) == before['controlled_worker_sha256']
    assert public.sha(public.initial.AEX.read_bytes()) == before['aex_sha256']
    assert start_source == before['source_sha256'] and start_core == before['core_sha256']
    (args.output/'candidate.cpp').write_text(candidate)
    names = ['o2'] if args.pilot else ['o2', 'san', 'default']
    binaries = {name: (profiles.default_contract_build(args.output/name, candidate) if name == 'default'
        else public.build(args.output/name, candidate, name == 'san')) for name in names}
    old_binary = public.build(args.output/'before', source)
    independent = []
    for case in independent_cases():
        native, frame, _, close, _ = public.native_render(args.parent_worker, args.output, case)
        assert not frame['render_error'] and frame['output']['guards_intact'] and close['session_clean'] and not close['unsupported_suite_calls']
        old_error, old_raw, _ = public.mac_render(old_binary, args.output, case, 'classic', ENV)
        results = {}
        for name, binary in binaries.items():
            for command in ['classic', 'smart']:
                error, raw, metadata = public.mac_render(binary, args.output, case, command, ENV)
                if error or raw != native:
                    (args.output/f"failed_native_{case['row_index']}.raw").write_bytes(native)
                    (args.output/f"failed_mac_{case['row_index']}_{name}_{command}.raw").write_bytes(raw)
                    print('STRENGTH_DIFF', case['row_index'], name, command, error,
                        sum(a != b for a, b in zip(raw, native)) if not error else None, flush=True)
                if not args.pilot: assert not error and raw == native, (case, name, command, error)
                result = dict(error=error, raw_sha256=public.sha(raw), raw_exact=not error and raw == native,
                    metadata=metadata, before_error=old_error, before_raw_exact=not old_error and old_raw == native)
                if name == 'o2': results[command] = result
                else: assert result == results[command]
        independent.append(dict(case, input_sha256=public.sha(public.fixture(case)), reference_raw_sha256=public.sha(native), results=results))
        if len(independent) % 40 == 0:
            (args.output/'partial_independent.json').write_text(json.dumps(independent, indent=2)+'\n')
            print('STRENGTH_INDEPENDENT', len(independent), sum(all(v['raw_exact'] for v in r['results'].values()) for r in independent), flush=True)
    retained = retained_cases()
    if not args.pilot:
        for index, case in enumerate(before['rows']+retained):
            for binary in binaries.values():
                for command in ['classic', 'smart']:
                    error, raw, metadata = public.mac_render(binary, args.output, case, command, ENV)
                    expected = case['results'][command]
                    assert error == expected['error'] and public.sha(raw) == expected['raw_sha256'] and metadata == expected['metadata'], (index, case['family'], case['depth'])
            if (index+1) % 500 == 0: print('STRENGTH_RETAINED', index+1, flush=True)
    assert public.sha(public.SOURCE.read_bytes()) == start_source and public.sha(profiles.CORE.read_bytes()) == start_core
    report = dict(schema='radialblur.strength-public/1', pilot=args.pilot, before_revision=BEFORE_REVISION,
        source_before_sha256=before['source_sha256'], source_sha256=public.sha(candidate.encode()),
        header_sha256=before['header_sha256'], core_sha256=start_core, aex_sha256=before['aex_sha256'],
        controlled_worker_sha256=before['controlled_worker_sha256'], window_worker_sha256=before['window_worker_sha256'],
        probe_start_source_sha256=start_source, production_source_and_core_changed_during_probe=False,
        summary=before['summary'], rows=copy.deepcopy(before['rows']), independent_rows=independent,
        independent_summary=dict(case_count=len(independent), both_commands_exact=sum(all(v['raw_exact'] for v in r['results'].values()) for r in independent),
            before_rejected=sum(bool(r['results']['classic']['before_error']) for r in independent),
            before_different=sum(not r['results']['classic']['before_raw_exact'] and not r['results']['classic']['before_error'] for r in independent)),
        retained_independent_case_count=len(retained), candidate_public_replay_count=(len(before['rows'])+len(retained)+len(independent))*6 if not args.pilot else len(independent)*2,
        original_strength_rule=original_rule(),
        native_parameter_declarations=[p for p in json.loads(gain.DECLARATIONS.read_text())['native_parameter_declarations'] if p['slot'] in [4, 10]],
        dependencies_sha256={str(path.relative_to(public.ROOT)): public.sha(path.read_bytes()) for path in [Path(__file__), Path(gain.__file__), BEFORE, gain.DECLARATIONS, public.SOURCE.with_suffix('.h'), profiles.CORE, public.initial.HARNESS]},
        claims_not_made=before['claims_not_made']+['Strength witnesses do not prove all controls/inputs, host UI/save/ROI/downsample, native Windows ISA/UCRT/AE or all-ten completion.'])
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    print('STRENGTH_PUBLIC_DONE', report['independent_summary'], 'REPLAYS', report['candidate_public_replay_count'], flush=True)


if __name__ == '__main__': main()
