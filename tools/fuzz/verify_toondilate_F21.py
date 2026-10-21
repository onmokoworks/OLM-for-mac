#!/usr/bin/env python3
"""F21 PF32 seed regression: real AEX stages, public routes, corpus and sanitizers.

Use MAIN's emulation venv. All builds/temp files stay under --scratch.
Historical corpus observations are retained; this report records before/after.
"""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import struct
import tempfile
import time
from types import SimpleNamespace

from triage_toondilate_T13 import DiagnosticAdapter, original_stage
from adapters.olmtoondilate import SOURCE
from adapters.public import ROOT, replace_once
from core import command, load_corpus, raw_diff, sha
from aex_loader import AexLoader
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

FIXED = '''\tstatic bool opaque(const PF_PixelFloat &p) {
\t\t// AEX 0x1801a698e: UCOMISS / CMOVZ selects a seed for equality or
\t\t// unordered (NaN), but not finite HDR alpha or either infinity.
\t\treturn p.alpha == 1.0f || std::isnan(p.alpha);
\t}'''
OLD = '\tstatic bool opaque(const PF_PixelFloat &p) { return p.alpha >= 1.0f; }'


def witnesses(adapter):
    # Pack integer words directly: Python float conversion would quiet sNaNs.
    bits = [0x3f7fffff, 0x3f800000, 0x3f800001, 0x40000000,
            0x7f7fffff, 0xff7fffff, 0x7f800000, 0xff800000,
            0x7fc12345, 0xffc12345, 0x7f812346, 0xff812346,
            0, 0x80000000, 1, 0x80000001]
    for alpha in bits:
        for geometry in ([1, 2], [2, 1]):
            for reverse in (False, True):
                case = adapter.generate(21, 0)
                pixels = [struct.pack('<4I', alpha, 0x3e000001, 0x3e800002, 0x3f000003),
                          struct.pack('<4I', 0x3f000000, 0x3e400004, 0x3ec00005, 0x3f400006)]
                if reverse:
                    pixels.reverse()
                case.update(geometry=geometry, depth=32, profile='F21-boundary',
                            pixels=b''.join(pixels), input_padding=3, output_padding=5,
                            parameters=[dict(slot=1, kind='s', value=2.0)])
                yield f'{alpha:08x}-{geometry[0]}x{geometry[1]}-{int(reverse)}', case


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--scratch', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    args = p.parse_args()
    scratch = args.scratch.resolve()
    assert scratch.is_relative_to(ROOT/'orchestra/state')
    scratch.mkdir(parents=True, exist_ok=True)
    os.environ.update(TMPDIR=str(scratch), TMP=str(scratch), TEMP=str(scratch), PYTHONDONTWRITEBYTECODE='1')
    tempfile.tempdir = str(scratch)
    options = SimpleNamespace(max_size=256, case_timeout=15, main=ROOT.parent.parent,
        worker=Path('/Users/onmk/.cache/olm-emu/radial_frozen_reference_bd878da/target/release/aex-guest-worker'))
    deadline = time.monotonic() + 1200
    source = SOURCE.read_text()
    before_source = replace_once(source, FIXED, OLD)
    stage_source = replace_once(source, '\tif (!has_seed) return PF_Err_NONE;', '''
    if (const char *path = std::getenv("OLM_TOON_STAGE_TRACE")) {
        if (FILE *f = std::fopen(path, "w")) {
            for (uint32_t d : dist) std::fprintf(f, "%u\\n", d);
            std::fclose(f);
        }
    }
\tif (!has_seed) return PF_Err_NONE;''')
    report = dict(schema='olm-toondilate-F21/1', before_source_sha256=sha(before_source.encode()),
                  after_source_sha256=sha(source.encode()), corpus=[], witnesses=[], campaigns={})
    with tempfile.TemporaryDirectory(dir=scratch, prefix='F21_') as raw:
        work = Path(raw)
        adapters = {}
        report['builds'] = {}
        for name, text, sanitize in [('before', before_source, False), ('after', None, False),
                                     ('stage', stage_source, False), ('sanitized', None, True)]:
            folder = work/name
            folder.mkdir()
            adapter = DiagnosticAdapter(options, text, sanitize)
            report['builds'][name] = adapter.prepare(folder, deadline)
            adapters[name] = adapter
        after = adapters['after']
        loader = AexLoader(str(after.aex), verbose=False, fast=True)
        code = loader.read_bytes(0x1801a698e, 6)
        report['seed_instructions'] = [dict(address=hex(i.address), mnemonic=i.mnemonic, operands=i.op_str)
                                       for i in Cs(CS_ARCH_X86, CS_MODE_64).disasm(code, 0x1801a698e)]
        assert [(i['mnemonic'], i['operands']) for i in report['seed_instructions']] == [
            ('ucomiss', 'xmm0, xmm6'), ('cmove', 'edx, ebx')]
        report['seed_instruction_bytes'] = code.hex()

        def candidate(name, case, folder, route='smart', trace=False):
            adapter = adapters[name]
            env = dict(adapter.env, ASAN_OPTIONS='detect_leaks=0:abort_on_error=1',
                       UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
            if trace:
                env['OLM_TOON_STAGE_TRACE'] = str(folder/'mask.txt')
            argv, data = adapter.candidate_command(case, folder, route)
            status, output, err = command(argv, data=data, timeout=15, deadline=deadline, env=env)
            assert status['status'] == 'ok', (name, status, err.decode(errors='replace'))
            assert b'Sanitizer' not in err and b'runtime error:' not in err, err
            return output

        def compare(name, case, saved=None, stage=False):
            with tempfile.TemporaryDirectory(dir=work) as d:
                folder = Path(d)
                oracle, expected = after.oracle(case, folder, deadline, 'smart')
                assert oracle['status'] == 'ok', oracle
                before = candidate('before', case, folder)
                actual = candidate('after', case, folder)
                assert actual == expected, (name, raw_diff(expected, actual, case['depth']))
                assert candidate('sanitized', case, folder) == actual
                row = dict(name=name, input_sha256=sha(case['pixels']), geometry=case['geometry'],
                           before='exact' if before == expected else 'mismatch', after='exact',
                           before_sha256=sha(before), after_sha256=sha(actual), oracle_sha256=sha(expected),
                           before_diff=raw_diff(expected, before, case['depth']) if before != expected else None)
                if saved:
                    assert sha(expected) == saved['result']['oracles']['smart']['raw_sha256']
                    assert sha(before) == saved['result']['routes']['smart']['raw_sha256']
                    row['saved_before_verified'] = True
                # Classic is a no-write diagnostic command, not a numeric image.
                classic_oracle, classic_raw = after.oracle(case, folder, deadline, 'classic')
                assert classic_oracle['status'] == 'ok' and classic_raw == bytes(len(case['pixels']))
                for build in ('before', 'after', 'sanitized'):
                    assert candidate(build, case, folder, 'classic') == bytes([0xee])*len(case['pixels'])
                row['classic_before_after'] = 'no_write'
                if stage:
                    original, worker_output, control = original_stage(case, after.aex)
                    assert worker_output == expected
                    assert candidate('stage', case, folder, trace=True) == actual
                    mac_mask = list(map(int, (folder/'mask.txt').read_text().splitlines()))
                    assert mac_mask == [x['distance'] for x in original], (name, original, mac_mask)
                    row.update(original_mask=original, mac_mask=mac_mask, worker_control=control)
                return row

        for corpus in ('olmtoondilate', 'olmtoondilate_T13'):
            paths = sorted((ROOT/'tests/fuzz_corpus'/corpus).glob('*.json'))
            def replay(path):
                case, saved = load_corpus(path, after)
                return compare(str(path.relative_to(ROOT)), case, saved, corpus.endswith('T13'))
            with ThreadPoolExecutor(max_workers=2) as pool:
                rows = list(pool.map(replay, paths))
            report['corpus'].extend(rows)
            print(corpus, dict(Counter((r['before'],r['after']) for r in rows)), flush=True)
        for name, case in witnesses(after):
            row = compare(name, case, stage=True)
            row['input_hex'] = case['pixels'].hex()
            row['parameters'] = case['parameters']
            report['witnesses'].append(row)
        print('boundary witnesses', len(report['witnesses']), 'exact', flush=True)

        # Recheck both fresh campaigns and all 1,200 public renders under sanitizers.
        for seed in (1, 2):
            baseline = ROOT/f'reports/fuzz/olmtoondilate_F21_before_seed{seed}.json'
            old = json.loads(baseline.read_text())
            new = json.loads((scratch/f'after-seed{seed}.json').read_text())
            assert old['completed'] == new['completed'] == 300
            assert old['provenance']['dependencies_sha256'][str(SOURCE.relative_to(ROOT))] == report['before_source_sha256']
            assert new['provenance']['dependencies_sha256'][str(SOURCE.relative_to(ROOT))] == report['after_source_sha256']
            changes = []
            for a, b in zip(old['cases'], new['cases']):
                assert a['index'] == b['index'] and a['input_sha256'] == b['input_sha256']
                assert a['result']['oracles'] == b['result']['oracles']
                assert a['result']['routes']['classic'] == b['result']['routes']['classic']
                assert b['result']['routes']['smart']['status'] == 'exact'
                if a['result']['routes']['smart'] != b['result']['routes']['smart']:
                    assert a['result']['routes']['smart']['status'] == 'mismatch'
                    changes.append(dict(index=a['index'], before=a['result']['routes']['smart'],
                                        after=b['result']['routes']['smart']))
            def sanitized(row):
                case = after.generate(seed, row['index'])
                with tempfile.TemporaryDirectory(dir=work) as d:
                    for route in after.routes:
                        output = candidate('sanitized', case, Path(d), route)
                        assert sha(output) == row['result']['routes'][route]['raw_sha256']
                return 2
            with ThreadPoolExecutor(max_workers=2) as pool:
                renders = sum(pool.map(sanitized, new['cases']))
            report['campaigns'][str(seed)] = dict(before=old['summary'], after=new['summary'],
                changes=changes, sanitized_renders=renders, sanitizer_errors=0,
                before_report_sha256=sha(baseline.read_bytes()),
                after_report_sha256=sha((scratch/f'after-seed{seed}.json').read_bytes()))
            print('seed', seed, 'changed toward exact', len(changes), 'sanitized renders', renders, flush=True)
    report['status'] = 'PASS'
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2)+'\n')
    print('PASS: corpus, boundary masks/raw output, campaigns and ASan/UBSan', flush=True)


if __name__ == '__main__':
    main()
