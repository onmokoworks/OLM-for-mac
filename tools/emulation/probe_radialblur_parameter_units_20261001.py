#!/usr/bin/env python3
"""Import-free parameter leaves and read-only exported builder observations.

Angle conversion runs only the original 0x87c9..0x87f4 instruction fragment;
it does not masquerade as a complete builder or an exported render. The latter
is measured separately with the fixture worker's Point API in percent units.
"""
import argparse
import json
import struct
import subprocess
import tempfile
from pathlib import Path

from PIL import Image
from unicorn.x86_const import UC_X86_REG_RDI, UC_X86_REG_RIP
from aex_loader import AexLoader
import probe_radialblur_public_aligned_20261001 as public


def leaf_observations():
    loader = AexLoader(str(public.initial.AEX), verbose=False, fast=False)
    definition = loader.bump_alloc(0x100)
    output = loader.bump_alloc(16)
    operand = loader.bump_alloc(0x100)
    loader.add_code_hook(0x1800087f4, lambda ld, _address, _size: ld.uc.emu_stop())
    constants = {hex(address): {'hex': loader.read_bytes(address, 8).hex(),
                               'f64': struct.unpack('<d', loader.read_bytes(address, 8))[0]}
                 for address in (0x1800212d8, 0x180025550)}
    values = sorted(set([-2147483648, -23592960, -5898240, -65536, -1, 0, 1, 65535,
                         65536, 65537, 2949120, 5898240, 23592960, 2147483647,
                         *[int(degrees*65536) for degrees in (-0.25, 0.25, 1.5, 37, 100)]]))
    rows = []
    for raw in values:
        loader.write_bytes(definition, bytes(0x100))
        loader.write_bytes(definition+0x38, struct.pack('<i', raw))
        results = {}
        for name, address in [('slider', 0x18001a260), ('angle', 0x18001a2a0),
                              ('noise_offset', 0x18001a2b0)]:
            loader.write_bytes(output, bytes([0xa5])*16)
            registers = loader.call_function(address, int_args=[definition, output], max_instructions=32)
            assert loader.uc.reg_read(UC_X86_REG_RIP) == 0x90000000
            assert not loader.import_log
            assert loader.read_bytes(output+4, 12) == bytes([0xa5])*12
            result = loader.read_bytes(output, 4)
            results[name] = {'hex': result.hex(), 'i32': struct.unpack('<i', result)[0],
                             'instructions': registers['instructions']}
            if name == 'noise_offset': results[name]['f32'] = struct.unpack('<f', result)[0]
        loader.write_bytes(operand, bytes([0x5a])*0x100)
        loader.write_bytes(operand+0x7c, struct.pack('<i', raw))
        loader.uc.reg_write(UC_X86_REG_RDI, operand)
        registers = loader.call_function(0x1800087c9, max_instructions=32)
        assert loader.uc.reg_read(UC_X86_REG_RIP) == 0x1800087f4
        assert not loader.import_log
        assert loader.read_bytes(operand, 0x7c) == bytes([0x5a])*0x7c
        assert loader.read_bytes(operand+0x80, 0x80) == bytes([0x5a])*0x80
        converted = struct.unpack('<i', loader.read_bytes(operand+0x7c, 4))[0]
        rows.append({'raw_fixed': raw, 'degrees_if_sdk_angle': raw/65536.0, 'leaves': results,
                     'angle_instruction_fragment_i32': converted,
                     'angle_fragment_instructions': registers['instructions']})
    return constants, rows


