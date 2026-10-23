#!/usr/bin/env python3
"""Test native-expf substitution against frozen sanitized controls.

Candidate source lives only in ticket scratch; production files are untouched.
"""
import argparse
import json
import os
from pathlib import Path
import re
import sys
import tempfile
sys.dont_write_bytecode = True
from adapters import olmblur
from core import sha
from run import ROOT
from verify_blur_retained_C12 import verify


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--scratch', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--legacy', action='store_true')
    p.add_argument('--depth', type=int, choices=(16, 32), nargs='+', default=[16, 32])
    args = p.parse_args()
    s = args.scratch.resolve()
    assert s.is_relative_to(ROOT/'orchestra/state/C21-olmblur-smart-r5')
    s.mkdir(parents=True, exist_ok=True)
    os.environ.update(TMPDIR=str(s), TMP=str(s), TEMP=str(s))
    original = olmblur.CORES
    report = {'legacy': args.legacy, 'baseline': verify(s), 'experiments': {}}
    with tempfile.TemporaryDirectory(prefix='expf_', dir=s) as td:
        for depth in args.depth:
            lane = 'legacy' if args.legacy else 'nonlegacy'
            path = ROOT/f'core/olmblur_worker{depth}_{lane}.cpp'
            source = path.read_text()
            body, count = re.subn(r'static_cast<float>\(\s*std::exp\(static_cast<double>\(exponent\)\)\)',
                                 'std::exp(exponent)', source)
            assert count == 1
            candidate = Path(td)/path.name
            candidate.write_text(body)
            try:
                olmblur.CORES = [candidate if x == path else x for x in original]
                result = verify(s)
            finally:
                olmblur.CORES = original
            result.update(source_sha256=sha(source.encode()), candidate_source_sha256=sha(body.encode()))
            report['experiments'][str(depth)] = result
            print(depth, result['status'], [x for x in result['lines'] if 'exact=1' not in x], flush=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    assert report['baseline']['status']['status'] == 'ok'
    assert len(report['baseline']['lines']) == 80
    assert not report['baseline']['stderr']


if __name__ == '__main__':
    main()
