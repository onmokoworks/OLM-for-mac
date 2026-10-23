#!/usr/bin/env python3
"""Recheck all measured nonfinite refusals with the current hash-bound oracle.

Both experiments are scratch-only. No admission or numerical change is promoted.
"""
import argparse
import json
import os
from pathlib import Path
import tempfile
import time

from adapters.olmdirectionalblur import ROOT
from core import raw_diff, sha
from probe_directionalblur_c30_nonfinite import Nonfinite
from probe_directionalblur_c36_nan import RotationNaN


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--campaigns', type=Path, nargs='+', required=True)
    p.add_argument('--worker', type=Path, required=True)
    p.add_argument('--scratch', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    args = p.parse_args()
    args.main, args.max_size, args.case_timeout = ROOT.parent.parent, 256, 30
    scratch = args.scratch.resolve()
    assert scratch.is_relative_to(ROOT/'orchestra/state')
    scratch.mkdir(parents=True, exist_ok=True)
    os.environ.update(TMPDIR=str(scratch), TMP=str(scratch), TEMP=str(scratch),
                      PYTHONDONTWRITEBYTECODE='1')
    tempfile.tempdir = str(scratch)
    report = {'campaigns': [], 'experiments': []}
    targets = []
    for path in args.campaigns:
        campaign = json.loads(path.read_text())
        assert campaign['status'] == 'complete' and campaign['completed'] == 300
        assert campaign['provenance']['worker_sha256'] == sha(args.worker.read_bytes())
        report['campaigns'].append({'path': str(path), 'sha256': sha(path.read_bytes()),
                                   'summary': campaign['summary']})
        for row in campaign['cases']:
            if row['result']['routes']['smart']['status'] == 'refusal':
                assert row['profile'] == 'nonfinite', row
                assert row['result']['oracles']['smart']['status'] == 'ok', row
                targets.append(row)
    deadline = time.monotonic() + 1800
    for name, cls in [('finite-gate-bypass', Nonfinite), ('rotation-generated-nan', RotationNaN)]:
        experiment = {'name': name, 'builds': [], 'cases': []}
        with tempfile.TemporaryDirectory(prefix='c51_', dir=scratch) as tmp:
            tmp = Path(tmp)
            adapters = [cls(args), cls(args, sanitizer=True)]
            for i, adapter in enumerate(adapters):
                d = tmp/str(i); d.mkdir()
                experiment['builds'].append(adapter.prepare(d, deadline))
            for target in targets:
                case = adapters[0].generate(target['seed'], target['index'])
                assert sha(case['pixels']) == target['input_sha256']
                with tempfile.TemporaryDirectory(prefix='case_', dir=tmp) as directory:
                    directory = Path(directory)
                    oracle, reference = adapters[0].oracle(case, directory, deadline, 'smart')
                    assert oracle['status'] == 'ok', oracle
                    assert sha(reference) == target['result']['oracles']['smart']['raw_sha256']
                    result, raw, guards = adapters[0].candidate(case, directory, 'smart', deadline)
                    sanitized, sanraw, _ = adapters[1].candidate(case, directory, 'smart', deadline)
                    assert result == sanitized and raw == sanraw
                    assert result['status'] == 'ok', result
                    row = {k: target[k] for k in ('seed', 'index', 'depth', 'geometry',
                           'profile', 'parameters', 'input_sha256', 'input_padding', 'output_padding')}
                    row.update(oracle=oracle, candidate=result, reference_sha256=sha(reference),
                               candidate_sha256=sha(raw), diff=raw_diff(reference, raw, case['depth']),
                               exact=reference == raw, sanitizer_same=True, guards=guards)
                    experiment['cases'].append(row)
                    print(name, row['seed'], row['index'], row['diff'], flush=True)
            experiment['commands'] = [a.commands for a in adapters]
        report['experiments'].append(experiment)
        args.report.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    report['source_hashes'] = {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in
        [Path(__file__), ROOT/'tools/fuzz/probe_directionalblur_c30_nonfinite.py',
         ROOT/'tools/fuzz/probe_directionalblur_c36_nan.py', ROOT/'core/x86_float.h',
         *sorted((ROOT/'core').glob('dblur*')), ROOT/'mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp'] if p.is_file()}
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')


if __name__ == '__main__':
    main()
