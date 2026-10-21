#!/usr/bin/env python3
"""Instruction-bound PF32 matte/final trace; uses the original AEX unchanged.

The existing bounded Smart-worker host supplies a declared zero-edge record;
this is a leaf/worker mechanism witness, not a public parameter-builder claim.
Public retained cases are checked separately by run.py.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/emulation'))
import probe_olmcolorkey_pf16_full_worker_20260805 as host
from aex_loader import AexLoader
from aex_witness import leaf_check
from unicorn.x86_const import UC_X86_REG_RAX, UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_XMM0
import capstone
import pefile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--main', type=Path, default=ROOT.parent.parent)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    aex = args.main / 'plugins_2025/OLMColorKey.aex'
    assert hashlib.sha256(aex.read_bytes()).hexdigest() == host.AEX_SHA256
    host.ROOT = args.main  # only affects report path formatting
    host.PIXEL_FORMAT = 'PF32'
    host.WIDTH = host.HEIGHT = 1
    host.PADDING = 0
    traces = []

    class TracedLoader(AexLoader):
        def __init__(self, *a, **kw):
            super().__init__(*a, **kw)
            # Prove Win64's fifth argument with the import-free final callback.
            src, dst = self.host_alloc(16), self.host_alloc(16)
            self.write_bytes(src, struct.pack('<4f', 1, 0, 0, 0))
            self.write_bytes(dst, struct.pack('<4f', .25, 0, 0, 0))
            leaf_check(self, 0x180004170, [0, 0, 0, src, dst], expected_ret=0)
            assert self.read_bytes(dst, 4) == struct.pack('<f', .75)

            def capture(ld, pc, _size):
                if pc == 0x180004147:  # initial matte has been written
                    srcp = ld.uc.reg_read(UC_X86_REG_RCX)
                    dstp = ld.uc.reg_read(UC_X86_REG_RDX)
                    traces.append(dict(stage='matte', source=ld.read_bytes(srcp, 16).hex(),
                                       output=ld.read_bytes(dstp, 16).hex()))
                else:
                    dstp = ld.uc.reg_read(UC_X86_REG_RAX)
                    traces.append(dict(stage='before_subss' if pc == 0x18000417a else 'after_subss',
                        xmm0_alpha=struct.pack('<I', ld.uc.reg_read(UC_X86_REG_XMM0) & 0xffffffff).hex(),
                        matte_alpha=ld.read_bytes(dstp, 4).hex()))
            for pc in (0x180004147, 0x18000417a, 0x18000417e):
                self.add_code_hook(pc, capture)

    host.AexLoader = TracedLoader
    rows = []
    # Independent boundary words, matching/nonmatching RGB, count zero/nonzero.
    for word in (0, 0x80000000, 0x3f000000, 0xff812346, 0x7f812345, 0x7fc12345):
        for enabled in (False, True):
            for matched in (False, True):
                raw = struct.pack('<4I', word, 0 if matched else 0x3e000000, 0, 0)
                host.fixture = lambda *unused, raw=raw: (raw, 16)
                traces.clear()
                result = host.execute_case(aex, enabled)
                assert result['execution']['rax'] == '0x0'
                assert result['acceptance_gates']['direct_actual_pixel_callback_matches_worker_output']
                rows.append(dict(alpha_hex=raw[:4].hex(), count=int(enabled), black_rgb=matched,
                    trace=list(traces), output_hex=result['captures']['worker_first_pixel_hex'],
                    hits=result['execution']['hits']))
    pe = pefile.PE(str(aex))
    disasm = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    instructions = [dict(pc=hex(i.address), instruction=i.mnemonic+' '+i.op_str)
                    for start,size in ((0x4170,0x15),(0x4190,0x7d))
                    for i in disasm.disasm(pe.get_data(start,size),0x180000000+start)]
    report = dict(aex_sha256=host.AEX_SHA256, rows=rows, instructions=instructions,
                  boundary='Bounded original Smart worker; fixture parameter record; native callbacks')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print('Original Smart worker:', len(rows), 'boundary traces; leaf ABI verified')


if __name__ == '__main__':
    main()
