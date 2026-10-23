#!/usr/bin/env python3
"""Classify the retained PF32 refusals using a scratch-only finite-gate bypass.

No numerical operation is changed. NaN sign-only differences belong to F38.
"""
import argparse
import json
import os
from pathlib import Path
import struct
import tempfile
import time

from adapters.olmdirectionalblur import ROOT, SOURCE
from adapters.public import replace_once
from core import raw_diff, sha
from verify_directionalblur_c02 import Build


class Nonfinite(Build):
    def compile(self, argv, deadline):
        argv = list(argv)
        if argv[0] == 'clang++':
            host = Path(next(str(x) for x in argv if str(x).endswith('/host.cpp')))
            body = replace_once(SOURCE.read_text(),
                'if (!GenericPF32FiniteInput(input)) return OLM_DIRECTIONAL_REFUSAL("pf32-nonfinite-input");',
                '// C30 diagnostic bypass; production finite policy stays intact.')
            body = body.replace('#include "../../core/', f'#include "{ROOT}/core/')
            body = body.replace('#include "OLMDirectionalBlur.h"', f'#include "{SOURCE.with_suffix(".h")}"')
            target = host.with_name('nonfinite.cpp')
            target.write_text(body)
            host.write_text(replace_once(host.read_text(), str(SOURCE), str(target)))
        return super().compile(argv, deadline)


def main():
    p = argparse.ArgumentParser(description=__doc__)
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
    deadline = time.monotonic() + 600
    report = {'cases': [], 'builds': []}
    with tempfile.TemporaryDirectory(prefix='nonfinite_', dir=scratch) as tmp:
        tmp = Path(tmp)
        adapters = [Nonfinite(args), Nonfinite(args, sanitizer=True)]
        for i, adapter in enumerate(adapters):
            d = tmp/str(i); d.mkdir()
            report['builds'].append(adapter.prepare(d, deadline))
        for index in (109, 299):
            case = adapters[0].generate(1, index)
            with tempfile.TemporaryDirectory(prefix='case_', dir=tmp) as d:
                d = Path(d)
                oracle, reference = adapters[0].oracle(case, d, deadline, 'smart')
                assert oracle['status'] == 'ok', oracle
                result, raw, _ = adapters[0].candidate(case, d, 'smart', deadline)
                sanitized, sanraw, _ = adapters[1].candidate(case, d, 'smart', deadline)
                assert result == sanitized and raw == sanraw
                assert result['status'] == 'ok', result
                words = list(zip(struct.iter_unpack('<I', reference), struct.iter_unpack('<I', raw)))
                different = [(a[0], b[0]) for a, b in words if a != b]
                sign_only = sum((a ^ b) == 0x80000000 and
                    (a & 0x7f800000) == 0x7f800000 and (a & 0x7fffff) != 0
                    for a, b in different)
                row = {'seed': 1, 'index': index, 'oracle': oracle, 'candidate': result,
                    'reference_sha256': sha(reference), 'candidate_sha256': sha(raw),
                    'diff': raw_diff(reference, raw, 32), 'nan_sign_only_words': sign_only,
                    'other_different_words': len(different)-sign_only, 'sanitizer_same': True}
                report['cases'].append(row)
                print(index, row['diff'], 'NaN sign only:', sign_only, flush=True)
        report['commands'] = [a.commands for a in adapters]
    report['probe_sha256'] = sha(Path(__file__).read_bytes())
    report['source_sha256'] = sha(SOURCE.read_bytes())
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')


if __name__ == '__main__':
    main()
