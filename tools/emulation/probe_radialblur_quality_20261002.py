#!/usr/bin/env python3
"""Restore the original FLOAT32 Quality setup and Rotation control conversion.

Native frames, contexts and traces stay in the private output directory. Public
reports retain hashes, constructed settings and a few setup scalar witnesses.
"""
import argparse
import copy
import json
from pathlib import Path
import struct
import subprocess

import pefile
from PIL import Image
import probe_radialblur_seed_thickness_20261002 as profiles

public = profiles.public
ENV = profiles.ENV
BEFORE = public.ROOT/'reports/radialblur_seed_thickness_public_20261002.json'
BEFORE_REVISION = '9dc47897965a58795dcc615e4dbec5f5f826af1f'
DECLARATIONS = public.ROOT/'reports/radialblur_size_range_public_20261002.json'


def before_source():
    source = subprocess.check_output(['git', 'show', BEFORE_REVISION+':mac/OLMRadialBlur/OLMRadialBlur.cpp'], cwd=public.ROOT).decode()
    assert public.sha(source.encode()) == json.loads(BEFORE.read_text())['source_sha256']
    return source


def candidate_source(source):
    start = source.index('        ((info.noise_type == 1 && info.quality == 5.0) ||', source.index('static bool IsGenericProceduralNoiseProfile('))
    end = source.index('\n}', start)
    source = source[:start]+'        (info.noise_type == 1 || info.noise_type == 2);'+source[end:]
    old = 'std::isfinite(info.quality) && info.quality >= 1.0 && info.quality <= 5.0 &&'
    assert source.count(old) == 1
    source = source.replace(old, old.replace('<= 5.0', '<= 50.0'))
    old = '''\tconst double quality = info.quality > 0.0 ? info.quality : 5.0;
\tconst double step_deg = 1.0 / quality;
\tconst double step_rad = step_deg * kPi / 180.0;
\tconst A_long angular_count = (A_long)(360.0 / step_deg);'''
    new = '''\t// Original builder: FLOAT32 Quality -> DIVSS reciprocal; constructor:
\t// CVTSS2SD -> MULSD stored constant -> FLOAT32 radians. Count uses DIVSS.
\tconst bool use_native_quality_setup = use_generic_baseline || use_generic_size_noise;
\tconst double quality = use_native_quality_setup ? (double)(float)info.quality : (info.quality > 0.0 ? info.quality : 5.0);
\tconst double step_deg = use_native_quality_setup ? (double)RadialF32Div(1.0f, (float)quality) : 1.0 / quality;
\tconst double step_rad = use_native_quality_setup ? (double)(float)(step_deg * 0.017453292500000002) : step_deg * kPi / 180.0;
\tconst A_long angular_count = use_native_quality_setup ? (A_long)RadialF32Div(360.0f, (float)step_deg) : (A_long)(360.0 / step_deg);'''
    assert source.count(old) == 2
    source = source.replace(old, new)
    # Original Zoom 56f0 builds its table from +64 (Strength); the Offset
    # controls at +58/+60 do not replace that table length.
    old = 'polar, ZoomGaussianWeights(ZoomEffectiveLength(worker_info)), polar_valid,'
    new = 'polar, ZoomGaussianWeights(use_native_quality_setup ? info.outer_strength : ZoomEffectiveLength(worker_info)), polar_valid,'
    assert source.count(old) == 1
    source = source.replace(old, new)
    start = source.index('static PF_Err RenderRotationTyped(')
    prefix, rotation = source[:start], source[start:]
    old = '''\t\tconst A_long outer_fade_span = std::max<A_long>(0, info.outer_edge_fade - 1);
\t\tconst A_long inner_fade_span = std::max<A_long>(0, info.inner_edge_fade - 1);'''
    new = '''\t\t// 4640 scales each raw integer by DOUBLE 0.2/step before CVTTSD2SI.
\t\tconst double native_quality_scale = 0.2 / step_deg;
\t\tconst auto native_quality_control = [&](A_long value) {
\t\t\treturn std::max<A_long>(0, (A_long)((double)value * native_quality_scale));
\t\t};
\t\tconst A_long outer_fade_span = use_native_quality_setup ? native_quality_control(info.outer_edge_fade) : std::max<A_long>(0, info.outer_edge_fade - 1);
\t\tconst A_long inner_fade_span = use_native_quality_setup ? native_quality_control(info.inner_edge_fade) : std::max<A_long>(0, info.inner_edge_fade - 1);'''
    assert rotation.count(old) == 1
    rotation = rotation.replace(old, new)
    old = 'const A_long outer_span = info.outer_offset_mode == 3'
    new = '''const A_long outer_span = use_native_quality_setup
\t\t\t\t? (info.outer_offset_mode == 3 ? DynamicOffsetForRadius(radius_count, native_quality_control(info.outer_offset), ri)
\t\t\t\t   : (info.outer_offset_mode == 2 ? std::max(native_quality_control(info.outer_strength), DynamicOffsetForRadius(radius_count, native_quality_control(info.outer_offset), ri)) : native_quality_control(info.outer_strength)))
\t\t\t\t: info.outer_offset_mode == 3'''
    assert rotation.count(old) == 1
    rotation = rotation.replace(old, new)
    old = 'const A_long inner_span = use_dynamic_inner_offset &&'
    new = '''const A_long inner_span = use_native_quality_setup
\t\t\t\t? (info.inner_offset_mode == 3 ? DynamicOffsetForRadius(radius_count, native_quality_control(info.inner_offset), ri)
\t\t\t\t   : (info.inner_offset_mode == 2 ? std::max(native_quality_control(info.inner_strength), DynamicOffsetForRadius(radius_count, native_quality_control(info.inner_offset), ri)) : native_quality_control(info.inner_strength)))
\t\t\t\t: use_dynamic_inner_offset &&'''
    assert rotation.count(old) == 1
    source = prefix+rotation.replace(old, new)
    old = 'const uint64_t angular = (uint64_t)(360.0L * (long double)info.quality);'
    new = '''const float budget_quality_step = RadialF32Div(1.0f, (float)info.quality);
\tconst uint64_t angular = (uint64_t)RadialF32Div(360.0f, budget_quality_step);'''
    assert source.count(old) == 1
    source = source.replace(old, new)
    old = 'const uint64_t strength = (uint64_t)info.outer_strength + (uint64_t)info.inner_strength;'
    new = '''const uint64_t raw_strength = (uint64_t)info.outer_strength + (uint64_t)info.inner_strength;
\tconst double budget_quality_scale = 0.2 / (double)budget_quality_step;
\tconst uint64_t scaled_strength = info.blur_type == 2
\t\t? (uint64_t)((double)info.outer_strength * budget_quality_scale) +
\t\t  (uint64_t)((double)info.inner_strength * budget_quality_scale) : raw_strength;
\tconst uint64_t strength = std::max(raw_strength, scaled_strength);'''
    assert source.count(old) == 1
    return source.replace(old, new)


