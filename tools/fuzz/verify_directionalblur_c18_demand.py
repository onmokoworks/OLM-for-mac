#!/usr/bin/env python3
"""Independent negative-Offset demand admission; public routes, strict sanitizers."""
import argparse
import json
import os
import struct
from pathlib import Path
import tempfile
import time
from adapters.olmdirectionalblur import ROOT, SOURCE
from verify_directionalblur_c02 import Build
from verify_directionalblur_c09_matrix import cases
from core import raw_diff, sha


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--depth', type=int, choices=[8,16,32], default=8)
    p.add_argument('--baseline', required=True)
    p.add_argument('--scratch', type=Path, required=True)
    p.add_argument('--worker', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    args = p.parse_args()
    args.main, args.max_size, args.case_timeout = ROOT.parent.parent, 256, 30
    scratch = args.scratch.resolve(); scratch.mkdir(parents=True, exist_ok=True)
    os.environ.update(TMPDIR=str(scratch), TMP=str(scratch), TEMP=str(scratch))
    tempfile.tempdir = str(scratch)
    report = {'baseline': args.baseline, 'depth': args.depth, 'cases': [], 'builds': []}
    deadline = time.monotonic() + 1800
    with tempfile.TemporaryDirectory(dir=scratch, prefix='demand_') as tmp:
        tmp = Path(tmp)
        adapters = [Build(args, baseline=True), Build(args), Build(args, sanitizer=True)]
        for i, adapter in enumerate(adapters):
            d = tmp/str(i); d.mkdir()
            report['builds'].append(adapter.prepare(d, deadline))
        for name, case in cases(adapters[0]):
            if name.split(':')[0] not in ('noise-fade', 'active-noise-fade'): continue
            index = case['index']
            if args.depth == 16:
                case['pixels'] = b''.join(struct.pack('<H', v*32768//255) for v in case['pixels'])
            elif args.depth == 32:
                case['pixels'] = b''.join(struct.pack('<f', v/255.0) for v in case['pixels'])
            case['depth'] = args.depth
            for param in case['parameters']:
                if param['slot'] == 19: param['value'] = [-1,-18,-36,-72,-360,-720,-32768][index%7]
            with tempfile.TemporaryDirectory(dir=tmp) as d:
                d = Path(d)
                oracle, reference = adapters[0].oracle(case, d, deadline, 'smart')
                assert oracle['status'] == 'ok', (name, oracle)
                row = {'name': name, 'parameters': case['parameters'], 'geometry': case['geometry'],
                       'input_sha256': sha(case['pixels']), 'oracle': oracle, 'routes': {}}
                row['oracle']['raw_sha256'] = sha(reference)
                for route in ('classic', 'smart'):
                    observations = [a.candidate(case, d, route, deadline) for a in adapters]
                    assert observations[1][:2] == observations[2][:2], (name, route, 'sanitizer')
                    before, after = observations[0][0], observations[1][0]
                    result = {'before': before, 'after': after, 'sanitizer_same': True}
                    if after['status'] == 'ok':
                        result['diff'] = raw_diff(reference, observations[1][1], args.depth)
                        result['exact'] = reference == observations[1][1]
                        result['raw_sha256'] = sha(observations[1][1])
                    row['routes'][route] = result
                    if before['status'] == 'ok': assert observations[0][:2] == observations[1][:2]
                report['cases'].append(row)
                args.report.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
                assert after['status'] == 'refusal' or result['exact'], (name, result)
            if len(report['cases']) % 32 == 0: print('VERIFIED', len(report['cases']), flush=True)
        report['commands'] = [a.commands for a in adapters]
    report['source_sha256'] = {str(p.relative_to(ROOT)): sha(p.read_bytes())
        for p in [SOURCE, *sorted((ROOT/'core').glob('dblur*'))]}
    report['probe_sha256'] = sha(Path(__file__).read_bytes())
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    print('PASS', len(report['cases']), flush=True)


if __name__ == '__main__': main()
