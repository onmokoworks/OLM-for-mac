#!/usr/bin/env python3
"""C09 scratch-only PF8 fallback gates; retain core safety and real public routes."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

from adapters.olmdirectionalblur import ROOT, SOURCE
from adapters.public import replace_once
from verify_directionalblur_c02 import Build
from core import raw_diff, sha


class Gate(Build):
    def __init__(self, args, **kwargs):
        super().__init__(args, **kwargs)
        self.source_ref = args.baseline

    def compile(self, argv, deadline):
        argv = list(argv)
        if argv[0] == 'clang++':
            host = Path(next(str(x) for x in argv if str(x).endswith('/host.cpp')))
            body = subprocess.check_output(['git', 'show', f'{self.source_ref}:{SOURCE.relative_to(ROOT)}'], cwd=ROOT).decode()
            start = body.index('    if (', body.index('static bool CanUsePF8FeatureFallback'))
            end = body.index('return false;', start) + len('return false;')
            body = body[:start] + '    // C09 scratch-only admission bypass; core bounds remain.\n' + body[end:]
            body = body.replace('#include "../../core/', f'#include "{ROOT}/core/')
            body = body.replace('#include "OLMDirectionalBlur.h"', f'#include "{SOURCE.with_suffix(".h")}"')
            target = host.with_name('gate.cpp')
            target.write_text(body)
            self.gate_sha256 = sha(body.encode())
            host.write_text(replace_once(host.read_text(), str(SOURCE), str(target)))
        return super().compile(argv, deadline)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--worker', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--scratch', type=Path, required=True)
    p.add_argument('--baseline', required=True)
    p.add_argument('--seeds', nargs='+', type=int, default=[1, 2, 3])
    args = p.parse_args()
    args.main, args.max_size, args.case_timeout = ROOT.parent.parent, 256, 30
    scratch = args.scratch.resolve(); scratch.mkdir(parents=True, exist_ok=True)
    os.environ.update(TMPDIR=str(scratch), TMP=str(scratch), TEMP=str(scratch), PYTHONDONTWRITEBYTECODE='1')
    tempfile.tempdir = str(scratch)
    deadline = time.monotonic() + 3600
    report = {'baseline': args.baseline, 'cases': [], 'builds': [], 'seeds': args.seeds}
    with tempfile.TemporaryDirectory(prefix='gate_', dir=scratch) as tmp:
        tmp = Path(tmp)
        adapters = [Build(args, baseline=True), Gate(args), Gate(args, sanitizer=True)]
        for i, adapter in enumerate(adapters):
            directory = tmp/str(i); directory.mkdir()
            report['builds'].append(adapter.prepare(directory, deadline))
        def run(item):
            seed, index = item; case = adapters[0].generate(seed, index)
            with tempfile.TemporaryDirectory(prefix='case_', dir=tmp) as d:
                d = Path(d); results = []; raws = []
                for adapter in adapters:
                    result, raw, guards = adapter.candidate(case, d, 'smart', deadline)
                    if result['status'] == 'ok': result['raw_sha256'] = sha(raw)
                    results.append(result); raws.append(raw)
                assert results[1] == results[2], (seed, index, results)
                row = {'seed': seed, 'index': index, 'depth': case['depth'], 'geometry': case['geometry'],
                       'parameters': case['parameters'], 'before': results[0], 'gate': results[1],
                       'sanitizer_same': True, 'changed': results[0] != results[1]}
                if row['changed']:
                    assert results[0]['status'] == 'refusal', row
                    oracle, reference = adapters[0].oracle(case, d, deadline, 'smart')
                    row['oracle'] = oracle
                    if oracle['status'] == 'ok':
                        oracle['raw_sha256'] = sha(reference)
                        if results[1]['status'] == 'ok':
                            row['exact'] = reference == raws[1]
                            row['diff'] = raw_diff(reference, raws[1], case['depth'])
                return row
        with ThreadPoolExecutor(max_workers=2) as pool:
            for row in pool.map(run, [(s, i) for s in args.seeds for i in range(300)]):
                report['cases'].append(row)
                if row['changed']:
                    print('CHANGED', row['seed'], row['index'], row['gate']['status'], row.get('exact'), row.get('diff'), flush=True)
        report['commands'] = [a.commands for a in adapters]
        report['gate_sha256'] = adapters[1].gate_sha256
    report['probe_sha256'] = sha(Path(__file__).read_bytes())
    report['source_sha256'] = {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in [SOURCE, *sorted((ROOT/'core').glob('dblur*'))]}
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    print('PASS', len(report['cases']), 'O2/sanitized pairs', flush=True)


if __name__ == '__main__':
    main()
