#!/usr/bin/env python3
"""Restore legal Gain through the original FLOAT32 getter and RGB writer.

Original AEX/worker stay unchanged. Raw images and traces stay private; the
public report contains hashes, constructed settings and scalar getter words.
"""
import argparse
import copy
import json
from pathlib import Path
import struct
import subprocess

import pefile
from PIL import Image
import probe_radialblur_quality_20261002 as quality

profiles = quality.profiles
public = quality.public
ENV = quality.ENV
BEFORE = public.ROOT/'reports/radialblur_quality_public_20261002.json'
BEFORE_REVISION = '1e3be713a46f6d5e2be8e06841baeb6537df7a42'
DECLARATIONS = quality.DECLARATIONS


def before_source():
    source = subprocess.check_output(['git', 'show', BEFORE_REVISION+':mac/OLMRadialBlur/OLMRadialBlur.cpp'], cwd=public.ROOT).decode()
    assert public.sha(source.encode()) == json.loads(BEFORE.read_text())['source_sha256']
    return source


def candidate_source(source):
    old = '\t\tinfo.brightness_gain == 1.0 &&\n\t\t(std::isfinite(info.size_variation)'
    new = '\t\tstd::isfinite(info.brightness_gain) && info.brightness_gain >= 0.0 && info.brightness_gain <= 10.0 &&\n\t\t(std::isfinite(info.size_variation)'
    assert source.count(old) == 1
    source = source.replace(old, new)
    # Original 9680 samples both block and smooth noise with a stored FLOAT32
    # reciprocal. Rotation's duplicate helpers still used direct division.
    old = '\tconst float sample_x = RadialF32Div((float)x, cell_size);\n\tconst float sample_y = RadialF32Div((float)y, cell_size);'
    new = '\tconst float inverse_cell_size = RadialF32Div(1.0f, cell_size);\n\tconst float sample_x = RadialF32Mul((float)x, inverse_cell_size);\n\tconst float sample_y = RadialF32Mul((float)y, inverse_cell_size);'
    assert source.count(old) == 2
    return source.replace(old, new)


def gains():
    return list(range(11))+[-0.0, 1e-50, 2**-150, 2**-149, 2**-126, 0.000001,
        0.1, 0.5, 0.9999999403953552, 0.9999999701976776, 1.0000000596046448,
        1.0000001192092896, 1.1, 1.9999998807907104, 2.0000001192092896,
        2.000000238418579, 2.25, 3.4, 9.99, 9.999999046325684, 9.999999523162842]


def independent_cases():
    cases = []
    def add(family, gain, group, depth, quality_value=3.4, geometry=None):
        geometry = geometry or [23, 13]
        params = public.initial.settings(family, *geometry)
        changes = {21: gain, 20: 5 if group == 'plain' else quality_value}
        pattern = dict(plain='diagonal', noise1='opaque', dual='islands', mode2='ring', mode3='right')[group]
        if group != 'plain':
            changes.update({22: 37.5, 24: 33.3, 25: 1 if group == 'noise1' else 2, 27: 53, 29: 3.4})
        if group in ['dual', 'mode2', 'mode3']:
            changes.update({7: 37, 10: 3, 13: 31, 17: 2.5, 18: 17})
        if group in ['mode2', 'mode3']:
            mode = 2 if group == 'mode2' else 3
            changes.update({5: mode, 6: 2, 28: 1})
            if family == 2: changes.update({11: mode, 12: 4})
        for param in params:
            if param['slot'] in changes: param['value'] = changes[param['slot']]
        cases.append(dict(family=family, geometry=geometry, depth=depth, pattern=pattern,
            state='gain_'+group, parameters=params, group=group, matrix='gain', row_index=len(cases)))
    for family in [1, 2]:
        for gain in gains():
            for group in ['plain', 'noise1', 'dual', 'mode2', 'mode3']:
                for depth in [8, 16, 32]: add(family, gain, group, depth)
        for q in [1, 50]:
            for gain in [0, 0.1, 1.0000000596046448, 2.25, 10]:
                for group in ['noise1', 'dual', 'mode3']:
                    for depth in [8, 16, 32]: add(family, gain, group, depth, q, [17, 15])
    assert len(cases) == 1140
    return cases


def retained_cases():
    cases = quality.retained_cases()+json.loads(BEFORE.read_text())['independent_rows']
    assert len(cases) == 6601
    return cases


def original_rule():
    pe = pefile.PE(str(public.initial.AEX))
    return dict(getter_code_sha256=public.sha(pe.get_data(0x881f, 0x883c-0x881f)),
        pf8_gain_writer_code_sha256=public.sha(pe.get_data(0x7bb0, 0x7c19-0x7bb0)),
        pf16_gain_writer_code_sha256=public.sha(pe.get_data(0x73a0, 0x7409-0x73a0)),
        pf32_gain_writer_code_sha256=public.sha(pe.get_data(0x83c0, 0x8429-0x83c0)),
        noise_sampler_code_sha256=public.sha(pe.get_data(0x9680, 0x96c6-0x9680)),
        float_getter_conversion_code_sha256=public.sha(pe.get_data(0x1a270, 14)),
        config_gain_offset=0x38, internal_parameter_id=0x10,
        rule='Builder e430 stores FLOAT32 Gain at config+0x38. Typed callers load it with MOVSS and multiply RGB with MULSS; alpha is unchanged. Caller MINSS and the depth-specific writer follow.')


