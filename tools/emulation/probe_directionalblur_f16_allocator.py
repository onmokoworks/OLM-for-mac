#!/usr/bin/env python3
"""F16: trace original PF8 renders and vary only noise-table allocator padding.

Padding variants are counterfactual host experiments, never reference pixels.
No AEX instruction, generated table entry, rotate or rowdriver is replaced.
"""
import argparse
import json
import math
import os
from pathlib import Path
import struct
import sys
import tempfile
import time
import types

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/fuzz'))
from adapters.olmdirectionalblur import Adapter
from core import sha
from aex_loader import AexLoader
from aex_witness import leaf_check
from PIL import Image
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from unicorn.x86_const import (UC_X86_REG_RAX, UC_X86_REG_RCX,
    UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9, UC_X86_REG_RSP)

TICKET = 'F16-dblur-generated-noise-fallback'
NEGATIVE = (167, 183, 222, 246)


def compare(a, b, stride=1):
    assert len(a) == len(b)
    offsets = [i for i in range(0, len(a), stride) if a[i:i+stride] != b[i:i+stride]]
    return {'different_units': len(offsets), 'unit_bytes': stride,
        'first': {'byte_offset': offsets[0], 'a': a[offsets[0]:offsets[0]+stride].hex(),
                  'b': b[offsets[0]:offsets[0]+stride].hex()} if offsets else None,
        'a_sha256': sha(a), 'b_sha256': sha(b)}


