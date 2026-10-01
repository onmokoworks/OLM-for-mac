#!/usr/bin/env python3
"""Connect admitted size/noise Rotation worlds to the original two-stage path.

Original reference code, callbacks and workers stay unchanged. Read only real
legacy polar/normalized/span planes; the legacy path has no accum/max planes.
Keep raw worlds and all intermediate binary data in the private output folder.
"""
import argparse
import copy
import json
import os
from pathlib import Path
import struct
import subprocess

import probe_radialblur_rotation_neutral_20261001 as neutral
public = neutral.public
fields = neutral.fields
writer = neutral.writer
BEFORE = public.ROOT/'reports/radialblur_rotation_fade_public_20261001.json'
BEFORE_REVISION = '7a7f53feb6d064a550124971e4920fb8d846efe4'
OLD = 'const bool use_generic_two_stage = use_generic_baseline;'
NEW = 'const bool use_generic_two_stage = use_generic_baseline || use_generic_size_noise;'


def before_source():
    source = subprocess.check_output(['git', 'show', BEFORE_REVISION+':mac/OLMRadialBlur/OLMRadialBlur.cpp'],
                                     cwd=public.ROOT).decode()
    assert public.sha(source.encode()) == json.loads(BEFORE.read_text())['source_sha256']
    return source


def connection_source(source):
    assert source.count(OLD) == 1
    return source.replace(OLD, NEW)


def candidate_source(source):
    source = connection_source(source)
    start = source.index('static bool BuildRadialSizeFactorPlaneAEX(')
    end = source.index('static FloatImage', start)
    part = source[start:end]
    comment = """// NaN is accepted by the AEX's COMISS/SETC predicate, but it is not
			// part of this bounded admission.  The portable label pass below uses
			// explicit x/y bounds and therefore does not inherit the AEX run
			// scanner's right-edge lookahead quirk."""
    assert part.count(comment) == 1
    part = part.replace(comment, """// NaN is accepted by the AEX's COMISS/SETC predicate, but it is not
			// part of this bounded admission.  Label visible cells with four-neighbor
			// connectivity, then reproduce the run scanner's right-edge count/write.""")
    marker = '\tstd::sort(component_areas->begin(), component_areas->end());'
    assert part.count(marker) == 1
    update = """	// AEX 8ad4 reads x == width before checking the row boundary.  An
	// occupied next-row first cell extends this run by one, without adding a
	// horizontal connection across rows.  The source mask has a zero guard.
	for (size_t edge = (size_t)w - 1; edge + 1 < count; edge += (size_t)w) {
		if (!mask[edge] || !mask[edge + 1]) continue;
		A_long &area = areas[labels[edge]];
		if (area == std::numeric_limits<A_long>::max()) return false;
		++area;
	}
	component_areas->clear();
	maximum_area = 0;
	for (size_t label = 1; label < areas.size(); ++label) {
		component_areas->push_back(areas[label]);
		maximum_area = std::max(maximum_area, areas[label]);
	}
"""
    part = part.replace(marker, update+marker)
    old_label = '\t\tconst uint32_t label = labels[cell];'
    assert part.count(old_label) == 1
    new_label = """		uint32_t label = labels[cell];
		// AEX 8dd0 also writes the extended endpoint into next-row x == 0.
		// Components materialize in first-run order; the later component wins.
		if (cell > 0 && cell % (size_t)w == 0 && mask[cell - 1] && mask[cell]) {
			label = std::max(label, labels[cell - 1]);
		}"""
    part = part.replace(old_label, new_label)
    return source[:start]+part+source[end:]


def cases(capture):
    return [row for row in capture['rows'] if row['matrix'] == 'topology' and row['family'] == 2 and row['depth'] == 32
            and row['state'] == 'size100_noise' and row['results']['classic']['error'] == 0
            and not row['results']['classic']['raw_exact']]


