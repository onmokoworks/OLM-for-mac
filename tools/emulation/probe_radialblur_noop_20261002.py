#!/usr/bin/env python3
"""Restore original all-zero copy without Blur admission or float arithmetic.

Original frames stay private. Type3's public checkout has no successful witness
and remains outside this restoration. Host envelope changes are bound separately.
"""
import argparse
import contextlib
import copy
import json
from pathlib import Path
import random
import struct

import probe_radialblur_strength_20261002 as strength
public = strength.public
ENV = strength.ENV
BEFORE = public.ROOT/'reports/radialblur_strength_public_20261002.json'


def before_source():
    source = strength.candidate_source(strength.before_source())
    assert public.sha(source.encode()) == json.loads(BEFORE.read_text())['source_sha256']
    return source


def candidate_source(source):
 marker='static PF_Err RenderWorld(PF_EffectWorld *input, PF_EffectWorld *output,\n\tPF_EffectWorld *noise_world, const OLMRadialBlurInfo &info, short bitdepth)'
 helpers='''// Original typed callers return their initial world copy when these six controls
// are zero. Type3's public checkout remains a separate unverified boundary.
static bool IsRadialNoOpControlProfile(const OLMRadialBlurInfo &info)
{
	return (info.blur_type == 1 || info.blur_type == 2) &&
		(info.noise_type == 1 || info.noise_type == 2) &&
		info.outer_strength == 0 && info.inner_strength == 0 &&
		info.outer_offset == 0 && info.inner_offset == 0 &&
		info.outer_edge_fade == 0 && info.inner_edge_fade == 0;
}

static bool RadialActiveRowBytes(short bitdepth, A_long width, std::size_t *bytes);

static PF_Err RenderRadialNoOpCopy(PF_EffectWorld *input, PF_EffectWorld *output,
	const OLMRadialBlurInfo &info, short bitdepth)
{
	std::size_t active = 0;
	if (!input || !output || input->width <= 0 || input->height <= 0 ||
		input->width != output->width || input->height != output->height ||
		info.comp_width != (PF_FpLong)input->width ||
		info.comp_height != (PF_FpLong)input->height ||
		!RadialActiveRowBytes(bitdepth, input->width, &active) ||
		input->rowbytes <= 0 || output->rowbytes <= 0 ||
		active > static_cast<std::size_t>(input->rowbytes) ||
		active > static_cast<std::size_t>(output->rowbytes) ||
		!RadialPayloadsDisjoint(input, output)) return PF_Err_BAD_CALLBACK_PARAM;
	// Copy bytes to preserve high-depth values, signed zero and NaN payloads.
	// No polar planes, float arithmetic, alignment or Blur work budget is used.
	for (A_long y = 0; y < input->height; ++y)
		std::memcpy(reinterpret_cast<A_u_char *>(output->data) + (size_t)y * output->rowbytes,
			reinterpret_cast<const A_u_char *>(input->data) + (size_t)y * input->rowbytes, active);
	return PF_Err_NONE;
}

'''
 assert source.count(marker)==1;source=source.replace(marker,helpers+marker)
 marker='''{
	if (info.noise_type == 3 && !RequiresNoiseLayer(info)) {'''
 replacement='''{
	if (IsRadialNoOpControlProfile(info)) return RenderRadialNoOpCopy(input, output, info, bitdepth);
	if (info.noise_type == 3 && !RequiresNoiseLayer(info)) {'''
 assert source.count(marker)==1;source=source.replace(marker,replacement)
 marker='''if (!err && IsGenericRadialControlProfile(info) &&
				!CheckedRadialGenericBudget'''
 replacement='''if (!err && !IsRadialNoOpControlProfile(info) && IsGenericRadialControlProfile(info) &&
				!CheckedRadialGenericBudget'''
 assert source.count(marker)==1;source=source.replace(marker,replacement)
 return source