def run_fixture(case, directory, aex, padding):
    fixture_path = ROOT / 'tools/emulation/dblur_fullrender_host_fixture_20260711.py'
    body = fixture_path.read_text().replace(
        '(row_width // 2, 73), (row_width // 2, row_width - 72)',
        '(row_width // 2, 0), (row_width // 2, row_width - 1)')
    fixture = types.ModuleType('f16_fixture')
    fixture.__file__ = str(fixture_path)
    exec(compile(body, str(fixture_path), 'exec'), fixture.__dict__)
    trace = {'table_reads': 0, 'outside_reads': [], 'allocations': []}
    field = []

    class TracedLoader(AexLoader):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.generator = None
            self.generator_allocations = 0
            self.pad_next_payload = False
            ptrs = [self.host_alloc(16) for _ in range(4)]
            self.write_bytes(ptrs[0], bytes(16))
            for p in ptrs[1:]: self.write_bytes(p, b'\xa5' * 16)
            checked = leaf_check(self, 0x180001000, [0, 0, *ptrs, 0, 0, 0, 0, 1, 0])
            assert self.read_bytes(ptrs[1], 16) == bytes(16)
            assert all(self.read_bytes(p, 16) == bytes(4)+b'\xa5'*12 for p in ptrs[2:])
            trace['abi_leaf_instructions'] = checked['instructions']

            def entry(ld, address, size):
                self.generator = ld.uc.reg_read(UC_X86_REG_RCX)
                sp = ld.uc.reg_read(UC_X86_REG_RSP)
                trace['generator'] = {
                    'work_geometry': [ld.uc.reg_read(UC_X86_REG_R8), ld.uc.reg_read(UC_X86_REG_R9)],
                    'cell_size_bits': ld.read_bytes(sp+0x28, 4).hex(),
                    'offset_bits': ld.read_bytes(sp+0x30, 4).hex(),
                    'seed': fixture.u32(ld, sp+0x38)}

            def read(ld, address, size):
                base = ld.uc.reg_read(UC_X86_REG_RAX)
                index = ld.uc.reg_read(UC_X86_REG_RCX)
                if index >= 1 << 63: index -= 1 << 64
                offset = index*4 + (4 if address == 0x1800037f8 else 0)
                allocation = next(a for a in trace['allocations'] if a['pointer'] == base)
                assert allocation['size'] == 404
                trace['table_reads'] += 1
                if offset < 0 or offset+4 > allocation['size']:
                    trace['outside_reads'].append({'rva': hex(address-0x180000000),
                        'index': index, 'byte_offset': offset, 'allocation_size': allocation['size'],
                        'value_bits': ld.read_bytes(base+offset, 4).hex()})

            def rowdriver(ld, address, size):
                if field: return
                assert self.generator is not None
                ctx = self.generator
                w, h = fixture.u32(ld, ctx+0x10), fixture.u32(ld, ctx+0x14)
                field.append(ld.read_bytes(fixture.u64(ld, ctx+8), w*h*4))
                trace['field_dimensions'] = [w, h]
                # Bind the in-allocation table independently of padding contents.
                trace['table_sha256'] = sha(ld.read_bytes(fixture.u64(ld, ctx+0x28), 404))

            self.add_code_hook(0x1800034e0, entry)
            for address in (0x1800037f3, 0x1800037f8): self.add_code_hook(address, read)
            self.add_code_hook(0x1800038d0, rowdriver)

        def install_callback(self, label, handler):
            if label == 'PFHandle.new':
                original = handler
                def handler(ld, args):
                    if self.generator is not None:
                        self.generator_allocations += 1
                    self.pad_next_payload = padding is not None and self.generator_allocations == 2
                    handle = original(ld, args)
                    self.pad_next_payload = False
                    trace['allocations'].append({'pointer': fixture.u64(ld, handle),
                        'size': args[0] & 0xffffffff})
                    return handle
            return super().install_callback(label, handler)

        def bump_alloc(self, size, align=16):
            if self.pad_next_payload:
                assert size == 404
                p = super().bump_alloc(size+512, align)
                self.write_bytes(p, struct.pack('<f', padding)*64)
                self.write_bytes(p+256+size, struct.pack('<f', padding)*64)
                return p+256
            return super().bump_alloc(size, align)

    fixture.AexLoader = TracedLoader
    w, h = case['geometry']
    rgba = bytearray(len(case['pixels']))
    for i in range(0, len(rgba), 4):
        a, r, g, b = case['pixels'][i:i+4]
        rgba[i:i+4] = bytes((r,g,b,a))
    source, output, raw = directory/'source.png', directory/'fixture.json', directory/'output.raw'
    Image.frombytes('RGBA', (w,h), bytes(rgba)).save(source)
    names = {1:'angle',2:'brightness-gain',3:'size-variation',5:'front-strength',6:'front-alpha-fade',
        7:'front-sharp-tail',10:'back-strength',11:'back-alpha-fade',12:'back-sharp-tail',
        15:'noise-variation',16:'noise-type',18:'seed',19:'noise-offset',20:'thickness'}
    # These fixed controls are read as signed high words by the original builder.
    # Gain and Thickness are double sliders; preserve their fractional values.
    sys.argv = [str(fixture_path),'--aex',str(aex),'--source',str(source),'--output',str(output),
        '--host-output-raw',str(raw),'--actual-iterate-callbacks','--no-detour-rotate',
        '--no-detour-rowdriver','--downsample-num','1','--downsample-den','1',
        '--world-area','0','0',str(w),str(h),'--max-instructions','100000000']
    for param in case['parameters']:
        slot, value = param['slot'], param['value']
        if slot not in names: continue
        if slot not in (2,20): value = math.floor(value)
        sys.argv += ['--'+names[slot], str(value)]
    fixture.main()
    result = json.loads(output.read_text())
    assert result['status'] == 'ok', result.get('blocked')
    assert result['output']['complete'] and len(field) == 1
    trace['builder'] = result['execution']['param_context']
    trace['padding_float'] = padding
    trace['output_sha256'] = sha(raw.read_bytes())
    trace['field_sha256'] = sha(field[0])
    return trace, field[0], raw.read_bytes()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--indices', type=int, nargs='+', default=[102,145,*NEGATIVE])
    args = parser.parse_args()
    args.main, args.max_size, args.case_timeout = ROOT.parent.parent, 256, 20
    scratch = ROOT/'orchestra/state'/TICKET
    scratch.mkdir(parents=True, exist_ok=True)
    os.environ.update(TMPDIR=str(scratch), TMP=str(scratch), TEMP=str(scratch))
    tempfile.tempdir = str(scratch)
    adapter = Adapter(args)
    rows = []
    with tempfile.TemporaryDirectory(prefix='allocator_', dir=scratch) as tmp:
        tmp = Path(tmp)
        for index in args.indices:
            case = adapter.generate(1, index)
            assert case['depth'] == 8
            oracle, reference = adapter.oracle(case, tmp, time.monotonic()+60)
            assert oracle['status'] == 'ok'
            trials = [run_fixture(case, tmp, adapter.aex, padding)
                      for padding in (None,0.0,1.0)]
            rows.append({'index': index, 'geometry': case['geometry'], 'parameters': case['parameters'],
                'input_sha256': sha(case['pixels']), 'oracle': oracle,
                'trials': [t[0] for t in trials],
                'original_fixture_vs_session': compare(trials[0][2], reference),
                'padding_field_delta': compare(trials[1][1], trials[2][1], 4),
                'padding_output_delta': compare(trials[1][2], trials[2][2])})
            assert len({t[0]['table_sha256'] for t in trials}) == 1
            assert all(bool(t[0]['outside_reads']) == (index in NEGATIVE) for t in trials)
            assert rows[-1]['original_fixture_vs_session']['different_units'] == 0
            assert bool(rows[-1]['padding_field_delta']['different_units']) == (index in NEGATIVE)
            assert rows[-1]['padding_output_delta']['different_units'] == 0
            print('INDEX', index, 'OOB',len(trials[0][0]['outside_reads']),
                  'FIELD', rows[-1]['padding_field_delta']['different_units'],
                  'OUTPUT', rows[-1]['padding_output_delta']['different_units'], flush=True)
    loader = AexLoader(str(adapter.aex), verbose=False, fast=False)
    address = 0x1800037a4
    code = loader.read_bytes(address, 0x37fe-0x37a4)
    instructions = [{'rva': hex(i.address-0x180000000), 'mnemonic': i.mnemonic,
                     'operands': i.op_str}
                    for i in Cs(CS_ARCH_X86, CS_MODE_64).disasm(code, address)]
    report = {'schema': 'directionalblur.f16-allocator/1', 'cases': rows,
        'table_read_instructions': instructions, 'table_read_code_sha256': sha(code),
        'aex_sha256': sha(adapter.aex.read_bytes()), 'worker_sha256': sha(args.worker.read_bytes()),
        'probe_sha256': sha(Path(__file__).read_bytes()),
        'adapter_sha256': sha((ROOT/'tools/fuzz/adapters/olmdirectionalblur.py').read_bytes()),
        'generator_sha256': sha((ROOT/'tools/fuzz/adapters/public.py').read_bytes()),
        'fixture_sha256': sha((ROOT/'tools/emulation/dblur_fullrender_host_fixture_20260711.py').read_bytes()),
        'loader_sha256': sha((ROOT/'tools/emulation/aex_loader.py').read_bytes()),
        'scope': 'Original builder, PF8 worker and callbacks, rotate, noise generator and rowdriver; host handle/iterate callbacks and host libm. Padding variants are diagnostics, not oracle replacements.'}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')


if __name__ == '__main__': main()
