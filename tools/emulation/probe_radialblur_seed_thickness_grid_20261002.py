#!/usr/bin/env python3
"""Read initialized original lattices; verify reciprocal dimensions and MT words."""
import argparse
import json
from pathlib import Path
import struct
import subprocess
import pefile

from PIL import Image
import probe_radialblur_seed_thickness_20261002 as profiles
import probe_radialblur_noise_offset_field_20261001 as field

public = profiles.public
DECLARATIONS=public.ROOT/'reports/radialblur_size_range_public_20261002.json'


def original_rule():
    pe=pefile.PE(str(public.initial.AEX))
    return dict(code_sha256=public.sha(pe.get_data(0x93bb,0x9429-0x93bb)),
                one_f32_le_hex=pe.get_data(0x212d4,4).hex(),
                margin_f32_le_hex=pe.get_data(0x216cc,4).hex(),
                rule='93de DIVSS computes FLOAT32 1/Thickness once; 9409/940d MULSS, 9411/9416 ADDSS 3, 941b/941f CVTTSS2SI construct dimensions.')


def cases():
    rows = []
    boundary = [([17, 15], 3.4), ([17, 15], 1.7000000476837158),
                ([17, 15], 1.888888955116272), ([23, 13], 1.9166667461395264),
                ([23, 13], 1.769230842590332), ([31, 7], 3.4444446563720703),
                ([7, 5], 7.000000953674316), ([7, 5], 3.500000476837158),
                ([17, 15], 1), ([17, 15], 100)]
    for family in [1, 2]:
        for index, (geometry, thickness) in enumerate(boundary):
            rows.append(field.case_for(family, geometry, 8, 1 if index % 2 else 2,
                                      [1, 53, 997, 1000][index % 4], thickness,
                                      [0, 65536, 1966080, 5898240][index % 4]))
    return rows