def public_builder_observations(worker, directory):
    directory.mkdir(parents=True, exist_ok=True)
    rows = []
    for family in (1, 2):
        case = next(c for c in public.specifications('getters')
                    if c['family'] == family and c['depth'] == 8 and c['state'] == 'edge')
        for parameter in case['parameters']:
            if parameter['slot'] == 13: parameter['value'] = 37
        native = public.native_case(case)
        image = Image.new('RGBA', tuple(case['geometry']))
        image.putdata([(r, g, b, a) for a, r, g, b in public.initial.pixels(*case['geometry'], case['pattern'])])
        ip = directory/f'input_{family}.png'; image.save(ip)
        # CLI lacks a typed Angle assignment. Omitted native defaults are observed
        # below; they must not be described as requested explicit zero values.
        assignments = [f"param_{p['slot']}@{p['slot']}="+
                       (','.join(map(str, p['value'])) if isinstance(p['value'], list) else str(p['value']))
                       for p in native['parameters'] if p['kind'] != 'a']
        command = [str(worker), 'render-trace-png', str(public.initial.AEX), str(ip),
                   str(directory/f'output_{family}.png'), '--watch', 'function=0x8690,arg=r9,size=272',
                   '--watch', 'function=0x1a2a0,arg=rdx,size=4',
                   '--watch', 'function=0x1a2b0,arg=rdx,size=4', *assignments]
        result = subprocess.run(command, capture_output=True, check=True)
        (directory/f'trace_{family}.json').write_bytes(result.stdout)
        data = json.loads(result.stdout)
        assert data['render_error'] == 0 and data['guards_intact']
        assert not data['unsupported_suite_calls'] and not data['dropped_unsupported_suite_calls']
        smart = next(t for t in data['execution_traces'] if t['selector'] == 'SMART_RENDER')
        assert not smart['truncated'] and not smart['dropped_memory_witnesses']
        witnesses = smart['memory_witnesses']
        builder = [w for w in witnesses if w['watch_id'] == 'watch-1']
        assert len(builder) == 1
        raw = bytes.fromhex(builder[0]['after']['hex'])
        fields = {name: {'offset': offset, 'format': fmt,
                         'value': struct.unpack_from('<'+fmt, raw, offset)[0]}
                  for name, offset, fmt in [('center_x', 0x28, 'd'), ('center_y', 0x30, 'd'),
                                           ('outer_edge', 0x6c, 'i'), ('inner_edge', 0x70, 'i'),
                                           ('angle', 0x7c, 'i'), ('quality_step', 0x80, 'f'),
                                           ('noise_offset', 0x100, 'f')]}
        assert fields['center_x']['value'] == 10 and fields['center_y']['value'] == 7
        assert fields['outer_edge']['value'] == 50 and fields['inner_edge']['value'] == 37
        leaves = {name: [w['after']['hex'] for w in witnesses if w['watch_id'] == wid]
                  for name, wid in [('angle_default_raw', 'watch-2'), ('noise_default_radians', 'watch-3')]}
        rows.append({'family': family, 'geometry': case['geometry'], 'fields': fields,
                     'default_leaves': leaves, 'parameter_values': data['parameter_values'],
                     'render_mode': data['render_mode'], 'input_png_sha256': public.sha(ip.read_bytes()),
                     'local_trace_sha256': public.sha(result.stdout), 'raw_output_sha256': data['raw_pixel_sha256'],
                     'guards_intact': True, 'unsupported_suite_calls': []})
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--worker', type=Path, required=True)
    parser.add_argument('--controlled-build', type=Path, required=True)
    parser.add_argument('--trace-dir', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    build = json.loads(args.controlled_build.read_text())
    assert public.sha(args.worker.read_bytes()) == build['controlled_worker_sha256']
    assert public.sha(public.initial.AEX.read_bytes()) == public.initial.AEX_SHA
    constants, leaves = leaf_observations()
    exported = public_builder_observations(args.worker, args.trace_dir)
    dependencies = [Path(__file__), Path(public.__file__), Path(public.initial.__file__),
                    public.ROOT/'tools/emulation/aex_loader.py',
                    public.ROOT/'disasm/OLMRadialBlur.aex.asm.txt',
                    public.ROOT/'decomp/OLMRadialBlur.aex.c.txt']
    report = {'schema': 'radialblur.parameter-units/1', 'aex_sha256': public.initial.AEX_SHA,
              'controlled_worker_sha256': build['controlled_worker_sha256'],
              'controlled_build_sha256': public.sha(args.controlled_build.read_bytes()),
              'constants': constants, 'leaf_rows': leaves, 'exported_builder_rows': exported,
              'dependencies_sha256': {str(p.relative_to(public.ROOT)): public.sha(p.read_bytes()) for p in dependencies},
              'claims_not_made': ['Angle fragment is not a complete builder/exported render',
                                 'Nonzero public Angle/Noise Offset were not traced by CLI',
                                 'Original binary consumes converted Angle integer directly in cos/sin; no degree correction inferred',
                                 'No native Windows UCRT/AE or complete compatibility proof']}
    args.report.write_text(json.dumps(report, sort_keys=True, indent=2)+'\n')
    print('RESULT', len(leaves), 'leaf rows', len(exported), 'exported builder rows', flush=True)


if __name__ == '__main__':
    main()