def independent_cases():
    cases = []
    def add(family, depth, geometry, pattern, group, changes=None):
        params = public.initial.settings(family, *geometry)
        values = {4: 0, 10: 0, **(changes or {})}
        for q in params:
            if q['slot'] in values: q['value'] = values[q['slot']]
        cases.append(dict(family=family, depth=depth, geometry=geometry, pattern=pattern,
            parameters=params, group=group, matrix='noop', row_index=len(cases), state='noop_'+group))
    controls = [('baseline', {}), ('repeat_border_off', {15: 0}),
        ('outside_center', {2: [-1, 8]}), ('offset_modes_zero', {5: 2, 11: 3}),
        ('angle720_ratio5', {17: 5, 18: 720}),
        ('noise_negative_phase', {24: 100, 25: 1, 27: 1000, 28: -1, 29: 1}),
        ('ignored_compound', {15: 0, 17: 5, 18: 720, 20: 50, 21: 10, 22: 100,
                             24: 100, 25: 2, 27: 1000, 28: 90, 29: 100})]
    for name, changes in controls:
        for family in [1, 2]:
            for depth in [8, 16, 32]: add(family, depth, [9, 7], 'mixed', name, changes)
    for geometry, depths in [([1920, 1080], [8, 16, 32]), ([3840, 2160], [8]), ([4097, 3], [8, 16, 32])]:
        for depth in depths:
            for family in [1, 2]: add(family, depth, geometry, 'geometry', 'geometry', {20: 50, 21: 10})
    for depth in [16, 32]:
        patterns = ['high', 'max'] if depth == 16 else ['hdr', 'signed', 'negative_zero', 'subnormal', 'infinities', 'nan_payloads']
        for pattern in patterns:
            for family in [1, 2]: add(family, depth, [9, 7], pattern, 'hdr', {21: 10, 22: 100, 24: 100})
    for depth in [16, 32]:
        for family in [1, 2]: add(family, depth, [3840, 2160], 'uhd_high', 'uhd_high', {20: 50, 21: 10})
    for depth in [8, 16, 32]:
        for family in [1, 2]: add(family, depth, [128, 128], 'bitpatterns', 'bitpatterns',
            {15: 0, 17: 5, 18: -720, 20: 50, 21: 10, 22: 100, 24: 100, 25: 2,
             27: 1000, 28: -1, 29: 1, 2: [-128, 256], 5: 3, 11: 2})
    assert len(cases) == 82
    return cases


def fixture(case):
    depth, pattern = case['depth'], case['pattern']
    w, h = case['geometry']
    if pattern == 'mixed':
        unit = {8: bytes([255,17,31,47,0,255,2,1,128,0,0,0]),
            16: struct.pack('<12H',65535,32769,2,1,0,65535,49152,40000,32768,0,0,0),
            32: struct.pack('<12I',0x3f800000,0x40000000,0x80000000,0x7fc12345,0,0xbf800000,
                0x7f800000,0xff800000,0x3f000000,1,0x7f812345,0xff812346)}[depth]
        assert w*h == 63
        return unit*21
    if pattern == 'geometry':
        unit = {8: bytes([255,17,31,47]), 16: struct.pack('<4H',32768,123,456,789),
                32: struct.pack('<4f',1,0.125,0.25,0.5)}[depth]
        last = {8: bytes([128,3,2,1]), 16: struct.pack('<4H',16384,3,2,1),
                32: struct.pack('<4f',0.5,0.75,0.25,0)}[depth]
        return unit*(w*h-1)+last
    if pattern == 'uhd_high':
        unit = struct.pack('<4H',65535,32769,49152,40000) if depth == 16 else struct.pack('<4I',0x3fc00000,0x7f812345,0x80000000,0xff800000)
        last = struct.pack('<4H',0,65535,1,32768) if depth == 16 else struct.pack('<4I',1,0x7fc54321,0xffc12345,0x7f800000)
        return unit*(w*h-1)+last
    if pattern == 'bitpatterns':
        assert w*h*4 == 65536
        if depth == 8: return bytes(range(256))*256
        if depth == 16: return struct.pack('<65536H', *range(65536))
        words = [(sign<<31)|(exp<<23)|mantissa for sign in [0,1] for exp in range(256)
                 for mantissa in [0,1,2,0x3ffffe,0x3fffff,0x400000,0x400001,0x7ffffe,0x7fffff]]
        rng = random.Random(20261002)
        words += [rng.getrandbits(32) for _ in range(65536-len(words))]
        return struct.pack('<65536I', *words)
    if depth == 16:
        words = [32769,65535,40000,49152] if pattern == 'high' else [65535]*4
        assert pattern in ['high', 'max']
        return b''.join(struct.pack('<4H', *words[i%4:], *words[:i%4]) for i in range(w*h))
    words = {'hdr':[0x3fc00000,0x40000000,0x40800000,0x7f7fffff],
        'signed':[0xbf800000,0xc0000000,0xbf000000,0x3f800000],
        'negative_zero':[0x80000000,0,0x80000000,0],
        'subnormal':[1,0x80000001,0x007fffff,0x807fffff],
        'infinities':[0x7f800000,0xff800000,0x3f800000,0],
        'nan_payloads':[0x7fc12345,0xffc54321,0x7f812345,0xff812346]}[pattern]
    return b''.join(struct.pack('<4I', *words[i%4:], *words[:i%4]) for i in range(w*h))