def grid_maps(worker, directory, core):
    directory.mkdir(parents=True, exist_ok=False)
    private_core = directory/'dblur_noise.h'
    private_core.write_text(core)
    harness = directory/'plane.cpp'
    harness.write_text(field.HARNESS.read_text().replace('../../core/dblur_noise.h', str(private_core)))
    binaries = {}
    for name in ['o2', 'san', 'default']:
        sanitize = name == 'san'
        binary = directory/name
        command = ['clang++', '-std=c++17', '-O1' if sanitize else '-O2',
                   '-fno-fast-math', '-ffp-contract=off', str(harness), '-o', str(binary)]
        if name == 'default': command = [c for c in command if c not in ['-fno-fast-math', '-ffp-contract=off']]
        if sanitize: command += ['-fsanitize=address,undefined', '-fno-omit-frame-pointer']
        subprocess.run(command, check=True)
        binaries[name] = binary
    rows = []
    for index, case in enumerate(cases()):
        geometry = case['geometry']
        params = {p['slot']: p['value'] for p in case['parameters']}
        thickness = field.f32(params[29])
        dimensions = field.plane_dimensions(geometry, thickness)
        division_dimensions = [int(field.f32(field.f32(v/thickness)+3.0)) for v in geometry]
        size = 4*dimensions[0]*dimensions[1]
        assert size <= 4096
        image = Image.new('RGBA', geometry)
        image.putdata([(r, g, b, a) for a, r, g, b in public.initial.pixels(*geometry, 'opaque')])
        image_path = directory/'input.png'
        image.save(image_path)
        native = public.native_case(case)
        assignments = [f"param_{p['slot']}@{p['slot']}"+(':angle' if p['kind'] == 'a' else '')+'='+
                       (','.join(map(str, p['value'])) if isinstance(p['value'], list) else str(p['value']))
                       for p in native['parameters']]
        run = subprocess.run([str(worker), 'render-trace-png', str(public.initial.AEX),
            str(image_path), str(directory/'output.png'),
            '--watch', 'function=0x1a2b0,arg=rdx,size=4',
            '--watch', 'function=0x9680,arg=rcx,size=72,occurrence=1',
            '--watch', f'function=0x9680,arg=rcx,deref=8,size={size},occurrence=1',
            *assignments], capture_output=True, check=True)
        trace = json.loads(run.stdout)
        assert not trace['render_error'] and trace['guards_intact']
        assert not trace['unsupported_suite_calls'] and not trace['dropped_unsupported_suite_calls']
        smart = next(t for t in trace['execution_traces'] if t['selector'] == 'SMART_RENDER')
        assert not smart['truncated'] and not smart['dropped_memory_witnesses']
        watches = {wid: [w for w in smart['memory_witnesses'] if w['watch_id'] == wid]
                   for wid in ['watch-1', 'watch-2', 'watch-3']}
        assert all(len(w) == 1 for w in watches.values())
        phase = bytes.fromhex(watches['watch-1'][0]['after']['hex'])
        context = bytes.fromhex(watches['watch-2'][0]['before']['hex'])
        plane_watch = watches['watch-3'][0]
        assert plane_watch['before']['status'] == 'captured'
        assert plane_watch['before']['hex'] == plane_watch['after']['hex']
        plane = bytes.fromhex(plane_watch['before']['hex'])
        assert list(struct.unpack_from('<2i', context, 0x10)) == dimensions
        assert list(struct.unpack_from('<2i', context, 0x18)) == geometry
        assert struct.unpack_from('<i', context, 0x20)[0] == 100
        thickness_bits = struct.unpack_from('<I', context, 0x40)[0]
        assert struct.pack('<I', thickness_bits) == struct.pack('<f', thickness)
        phase_bits = struct.unpack('<I', phase)[0]
        for binary in binaries.values():
            actual = subprocess.run([str(binary), *map(str, geometry), f'{thickness_bits:08x}',
                f'{phase_bits:08x}', str(params[27])], capture_output=True, check=True, env=profiles.ENV)
            assert list(map(int, actual.stderr.split())) == dimensions
            assert actual.stdout == plane, index
        (directory/f'trace_{index}.json').write_bytes(run.stdout)
        (directory/f'plane_{index}.raw').write_bytes(plane)
        rows.append(dict(case=case, thickness_f32_word=f'{thickness_bits:08x}',
            phase_f32_word=f'{phase_bits:08x}', native_dimensions=dimensions,
            direct_division_dimensions=division_dimensions,
            division_changes_dimensions=dimensions != division_dimensions,
            plane_word_count=size//4, native_plane_sha256=public.sha(plane),
            plane_first_four_f32_le_hex=plane[:16].hex(), initialized_plane_exact=True,
            sampler_leaves_plane_unchanged=True, trace_sha256=public.sha(run.stdout)))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--worker', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--report', type=Path, required=True)
    args = ap.parse_args()
    before = json.loads(profiles.BEFORE.read_text())
    assert public.sha(args.worker.read_bytes()) == before['window_worker_sha256']
    assert public.sha(public.initial.AEX.read_bytes()) == before['aex_sha256']
    core = profiles.candidate_core(profiles.before_core())
    rows = grid_maps(args.worker, args.output, core)
    report = dict(schema='radialblur.seed-thickness-grid/1', rows=rows, case_count=len(rows),
        plane_word_count=sum(r['plane_word_count'] for r in rows),
        division_dimension_counterexample_count=sum(r['division_changes_dimensions'] for r in rows),
        core_sha256=public.sha(core.encode()), worker_sha256=before['window_worker_sha256'],
        aex_sha256=before['aex_sha256'], o2_and_strict_sanitizer_exact=True, default_compiler_contract_exact=True,
        native_dimension_rule=original_rule(),
        native_parameter_declarations=[p for p in json.loads(DECLARATIONS.read_text())['native_parameter_declarations'] if p['slot'] in [27,29]],
        dependencies_sha256={str(p.relative_to(public.ROOT)):public.sha(p.read_bytes())
            for p in [Path(__file__), field.HARNESS, Path(field.__file__), DECLARATIONS]},
        claims_not_made=['Initialized original grids and reciprocal rule do not close arbitrary inputs/settings or native Windows UCRT/ISA/AE.',
                        'Original binaries, private contexts, full planes and traces remain private.'])
    args.report.write_text(json.dumps(report, sort_keys=True, indent=2)+'\n')
    print('SEED_THICKNESS_GRID', len(rows), 'WORDS', report['plane_word_count'],
          'DIVISION_COUNTEREXAMPLES', report['division_dimension_counterexample_count'], flush=True)


if __name__ == '__main__': main()
