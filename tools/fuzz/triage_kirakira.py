#!/usr/bin/env python3
"""T06 scratch-only admission experiments; all remaining arguments go to run.py.

Example: python3 tools/fuzz/triage_kirakira.py --experiment tuples --plugin
olmkirakira --jobs 2 --scratch orchestra/state/T06-triage-kirakira ...
Production source is never rewritten. The generated translation unit uses a
compile-time switch; strings and SDK helpers still come from the normal adapter.
"""
import argparse
import json
import math
import struct
from pathlib import Path
import sys

sys.dont_write_bytecode = True
import run
from adapters import olmkirakira
from core import sha, raw_diff


def difference_details(expected, actual, case):
    depth = case['depth']
    unit, fmt = {8:(1,'B'),16:(2,'H'),32:(4,'f')}[depth]
    words = [i//unit for i in range(0,len(expected),unit)
             if expected[i:i+unit] != actual[i:i+unit]]
    channels = {c:sum(i%4 == n for i in words) for n,c in enumerate('ARGB')}
    pixels = sorted(set(i//4 for i in words))
    w,h = case['geometry']
    finite_deltas = []
    nonfinite = 0
    for i in words:
        a = struct.unpack_from('<'+fmt,expected,i*unit)[0]
        b = struct.unpack_from('<'+fmt,actual,i*unit)[0]
        if math.isfinite(a) and math.isfinite(b):
            finite_deltas.append(abs(a-b))
        else:
            nonfinite += 1
    first = words[0]
    return dict(raw_diff(expected,actual,depth),
        expected_sha256=sha(expected), actual_sha256=sha(actual),
        max_abs_byte_diff=max(abs(a-b) for a,b in zip(expected,actual)),
        max_abs_finite_sample_diff=max(finite_deltas,default=None),
        nonfinite_differing_words=nonfinite, channels=channels,
        differing_pixels=len(pixels),total_pixels=w*h,
        bbox=[min(p%w for p in pixels),min(p//w for p in pixels),
              max(p%w for p in pixels),max(p//w for p in pixels)],
        affected_rows=sorted(set(p//w for p in pixels)),
        first_xy_channel=[(first//4)%w,(first//4)//w,'ARGB'[first%4]],
        first_stage=None,
        stage_limit='Mac src/glow/prequantized debug points exist; retained session worker exposes final raw only, so no paired first stage is claimed')


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--experiment', choices=('tuples', 'request', 'layout', 'all'), required=True)
    parser.add_argument('--sanitizers', action='store_true')
    parser.add_argument('--details', type=Path)
    args, rest = parser.parse_known_args()
    if '--jobs' not in rest or rest[rest.index('--jobs')+1] != '2':
        parser.error('T06 requires --jobs 2')
    details = []
    original = olmkirakira.Adapter

    class ExperimentAdapter(original):
        def compile(self, argv, deadline):
            argv = list(argv)
            if argv[0] == 'clang++':
                host = next(Path(x) for x in argv if str(x).endswith('/host.cpp'))
                source = olmkirakira.SOURCE.read_text()
                if args.experiment in ('tuples', 'all'):
                    old = 'if (!exact_closure && !generic_beta) {'
                    assert source.count(old) == 2
                    source = source.replace(old, 'if (!OLM_KIRA_TRIAGE_GATE_OFF && !exact_closure && !generic_beta) {')
                if args.experiment in ('request', 'all'):
                    old = 'if (!exact_request_matches_known_frame &&\n\t\t!request_contains_generic_full_frame) {'
                    assert source.count(old) == 1
                    source = source.replace(old, 'if (!OLM_KIRA_TRIAGE_GATE_OFF && !exact_request_matches_known_frame &&\n\t\t!request_contains_generic_full_frame) {')
                if args.experiment in ('layout', 'all'):
                    old = ('if ((reinterpret_cast<uintptr_t>(world->data) % alignment) != 0 ||\n'
                           '\t\t(static_cast<size_t>(world->rowbytes) % alignment) != 0) {')
                    assert source.count(old) == 1
                    source = source.replace(old, ('if (!OLM_KIRA_TRIAGE_GATE_OFF &&\n'
                        '\t\t((reinterpret_cast<uintptr_t>(world->data) % alignment) != 0 ||\n'
                        '\t\t(static_cast<size_t>(world->rowbytes) % alignment) != 0)) {'))
                source = source.replace('#include "OLMKiraKira.h"', '#include "'+str(olmkirakira.SOURCE.with_suffix('.h'))+'"')
                source = source.replace('#include "../../core/', '#include "'+str(olmkirakira.ROOT/'core')+'/')
                copied = host.parent/'kirakira_gate_off.cpp'
                copied.write_text(source)
                host.write_text(host.read_text().replace(str(olmkirakira.SOURCE), str(copied)))
                argv.insert(1, '-DOLM_KIRA_TRIAGE_GATE_OFF=1')
                if args.sanitizers:
                    argv[1:1] = ['-fsanitize=address,undefined', '-fno-sanitize-recover=all', '-fno-omit-frame-pointer', '-g']
                    self.env['ASAN_OPTIONS'] = 'detect_leaks=0'
                    self.env['UBSAN_OPTIONS'] = 'print_stacktrace=1:halt_on_error=1'
                self.experiment_binding = dict(experiment=args.experiment,
                    sanitizers=args.sanitizers, scratch_source_sha256=sha(source.encode()),
                    switch='OLM_KIRA_TRIAGE_GATE_OFF=1',
                    limitation='Bypasses selected admission checks and optionally typed alignment; span/format checks, request normalization, helper fallbacks and arithmetic unchanged')
            return super().compile(argv, deadline)

        def oracle(self, case, directory, deadline):
            if args.details:
                (directory/'triage-reference.raw').unlink(missing_ok=True)
            status, raw = super().oracle(case, directory, deadline)
            if args.details and status['status'] == 'ok':
                (directory/'triage-reference.raw').write_bytes(raw)
            return status, raw

        def candidate(self, case, directory, route, deadline):
            outcome = super().candidate(case, directory, route, deadline)
            reference = directory/'triage-reference.raw'
            if args.details and reference.exists() and outcome[0]['status'] == 'ok':
                expected, actual = reference.read_bytes(), outcome[1]
                if expected != actual:
                    details.append(dict(index=case['index'], route=route,
                        geometry=case['geometry'], depth=case['depth'],
                        input_sha256=sha(case['pixels']),
                        **difference_details(expected, actual, case)))
            return outcome

        def prepare(self, scratch, deadline):
            result = super().prepare(scratch, deadline)
            return dict(result, triage=self.experiment_binding)

    olmkirakira.Adapter = ExperimentAdapter
    sys.argv = [sys.argv[0], *rest]
    code = run.main()
    if args.details:
        args.details.parent.mkdir(parents=True, exist_ok=True)
        args.details.write_text(json.dumps(details, indent=2, sort_keys=True)+'\n')
    return code


if __name__ == '__main__':
    sys.exit(main())