@contextlib.contextmanager
def fixture_scope(case, data=None):
    previous = public.initial.fixture
    data = fixture(case) if data is None else data
    try:
        public.initial.fixture = lambda ignored: data
        yield data
    finally: public.initial.fixture = previous


def large_harness(odd_rowbytes=False):
    body = public.initial.HARNESS.read_text()
    assert body.count('w>64||h>64') == 1
    body = body.replace('w>64||h>64', 'w>8192||h>8192')
    if odd_rowbytes:
        assert body.count('irb=active+3*ps,orb=active+5*ps') == 1
        body = body.replace('irb=active+3*ps,orb=active+5*ps', 'irb=active+3,orb=active+5')
    return body


@contextlib.contextmanager
def harness_scope(path):
    previous = public.initial.HARNESS
    try:
        public.initial.HARNESS = path
        yield
    finally: public.initial.HARNESS = previous


def build(directory, source, mode='o2', odd_rowbytes=False):
    hp = directory.parent/(directory.name+'_harness.cpp')
    hp.write_text(large_harness(odd_rowbytes))
    with harness_scope(hp):
        return (strength.profiles.default_contract_build(directory, source) if mode == 'default'
                else public.build(directory, source, mode == 'san'))


def retained_cases():
    previous = json.loads(BEFORE.read_text())
    cases = previous['rows']+strength.retained_cases()+previous['independent_rows']
    assert len(cases) == 9563
    return cases


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--worker', type=Path, required=True)
    ap.add_argument('--worker-build', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--report', type=Path, required=True)
    ap.add_argument('--pilot', action='store_true')
    args = ap.parse_args(); args.output.mkdir(parents=True, exist_ok=False)
    binding = json.loads(args.worker_build.read_text())
    assert public.sha(args.worker.read_bytes()) == binding['worker_sha256']
    assert binding['parent_source_and_worker_unchanged'] and not binding['original_aex_changed']
    previous = json.loads(BEFORE.read_text()); source = before_source(); candidate = candidate_source(source)
    initial_source = public.sha(public.SOURCE.read_bytes())
    assert initial_source == previous['source_sha256']
    assert public.sha(public.initial.AEX.read_bytes()) == previous['aex_sha256']
    core = public.ROOT/'core/dblur_noise.h'; initial_core = public.sha(core.read_bytes())
    (args.output/'candidate.cpp').write_text(candidate)
    names = ['o2'] if args.pilot else ['o2', 'san', 'default']
    binaries = {name: build(args.output/name, candidate, name) for name in names}
    before_binary = build(args.output/'before', source)
    rows = []; replays = 0
    for case in independent_cases():
        with fixture_scope(case) as data:
            native, frame, _, close, _ = public.native_render(args.worker, args.output, case)
            assert native == data and frame['output']['guards_intact'] and close['session_clean']
            old_error, old_raw, _ = public.mac_render(before_binary, args.output, case, 'classic', ENV)
            old_smart_error, old_smart_raw, _ = public.mac_render(before_binary, args.output, case, 'smart', ENV)
            results = {}
            for name, binary in binaries.items():
                for command in ['classic', 'smart']:
                    error, raw, metadata = public.mac_render(binary, args.output, case, command, ENV)
                    assert not error and raw == native, (case, name, command, error)
                    result = dict(error=error, raw_sha256=public.sha(raw), raw_exact=True, metadata=metadata)
                    if name == 'o2': results[command] = result
                    else: assert result == results[command]
                    replays += 1
            rows.append(dict(case, input_sha256=public.sha(data), reference_raw_sha256=public.sha(native),
                reference_input_exact=True, results=results, before_error=old_error,
                before_raw_exact=not old_error and old_raw==native, before_smart_error=old_smart_error,
                before_smart_raw_exact=not old_smart_error and old_smart_raw==native))
            if len(rows)%10 == 0: print('NOOP_INDEPENDENT', len(rows), 'REPLAYS', replays, flush=True)
    retained = retained_cases()
    if not args.pilot:
        for name, binary in binaries.items():
            for case in retained:
                for command in ['classic', 'smart']:
                    error, raw, metadata = public.mac_render(binary, args.output, case, command, ENV)
                    expected = case['results'][command]
                    assert error == expected['error'] and public.sha(raw) == expected['raw_sha256'] and metadata == expected['metadata'], (case, name, command)
                    replays += 1
                if replays%1000 == 0: print('NOOP_RETAINED', name, replays, flush=True)
    assert public.sha(public.SOURCE.read_bytes()) == initial_source and public.sha(core.read_bytes()) == initial_core
    result = dict(schema='radialblur.noop-public/1', pilot=args.pilot,
        source_before_sha256=initial_source, source_sha256=public.sha(candidate.encode()),
        header_sha256=previous['header_sha256'], core_sha256=initial_core, aex_sha256=previous['aex_sha256'],
        controlled_worker_sha256=previous['controlled_worker_sha256'], window_worker_sha256=previous['window_worker_sha256'],
        copy_worker_sha256=binding['worker_sha256'], copy_worker_build_sha256=public.sha(args.worker_build.read_bytes()),
        summary=previous['summary'], rows=copy.deepcopy(previous['rows']), independent_rows=rows,
        independent_summary=dict(case_count=len(rows), both_commands_exact=len(rows),
            before_rejected=sum(bool(r['before_error']) for r in rows),
            before_different=sum(not r['before_error'] and not r['before_raw_exact'] for r in rows),
            before_smart_rejected=sum(bool(r['before_smart_error']) for r in rows)),
        retained_case_count=len(retained), candidate_public_replay_count=replays,
        original_zero_copy_rule=strength.original_rule()['zero_control_copy_branch_code_sha256'],
        production_source_and_core_changed_during_probe=False,
        dependencies_sha256={str(path.relative_to(public.ROOT)): public.sha(path.read_bytes()) for path in
            [Path(__file__), Path(strength.__file__), BEFORE, public.SOURCE.with_suffix('.h'), core, public.initial.HARNESS]},
        claims_not_made=previous['claims_not_made']+['Type3 checkout, partial ROI/downsample, native AE and all-ten completion remain unproven. Host memory/dimension envelopes do not prove native Windows hosting.'])
    args.report.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print('NOOP_PUBLIC_DONE', result['independent_summary'], 'REPLAYS', replays, flush=True)


if __name__ == '__main__': main()
