#!/usr/bin/env python3
"""Independent typed angle-boundary renders against original public Smart AEX."""
import argparse
import copy
import json
import os
from pathlib import Path
import struct
import tempfile
import time

from adapters.olmdirectionalblur import ROOT, SOURCE
from core import raw_diff, sha
from verify_directionalblur_c02 import Build
from verify_directionalblur_c09_matrix import cases


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline', required=True)
    p.add_argument('--scratch', type=Path, required=True)
    p.add_argument('--worker', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    args = p.parse_args()
    args.main, args.max_size, args.case_timeout = ROOT.parent.parent, 256, 30
    scratch = args.scratch.resolve()
    assert scratch.is_relative_to(ROOT/'orchestra/state')
    scratch.mkdir(parents=True, exist_ok=True)
    os.environ.update(TMPDIR=str(scratch), TMP=str(scratch), TEMP=str(scratch),
                      PYTHONDONTWRITEBYTECODE='1')
    tempfile.tempdir = str(scratch)
    # All integer angles in [-720,720] whose float radians differ between
    # full pi and the binary's 3.14159265, plus adjacent controls and anchors.
    boundaries = [-693,-488,-406,-289,-248,-169,-11,68,109,226,308,513,542,677,706]
    angles = sorted({a+d for a in boundaries for d in (-1,0,1)} | {0,45,-73,123})
    report = {'baseline': args.baseline, 'angles': angles, 'cases': [], 'builds': []}
    deadline = time.monotonic()+1800
    with tempfile.TemporaryDirectory(prefix='angles_', dir=scratch) as tmp:
        tmp = Path(tmp)
        adapters = [Build(args, baseline=True), Build(args), Build(args, sanitizer=True)]
        for i, adapter in enumerate(adapters):
            d = tmp/str(i); d.mkdir()
            report['builds'].append(adapter.prepare(d, deadline))
        templates = [c for name, c in cases(adapters[0])
                     if name in ('noise-fade:3', 'plain-fade:4')]
        assert len(templates) == 2
        for angle in angles:
            for depth in (8,16,32):
                for template in templates:
                    case = copy.deepcopy(template)
                    case['depth'] = depth
                    if depth == 16:
                        case['pixels'] = b''.join(struct.pack('<H', v*32768//255) for v in case['pixels'])
                    elif depth == 32:
                        case['pixels'] = b''.join(struct.pack('<f', v/255.0) for v in case['pixels'])
                    for param in case['parameters']:
                        if param['slot'] == 1: param['value'] = angle
                    with tempfile.TemporaryDirectory(prefix='case_', dir=tmp) as d:
                        d = Path(d)
                        oracle, reference = adapters[0].oracle(case, d, deadline, 'smart')
                        assert oracle['status'] == 'ok', oracle
                        row = {'angle': angle, 'depth': depth, 'geometry': case['geometry'],
                               'parameters': case['parameters'], 'input_sha256': sha(case['pixels']),
                               'oracle': dict(oracle, raw_sha256=sha(reference)), 'routes': {}}
                        for route in ('classic','smart'):
                            obs = [a.candidate(case, d, route, deadline) for a in adapters]
                            assert obs[1][:2] == obs[2][:2], (angle, depth, route, 'sanitizer')
                            assert obs[1][0]['status'] == 'ok'
                            before, after = obs[0][1], obs[1][1]
                            assert after == reference, (angle, depth, route, raw_diff(reference, after, depth))
                            if before == reference: assert before == after
                            row['routes'][route] = {'before': obs[0][0], 'after': obs[1][0],
                                'before_sha256': sha(before), 'after_sha256': sha(after),
                                'before_diff': raw_diff(reference, before, depth),
                                'exact': True, 'sanitizer_same': True}
                        report['cases'].append(row)
                    if len(report['cases']) % 42 == 0:
                        print('VERIFIED', len(report['cases']), flush=True)
                        args.report.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
        report['commands'] = [a.commands for a in adapters]
    report['source_sha256'] = {str(p.relative_to(ROOT)): sha(p.read_bytes())
        for p in (SOURCE, ROOT/'core/dblur_frontonly.cpp')}
    report['probe_sha256'] = sha(Path(__file__).read_bytes())
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    print('PASS', len(report['cases']), flush=True)


if __name__ == '__main__':
    main()