def field_cases():
    cases = []
    for family in [1, 2]:
        for gain in gains():
            params = public.initial.settings(family, 23, 13)
            next(p for p in params if p['slot'] == 21)['value'] = gain
            cases.append(dict(family=family, geometry=[23, 13], depth=8, pattern='diagonal',
                state='gain_fields', parameters=params))
    return cases


def native_fields(worker, directory):
    directory.mkdir(parents=True, exist_ok=False)
    rows = []
    for index, case in enumerate(field_cases()):
        gain = next(p['value'] for p in case['parameters'] if p['slot'] == 21)
        image = Image.new('RGBA', case['geometry'])
        image.putdata([(r, g, b, a) for a, r, g, b in public.initial.pixels(*case['geometry'], case['pattern'])])
        image.save(directory/'input.png')
        assignments = [f"param_{p['slot']}@{p['slot']}"+(':angle' if p['kind'] == 'a' else '')+'='+
            (','.join(map(str, p['value'])) if isinstance(p['value'], list) else str(p['value']))
            for p in public.native_case(case)['parameters']]
        run = subprocess.run([str(worker), 'render-trace-png', str(public.initial.AEX),
            str(directory/'input.png'), str(directory/'output.png'), '--watch',
            'function=0x8690,arg=r9,size=272', *assignments], check=True, capture_output=True)
        (directory/f'trace_{index}.json').write_bytes(run.stdout)
        trace = json.loads(run.stdout)
        assert not trace['render_error'] and trace['guards_intact']
        assert not trace['unsupported_suite_calls'] and not trace['dropped_unsupported_suite_calls']
        smart = next(t for t in trace['execution_traces'] if t['selector'] == 'SMART_RENDER')
        assert not smart['truncated'] and not smart['dropped_memory_witnesses']
        witnesses = [w for w in smart['memory_witnesses'] if w['watch_id'] == 'watch-1']
        assert len(witnesses) == 1
        config = bytes.fromhex(witnesses[0]['after']['hex'])
        actual = config[0x38:0x3c]
        expected = struct.pack('<f', gain)
        assert actual == expected, (gain, actual.hex(), expected.hex())
        rows.append(dict(case=case, gain_f32_word=f'{struct.unpack("<I", actual)[0]:08x}',
            getter_exact=True, trace_sha256=public.sha(run.stdout)))
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
            print('GAIN_INDEPENDENT', len(independent), flush=True)
    for index, case in enumerate(before['rows']+retained):
        for binary in binaries.values():
            for command in ['classic', 'smart']:
                error, raw, metadata = public.mac_render(binary, args.output, case, command, ENV)
                expected = case['results'][command]
                assert error == expected['error'] and public.sha(raw) == expected['raw_sha256'] and metadata == expected['metadata'], (index, case['family'], case['depth'])
        if (index+1) % 500 == 0: print('GAIN_RETAINED', index+1, flush=True)
    fields = native_fields(args.window_worker, args.output/'fields')
    assert public.sha(public.SOURCE.read_bytes()) == start_source and public.sha(profiles.CORE.read_bytes()) == start_core
    report = dict(schema='radialblur.gain-public/1', before_revision=BEFORE_REVISION,
        source_before_sha256=before['source_sha256'], source_sha256=public.sha(candidate.encode()),
        header_sha256=before['header_sha256'], core_sha256=start_core, aex_sha256=before['aex_sha256'],
        controlled_worker_sha256=before['controlled_worker_sha256'], window_worker_sha256=before['window_worker_sha256'],
        probe_start_source_sha256=start_source, production_source_and_core_changed_during_probe=False,
        summary=before['summary'], rows=copy.deepcopy(before['rows']), independent_rows=independent,
        independent_summary=dict(case_count=len(independent), both_commands_exact=len(independent),
            before_rejected=sum(bool(r['results']['classic']['before_error']) for r in independent),
            before_different=sum(not r['results']['classic']['before_raw_exact'] and not r['results']['classic']['before_error'] for r in independent)),
        retained_independent_case_count=len(retained), candidate_public_replay_count=(len(before['rows'])+len(retained)+len(independent))*6,
        native_setup_fields=fields, native_setup_case_count=len(fields), original_gain_rule=original_rule(),
        native_parameter_declarations=[p for p in json.loads(DECLARATIONS.read_text())['native_parameter_declarations'] if p['slot'] == 21],
        dependencies_sha256={str(path.relative_to(public.ROOT)): public.sha(path.read_bytes())
            for path in [Path(__file__), Path(quality.__file__), Path(profiles.__file__), BEFORE, DECLARATIONS, public.SOURCE.with_suffix('.h'), profiles.CORE, public.initial.HARNESS]},
        claims_not_made=before['claims_not_made']+['Gain witnesses and native getter do not prove all controls/inputs, host UI/save/ROI/downsample, native Windows ISA/UCRT/AE or all-ten completion.'])
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    print('GAIN_PUBLIC_DONE', report['independent_summary'], 'REPLAYS', report['candidate_public_replay_count'], 'FIELDS', len(fields), flush=True)


if __name__ == '__main__': main()