def independent_cases():
    cases = []
    def add(family, quality, group, geometry, depth, pattern='diagonal', changes=None):
        params = public.initial.settings(family, *geometry)
        values = {20: quality, **(changes or {})}
        for param in params:
            if param['slot'] in values:
                param['value'] = values[param['slot']]
        cases.append(dict(family=family, geometry=geometry, depth=depth, pattern=pattern,
            state='quality_'+group, parameters=params, group=group, matrix='quality', row_index=len(cases)))
    qualities = list(range(1, 51))+[1.0000000596046448, 1.0000001192092896, 1.01, 1.1, 1.7, 3.4,
        4.999999523162842, 4.999999761581421, 5.000000238418579, 5.000000476837158,
        6.666666507720947, 12.3456789, 25.01, 33.3, 49.99, 49.999996185302734, 49.99999809265137]
    for family in [1, 2]:
        for quality in qualities:
            for group in ['plain', 'noise1', 'dual', 'mode2', 'mode3']:
                changes = {27: 997, 29: 3.4}
                if group != 'plain':
                    changes.update({22: 37.5, 24: 33.3, 25: 1 if group == 'noise1' else 2, 28: 1})
                if group in ['dual', 'mode2', 'mode3']:
                    changes.update({7: 37, 10: 3, 13: 37, 17: 2.5, 18: 17})
                if group == 'mode2':
                    changes.update({5: 2, 6: 2})
                    if family == 2: changes.update({11: 2, 12: 4})
                if group == 'mode3':
                    changes.update({5: 3, 6: 4})
                    if family == 2: changes.update({11: 3, 12: 2})
                for depth in [8, 16, 32]:
                    add(family, quality, group, [17, 15] if group == 'plain' else [23, 13], depth,
                        'opaque' if group == 'noise1' else 'diagonal', changes)
        for quality in [1, 3, 5, 6, 3.4, 49.99]:
            for mode in [1, 2, 3]:
                changes = {7: 37, 13: 31, 10: 3, 5: mode, 6: 0 if mode == 1 else 2,
                    27: 53, 29: 3.4, 22: 37.5, 24: 33.3, 25: 2, 17: 2.5, 18: 17}
                if family == 2: changes.update({11: mode, 12: 0 if mode == 1 else 4})
                for depth in [8, 16, 32]: add(family, quality, 'asymmetric', [23, 13], depth, changes=changes)
        for geometry in [[9, 7], [32, 18]]:
            for quality in [1, 3, 5]:
                for noise in [0, 50]:
                    for depth in [8, 16, 32]:
                        for pattern in ['diagonal', 'opaque']:
                            add(family, quality, 'legacy_overlap', geometry, depth, pattern, {24: noise})
    assert len(cases) == 2262
    return cases


