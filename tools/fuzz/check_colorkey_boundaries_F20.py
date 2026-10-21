#!/usr/bin/env python3
"""Independent zero-count toggles, nonfinite RGB predicates, odd byte strides.

Smart AEX is the numerical oracle for both Mac entrypoints here. run.py retains
the separate like-named route comparison required by the ticket.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import itertools
import json
import os
from pathlib import Path
import struct
import time
from types import SimpleNamespace

from adapters.olmcolorkey import Adapter
from core import raw_diff, sha

ROOT = Path(__file__).resolve().parents[2]


def cases(adapter):
    for depth, keep, premult, replace, component, edge in itertools.product(
            (8, 16, 32), (0, 1), (0, 1), (0, 1), (0, 1), ('none', 'thin-in', 'thin-out', 'blur')):
        parameters = adapter.defaults(3, 2)
        values = {1:keep, 4:premult, 8:component, 22:0, 23:replace,
                  14: -1 if edge=='thin-in' else 1 if edge=='thin-out' else 0,
                  18: 1 if edge=='blur' else 0}
        for p in parameters:
            if p['slot'] in values: p['value'] = values[p['slot']]
        if depth==32:
            pixels = b''.join(struct.pack('<4I', alpha, 0x7f800000, 0xff812346, 0x80000000)
                for alpha in (0, 0x80000000, 0x3f000000, 0x7f800000, 0xff812346, 0x7fc12345))
        else:
            top = 255 if depth==8 else 32768
            pixels = b''.join(struct.pack('<4B' if depth==8 else '<4H', a, 0, top//2, top)
                for a in (0, 1, top//2, top, top-1, 0))
        yield dict(label=f'zero-{depth}-{keep}-{premult}-{replace}-{component}-{edge}',
            seed=0, index=0, geometry=[3,2], depth=depth, parameters=parameters, pixels=pixels,
            input_padding=3, output_padding=3)
    # All three component positions; both alpha signs; scalar/per-component and
    # Keep modes distinguish ordered rejection from unordered acceptance.
    for channel, alpha, word, component, keep in itertools.product(range(3),
            (0, 0x80000000), (0x7f800000, 0xff800000, 0x7f812345, 0xff812346), (0,1), (0,1)):
        parameters = adapter.defaults(1,2)
        for p in parameters:
            if p['slot'] in (1,4,8,22,24,26):
                p['value'] = {1:keep,4:1,8:component,22:1,24:1,26:[255,0,0,0]}[p['slot']]
        rgb = [0,0,0]; rgb[channel] = word
        yield dict(label=f'rgb-{channel}-{alpha:x}-{word:x}-{component}-{keep}',
            seed=0, index=0, geometry=[1,2], depth=32, parameters=parameters,
            pixels=struct.pack('<4I',alpha,*rgb)*2, input_padding=1, output_padding=1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scratch', type=Path, required=True)
    parser.add_argument('--worker', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    scratch = args.scratch.resolve()
    assert scratch.is_relative_to(ROOT/'orchestra/state/F20-colorkey-zero-color-and-byte-safe')
    scratch.mkdir(parents=True,exist_ok=True)
    os.environ.update(TMPDIR=str(scratch),TMP=str(scratch),TEMP=str(scratch),
                      ASAN_OPTIONS='detect_leaks=0',UBSAN_OPTIONS='halt_on_error=1')
    options = SimpleNamespace(max_size=256,case_timeout=30,main=ROOT.parent.parent,worker=args.worker)
    deadline = time.monotonic()+900
    adapters = []
    provenance = []
    for sanitize in (False,True):
        os.environ['OLM_COLOR_TRIAGE_SANITIZE'] = str(int(sanitize))
        adapter = Adapter(options)
        build = scratch/('san' if sanitize else 'o2'); build.mkdir(exist_ok=True)
        provenance.append(adapter.prepare(build,deadline)); adapters.append(adapter)

    def check(case):
        directory = scratch/case['label']; directory.mkdir(exist_ok=True)
        oracle, raw = adapters[0].oracle(case,directory,deadline,'smart')
        assert oracle['status']=='ok',(case['label'],oracle)
        results = {}
        for build,adapter in zip(('o2','san'),adapters):
            for route in ('classic','smart'):
                outcome, candidate, _ = adapter.candidate(case,directory,route,deadline)
                results[build+'-'+route] = dict(status=outcome, exact=candidate==raw,
                                               diff=raw_diff(raw,candidate,case['depth']))
                assert outcome['status']=='ok' and not outcome.get('sanitizer'), (case['label'],outcome)
        return dict(label=case['label'],input_sha256=sha(case['pixels']),oracle_sha256=sha(raw),results=results)
    with ThreadPoolExecutor(max_workers=2) as pool:
        rows = list(pool.map(check,cases(adapters[0])))
    report = dict(provenance=provenance,case_count=len(rows),cases=rows,
                  exact=sum(v['exact'] for row in rows for v in row['results'].values()))
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(report['case_count'],'cases;',report['exact'],'/',len(rows)*4,'exact; sanitizer clean')
    assert report['exact']==len(rows)*4


if __name__=='__main__': main()