def natural(worker, temp, capture, source, candidate):
    harness = public.initial.HARNESS; hp = temp/'planes.cpp'; hp.write_text(fields.plane_harness())
    try:
        public.initial.HARNESS = hp
        binaries = {'before': public.build(temp/'before_planes', neutral.passive_legacy_source(source)),
                    'candidate': public.build(temp/'candidate_planes', candidate)}
    finally:
        public.initial.HARNESS = harness
    results = []
    selected = cases(capture); assert len(selected) == 12
    for index, case in enumerate(selected):
        directory = temp/f'natural_{index}'; directory.mkdir()
        native, trace = neutral.trace(worker, directory, case)
        comparisons, raw_hashes, dimensions = {}, {}, {}
        for name, binary in binaries.items():
            plane_dir = directory/name; plane_dir.mkdir()
            error, raw, _ = public.mac_render(binary, directory, case, 'classic', dict(os.environ, ROTATION_PLANES_DIRECTORY=str(plane_dir)))
            assert not error; raw_hashes[name] = public.sha(raw)
            if name == 'before': assert raw_hashes[name] == case['results']['classic']['raw_sha256']
            dimensions[name] = list(struct.unpack('<2i', (plane_dir/'dimensions.i32').read_bytes()))
            # The passive copy does not invent an absent legacy accumulation
            # plane or treat a never-used initialized scalar array as a worker.
            names = ['polar', 'normalized', 'span'] if name == 'before' else list(native)
            comparisons[name] = {nm: fields.compare_words(native[nm], (plane_dir/f'{nm}.f32').read_bytes()[:len(native[nm])]) for nm in names}
        assert raw_hashes['candidate'] == case['reference_raw_sha256']
        assert all(value['different_words'] == 0 for value in comparisons['candidate'].values())
        results.append({'case': case, 'trace': trace, 'mac_dimensions': dimensions, 'field_comparisons': comparisons,
                        'mac_raw_sha256': raw_hashes, 'candidate_raw_exact': True,
                        'legacy_comparison_planes': ['polar', 'normalized', 'span']})
        print('SIZE_NOISE_NATURAL', case['geometry'], case['pattern'],
              {nm: value['different_words'] for nm, value in comparisons['before'].items()}, flush=True)
    return results


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--worker', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True); ap.add_argument('--report', type=Path, required=True)
    args = ap.parse_args(); args.output.mkdir(exist_ok=False, parents=True)
    capture = json.loads(BEFORE.read_text()); source = before_source(); candidate = candidate_source(source)
    start_source_sha = public.sha(public.SOURCE.read_bytes())
    build = json.loads((public.ROOT/'reports/radialblur_readonly_windows_reference_build_20261001.json').read_text())
    assert public.sha(args.worker.read_bytes()) == build['worker_sha256']
    assert public.sha(public.initial.AEX.read_bytes()) == capture['aex_sha256']
    witnesses = natural(args.worker, args.output, capture, source, candidate)
    binaries = {'o2': public.build(args.output/'o2', candidate), 'san': public.build(args.output/'san', candidate, True)}
    env = dict(os.environ, ASAN_OPTIONS='detect_leaks=0:halt_on_error=1', UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
    rows = []
    for index, case in enumerate(capture['rows']):
        results = {}
        for name, binary in binaries.items():
            for command in ['classic', 'smart']:
                error, raw, metadata = public.mac_render(binary, args.output, case, command, env)
                old = case['results'][command]; assert error == old['error'] and metadata == old['metadata']
                result = {'error': error, 'raw_sha256': public.sha(raw) if not error else None,
                          'raw_exact': not error and public.sha(raw) == case['reference_raw_sha256'], 'metadata': metadata,
                          'before_raw_exact': old['raw_exact'], 'before_raw_unchanged': (public.sha(raw) if not error else None) == old['raw_sha256']}
                if name == 'o2': results[command] = result
                else: assert result == results[command]
        row = {key: copy.deepcopy(case[key]) for key in ['family', 'geometry', 'depth', 'pattern', 'state', 'parameters', 'group', 'matrix', 'row_index',
                                                        'input_sha256', 'reference_raw_sha256', 'parent_raw_sha256']}
        row['results'] = results; rows.append(row)
        if (index+1) % 128 == 0: print('SIZE_NOISE_PUBLIC', index+1, flush=True)
    assert public.sha(public.SOURCE.read_bytes()) == start_source_sha
    summary = writer.summarize(rows); assert summary['lost_exact'] == 0
    report = {'schema': 'radialblur.rotation-size-noise-public/1', 'before_revision': BEFORE_REVISION,
              'source_before_sha256': capture['source_sha256'], 'source_sha256': public.sha(candidate.encode()),
              'header_sha256': capture['header_sha256'], 'aex_sha256': capture['aex_sha256'],
              'controlled_worker_sha256': capture['controlled_worker_sha256'], 'window_worker_sha256': build['worker_sha256'],
              'probe_start_source_sha256': start_source_sha, 'production_source_changed_during_probe': False,
              'summary': summary, 'rows': rows, 'natural_witnesses': witnesses, 'public_replay_count': len(rows)*4,
              'natural_owned_field_words': sum(value['word_count'] for witness in witnesses for value in witness['field_comparisons']['candidate'].values()),
              'matrix_summaries': {m: writer.summarize([row for row in rows if row['matrix'] == m]) for m in capture['matrix_summaries']},
              'dependencies_sha256': {str(p.relative_to(public.ROOT)): public.sha(p.read_bytes()) for p in
                                      [Path(__file__), Path(neutral.__file__), Path(fields.__file__), BEFORE, public.SOURCE.with_suffix('.h'), public.initial.HARNESS]},
              'claims_not_made': ['Only real polar/normalized/span legacy planes are compared; legacy has no accum/max workers.',
                                 'The extra Mac radius row is excluded from native-owned field comparisons.',
                                 'Three scalar fade words and native Windows ISA/RCPPS/general UCRT remain open.',
                                 'Finite topology/depth/settings do not prove arbitrary inputs, Size25, Zoom, Quality, native AE/UI/save/ROI/downsample or all-ten completion.']}
    args.report.write_text(json.dumps(report, sort_keys=True, indent=2)+'\n')
    print('SIZE_NOISE_DONE', summary, report['natural_owned_field_words'], flush=True)


if __name__ == '__main__':
    main()