def retained_cases():
    cases = profiles.retained_cases()+json.loads(BEFORE.read_text())['independent_rows']
    assert len(cases) == 4339
    return cases


def original_rule():
    pe = pefile.PE(str(public.initial.AEX))
    return dict(setup_code_sha256=public.sha(pe.get_data(0x87df, 0x8830-0x87df)),
        zoom_constructor_code_sha256=public.sha(pe.get_data(0xa810, 0xa850-0xa810)),
        rotation_constructor_code_sha256=public.sha(pe.get_data(0x1ac0, 0x1b10-0x1ac0)),
        rotation_scale_code_sha256=public.sha(pe.get_data(0x46f3, 0x47fc-0x46f3)),
        zoom_strength_setup_code_sha256=public.sha(pe.get_data(0x57a4, 0x5835-0x57a4)),
        radian_constant_f64_le_hex=pe.get_data(0x212d8, 8).hex(),
        scale_constant_f64_le_hex=pe.get_data(0x21608, 8).hex(),
        rule='Builder converts Quality to FLOAT32 then DIVSS 1/Quality; constructors multiply the FLOAT32 reciprocal by DOUBLE radians constant then round to FLOAT32. Rotation uses DOUBLE 0.2/step and CVTTSD2SI for Strength, Offset and Fade.')


def field_cases():
    cases = []
    for family in [1, 2]:
        for quality in [1, 3, 5, 6, 1.1, 3.4, 4.999999761581421, 5.000000238418579, 49.99999809265137, 50]:
            for mode in [1, 2, 3]:
                params = public.initial.settings(family, 23, 13)
                changes = {20: quality, 4: 4, 5: mode, 6: 0 if mode == 1 else 2, 10: 3, 7: 37, 13: 31}
                if family == 2: changes.update({11: mode, 12: 0 if mode == 1 else 4})
                for param in params:
                    if param['slot'] in changes: param['value'] = changes[param['slot']]
                cases.append(dict(family=family, geometry=[23, 13], depth=8, pattern='diagonal',
                    state='quality_fields', parameters=params))
    return cases


