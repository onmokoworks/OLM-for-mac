#!/usr/bin/env python3
"""Reproduce F15's Classic/Smart reference split; production stays untouched."""
from __future__ import annotations
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/fuzz'))
from adapters.olmblur import Adapter
from core import load_corpus, sha


def trace_classic(case, main):
    # Reuse the retained guarded public-selector fixture, substituting only the
    # corpus dimensions/pixels and installing a read-only worker-entry hook.
    import test_olmblur_classic_public_entry_closure_20260812 as fixture
    from unicorn import UC_HOOK_CODE
    from unicorn.x86_const import UC_X86_REG_R9, UC_X86_REG_R8
    original_loader = fixture.AexLoader
    observed = []

    class TracedLoader(original_loader):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            def entry(uc, address, size, user):
                ctx = uc.reg_read(UC_X86_REG_R9)
                world = uc.reg_read(UC_X86_REG_R8)
                data = struct.unpack('<Q', self.read_bytes(world+0x18, 8))[0]
                stride = struct.unpack('<I', self.read_bytes(world+0x20, 4))[0]
                active = case['geometry'][0]*case['depth']//2
                raw = b''.join(self.read_bytes(data+y*stride, active)
                               for y in range(case['geometry'][1]))
                amount, smoothness, repeat = struct.unpack('<ffi', self.read_bytes(ctx+0x20, 12))
                observed.append(dict(worker_entry=hex(address), amount=amount,
                                     smoothness=smoothness, repeat=repeat,
                                     copied_output_sha256=sha(raw)))
            for address in (0x180003710, 0x180002280):
                self.uc.hook_add(UC_HOOK_CODE, entry, begin=address, end=address)

    prior = (fixture.AEX, fixture.WIDTH, fixture.HEIGHT, fixture.AexLoader,
             fixture.fixture.source_bytes)
    try:
        fixture.AEX = main/'plugins_2025/OLMBlur.aex'
        fixture.WIDTH, fixture.HEIGHT = case['geometry']
        fixture.AexLoader = TracedLoader
        fixture.fixture.source_bytes = lambda depth: case['pixels']
        result = fixture.actual_classic(case['depth'], 1, 0)
    finally:
        (fixture.AEX, fixture.WIDTH, fixture.HEIGHT, fixture.AexLoader,
         fixture.fixture.source_bytes) = prior
    assert len(observed) == 1 and observed[0]['amount'] == 0
    assert observed[0]['copied_output_sha256'] == sha(case['pixels'])
    return dict(public_export=result, worker_entries=observed)


def first_difference(a, b):
    return next((dict(byte=i, reference=x, candidate=y)
                 for i, (x, y) in enumerate(zip(a, b)) if x != y), None)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--scratch', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--main', type=Path, default=ROOT.parent.parent)
    p.add_argument('--worker', type=Path, default=Path.home()/'.cache/olm-emu/radial_frozen_reference_bd878da/target/release/aex-guest-worker')
    args = p.parse_args()
    args.scratch = args.scratch.resolve()
    assert args.scratch.is_relative_to(ROOT/'orchestra/state/F15-olmblur-small-fixture-promotion')
    args.scratch.mkdir(parents=True, exist_ok=True)
    os.environ.update(TMPDIR=str(args.scratch), TMP=str(args.scratch), TEMP=str(args.scratch))
    tempfile.tempdir = str(args.scratch)
    adapter = Adapter(argparse.Namespace(max_size=256, case_timeout=30, main=args.main, worker=args.worker))
    rows = []
    with tempfile.TemporaryDirectory(prefix='routes_', dir=args.scratch) as td:
        work = Path(td)
        provenance = adapter.prepare(work, time.monotonic()+120)
        for path in sorted((ROOT/'tests/fuzz_corpus/olmblur').glob('*.json')):
            case, saved = load_corpus(path, adapter)
            if saved['result']['routes']['classic']['status'] != 'mismatch':
                continue
            assert all(p['value'] == v for p, v in zip(case['parameters'], (5., 100., 2, 1, 0)))
            outputs = {}
            for route, oracle_path in (('smart', 'smartfx'), ('classic', 'classic')):
                adapter.oracle_route, adapter.oracle_path = route, oracle_path
                status, raw = adapter.oracle(case, work, time.monotonic()+60)
                assert status['status'] == 'ok', status
                outputs[route] = raw
            status, candidate, _ = adapter.candidate(case, work, 'classic', time.monotonic()+60)
            assert status['status'] == 'ok', status
            assert candidate == outputs['classic'] == case['pixels']
            assert candidate != outputs['smart']
            assert sha(outputs['smart']) == saved['result']['oracle']['raw_sha256']
            assert sha(candidate) == saved['result']['routes']['classic']['raw_sha256']
            trace = trace_classic(case, args.main)
            rows.append(dict(corpus=path.name, index=case['index'], depth=case['depth'],
                geometry=case['geometry'], input_sha256=sha(case['pixels']),
                aex_classic_sha256=sha(outputs['classic']), aex_smart_sha256=sha(outputs['smart']),
                mac_classic_sha256=sha(candidate), matched_classic=True,
                smart_diff_bytes=sum(a != b for a,b in zip(outputs['smart'], candidate)),
                smart_first_difference=first_difference(outputs['smart'],candidate), trace=trace))
    assert len(rows) == 13
    provenance['audit_oracle_routes'] = ['classic', 'smartfx']
    provenance['audit_stage_support'] = 'Direct Unicorn Classic worker-entry context and post-copy output'
    report = dict(status='PASS_COMPARATOR_ROUTE_SPLIT', provenance=provenance,
        audit_sha256=sha(Path(__file__).read_bytes()),
        trace_dependencies_sha256={name:sha((ROOT/'tools/emulation'/name).read_bytes()) for name in
            ('aex_loader.py', 'test_olmblur_fullentry.py',
             'test_olmblur_classic_public_entry_closure_20260812.py')},
        static_sources={str(path):sha(path.read_bytes()) for path in
                        (args.main/'decomp/OLMBlur.aex.c.txt', args.main/'disasm/OLMBlur.aex.asm.txt')},
        summary=dict(cases=len(rows), depths=dict(Counter(str(r['depth']) for r in rows)),
                     classic_exact=len(rows), smart_comparator_mismatch=len(rows)), rows=rows)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    print(report['status'], report['summary'])


if __name__ == '__main__':
    main()