def native_fields(worker, directory):
    directory.mkdir(parents=True, exist_ok=False)
    rows = []
    f32 = lambda value: struct.unpack('<f', struct.pack('<f', value))[0]
    for index, case in enumerate(field_cases()):
        values = {p['slot']: p['value'] for p in case['parameters']}
        image = Image.new('RGBA', case['geometry'])
        image.putdata([(r, g, b, a) for a, r, g, b in public.initial.pixels(*case['geometry'], case['pattern'])])
        image.save(directory/'input.png')
        assignments = [f"param_{p['slot']}@{p['slot']}"+(':angle' if p['kind'] == 'a' else '')+'='+
            (','.join(map(str, p['value'])) if isinstance(p['value'], list) else str(p['value']))
            for p in public.native_case(case)['parameters']]
        watches = ['--watch', 'function=0x8690,arg=r9,size=272', '--watch',
            f"function={'0xa810' if case['family'] == 1 else '0x1ac0'},arg=rcx,size=24,occurrence=1"]
        if case['family'] == 2:
            watches += ['--watch', 'function=0x4640,arg=rcx,size=64,occurrence=1',
                '--watch', 'function=0x4640,arg=rcx,offset=240104,size=8,occurrence=1',
                '--watch', 'function=0x4640,arg=rcx,offset=248112,size=8,occurrence=1']
        else:
            watches += ['--watch', 'function=0x56f0,arg=rcx,offset=16088,size=8,occurrence=1',
                '--watch', 'function=0x56f0,arg=rcx,offset=16896,size=8,occurrence=1']
        run = subprocess.run([str(worker), 'render-trace-png', str(public.initial.AEX),
            str(directory/'input.png'), str(directory/'output.png'), *watches, *assignments], check=True, capture_output=True)
        (directory/f'trace_{index}.json').write_bytes(run.stdout)
        trace = json.loads(run.stdout)
        assert not trace['render_error'] and trace['guards_intact']
        assert not trace['unsupported_suite_calls'] and not trace['dropped_unsupported_suite_calls']
        smart = next(t for t in trace['execution_traces'] if t['selector'] == 'SMART_RENDER')
        assert not smart['truncated'] and not smart['dropped_memory_witnesses']
        ws = {wid: [w for w in smart['memory_witnesses'] if w['watch_id'] == wid]
              for wid in ['watch-'+str(i+1) for i in range(4 if case['family'] == 1 else 5)]}
        assert all(len(w) == 1 for w in ws.values())
        config = bytes.fromhex(ws['watch-1'][0]['after']['hex'])
        ctor = bytes.fromhex(ws['watch-2'][0]['after']['hex'])
        step = f32(1/f32(values[20])); radian = f32(step*0.017453292500000002)
        assert struct.unpack_from('<f', config, 0x80)[0] == step
        offset = 16 if case['family'] == 1 else 0
        assert struct.unpack_from('<2f', ctor, offset) == (step, radian)
        raw_controls = dict(outer_offset=values[6], inner_offset=values[12], outer_strength=values[4],
            inner_strength=values[10], outer_fade=values[7], inner_fade=values[13])
        raw_offsets = dict(outer_offset=0x58, inner_offset=0x60, outer_strength=0x64,
            inner_strength=0x68, outer_fade=0x6c, inner_fade=0x70)
        assert {k: struct.unpack_from('<i', config, o)[0] for k, o in raw_offsets.items()} == raw_controls
        scaled = None
        if case['family'] == 2:
            work = bytes.fromhex(ws['watch-3'][0]['after']['hex'])
            strength = bytes.fromhex(ws['watch-4'][0]['after']['hex'])
            fade = bytes.fromhex(ws['watch-5'][0]['after']['hex'])
            scaled = dict(outer_offset=struct.unpack_from('<i', work, 0x28)[0],
                inner_offset=struct.unpack_from('<i', work, 0x30)[0],
                outer_strength=struct.unpack_from('<i', strength)[0], inner_strength=struct.unpack_from('<i', strength, 4)[0],
                outer_fade=struct.unpack_from('<i', fade)[0], inner_fade=struct.unpack_from('<i', fade, 4)[0])
            assert scaled == {k: int(v*(0.2/step)) for k, v in raw_controls.items()}
        else:
            strength = bytes.fromhex(ws['watch-3'][0]['after']['hex'])
            fade = bytes.fromhex(ws['watch-4'][0]['after']['hex'])
            scaled = dict(outer_strength=struct.unpack_from('<i', strength)[0],
                inner_strength=struct.unpack_from('<i', strength, 4)[0],
                outer_fade=struct.unpack_from('<i', fade)[0], inner_fade=struct.unpack_from('<i', fade, 4)[0])
            assert scaled == {k: raw_controls[k] for k in scaled}
        rows.append(dict(case=case, step_f32_word=f'{struct.unpack_from("<I", config, 0x80)[0]:08x}',
            radian_f32_word=f'{struct.unpack_from("<I", ctor, offset+4)[0]:08x}',
            raw_controls=raw_controls, scaled_controls=scaled, setup_exact=True, trace_sha256=public.sha(run.stdout)))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--parent-worker', type=Path, required=True)
    ap.add_argument('--window-worker', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--report', type=Path, required=True)
    args = ap.parse_args(); args.output.mkdir(parents=True, exist_ok=False)
    before = json.loads(BEFORE.read_text()); source = before_source(); candidate = candidate_source(source)
    start_source = public.sha(public.SOURCE.read_bytes()); start_core = public.sha(profiles.CORE.read_bytes())
    assert public.sha(args.parent_worker.read_bytes()) == before['controlled_worker_sha256']
    assert public.sha(args.window_worker.read_bytes()) == before['window_worker_sha256']
    assert public.sha(public.initial.AEX.read_bytes()) == before['aex_sha256']
    assert start_source == before['source_sha256'] and start_core == before['core_sha256']
    binaries = {name: (profiles.default_contract_build(args.output/name, candidate) if name == 'default'
        else public.build(args.output/name, candidate, name == 'san')) for name in ['o2', 'san', 'default']}
    old_binary = public.build(args.output/'before', source)
    retained = retained_cases()
    for index, case in enumerate(before['rows']+retained):
        for binary in binaries.values():
            for command in ['classic', 'smart']:
                error, raw, metadata = public.mac_render(binary, args.output, case, command, ENV)
                expected = case['results'][command]
                assert error == expected['error'] and public.sha(raw) == expected['raw_sha256'] and metadata == expected['metadata'], (index, case['family'], case['depth'])
        if (index+1) % 500 == 0: print('QUALITY_RETAINED', index+1, flush=True)
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
                assert not error and raw == native, (case, name, command, error)
                result = dict(error=error, raw_sha256=public.sha(raw), raw_exact=True, metadata=metadata,
                    before_error=old_error, before_raw_exact=not old_error and old_raw == native)
                if name == 'o2': results[command] = result
                else: assert result == results[command]
        independent.append(dict(case, input_sha256=public.sha(public.fixture(case)), reference_raw_sha256=public.sha(native), results=results))
        if len(independent) % 100 == 0:
            (args.output/'partial_independent.json').write_text(json.dumps(independent, indent=2)+'\n')
            print('QUALITY_INDEPENDENT', len(independent), flush=True)
    fields = native_fields(args.window_worker, args.output/'fields')
    assert public.sha(public.SOURCE.read_bytes()) == start_source and public.sha(profiles.CORE.read_bytes()) == start_core
    report = dict(schema='radialblur.quality-public/1', before_revision=BEFORE_REVISION,
        source_before_sha256=before['source_sha256'], source_sha256=public.sha(candidate.encode()),
        header_sha256=before['header_sha256'], core_sha256=start_core, aex_sha256=before['aex_sha256'],
        controlled_worker_sha256=before['controlled_worker_sha256'], window_worker_sha256=before['window_worker_sha256'],
        probe_start_source_sha256=start_source, production_source_and_core_changed_during_probe=False,
        summary=before['summary'], rows=copy.deepcopy(before['rows']), independent_rows=independent,
        independent_summary=dict(case_count=len(independent), both_commands_exact=len(independent),
            before_rejected=sum(bool(r['results']['classic']['before_error']) for r in independent),
            before_different=sum(not r['results']['classic']['before_raw_exact'] and not r['results']['classic']['before_error'] for r in independent)),
        retained_independent_case_count=len(retained), candidate_public_replay_count=(len(before['rows'])+len(retained)+len(independent))*6,
        native_setup_fields=fields, native_setup_case_count=len(fields), original_quality_rule=original_rule(),
        native_parameter_declarations=[p for p in json.loads(DECLARATIONS.read_text())['native_parameter_declarations'] if p['slot'] == 20],
        dependencies_sha256={str(path.relative_to(public.ROOT)): public.sha(path.read_bytes())
            for path in [Path(__file__), Path(profiles.__file__), BEFORE, DECLARATIONS, public.SOURCE.with_suffix('.h'), profiles.CORE, public.initial.HARNESS]},
        claims_not_made=before['claims_not_made']+['Quality witnesses and native setup do not prove all controls/inputs, host UI/save/ROI/downsample, native Windows ISA/UCRT/AE or all-ten completion.'])
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    print('QUALITY_PUBLIC_DONE', report['independent_summary'], 'REPLAYS', report['candidate_public_replay_count'], 'FIELDS', len(fields), flush=True)


if __name__ == '__main__': main()
