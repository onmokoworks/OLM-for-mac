#!/usr/bin/env python3
"""C48 raw PF32 witnesses and independent size/noise/no-fade boundary controls."""
import argparse
import copy
import json
import os
from pathlib import Path
import random
import re
import shutil
import struct
import subprocess
import sys
import time
from types import SimpleNamespace
sys.dont_write_bytecode = True
from adapters.radialblur import Adapter, public, ROOT
from core import evaluate, load_corpus, sha


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--revision', help='Optional baseline source revision')
    ap.add_argument('--sanitize', action='store_true')
    ap.add_argument('--corpus', action='store_true', help='Replay all retained RadialBlur cases with F46')
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--case', type=Path, help='Replay one retained corpus file')
    ap.add_argument('--timeout', type=float, default=30)
    ap.add_argument('--indices', help='Recheck selected generated indices with a 30-second timeout')
    args = ap.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT/'orchestra/state/C48-radial-s01-pf32-mismatch')
    out.mkdir(parents=True, exist_ok=False)
    os.environ.update(TMPDIR=str(out), TMP=str(out), TEMP=str(out))
    if args.sanitize:
        os.environ['OLM_RADIAL_CANDIDATE_SANITIZE'] = '1'
    if args.revision:
        original = public.SOURCE
        source = subprocess.check_output(['git', 'show', args.revision+':mac/OLMRadialBlur/OLMRadialBlur.cpp'], cwd=ROOT).decode()
        source = re.sub(r'^#include "([^"]+)"', lambda m: '#include "'+str((original.parent/m[1]).resolve())+'"', source, flags=re.MULTILINE)
        snapshot = out/'baseline.cpp'
        snapshot.write_text(source)
        snapshot.with_suffix('.h').write_bytes(original.with_suffix('.h').read_bytes())
        for name in ('OLMRadialBlur.h', 'OLMRadialBlur_Strings.cpp', 'OLMRadialBlur_Strings.h'):
            (out/name).symlink_to(original.parent/name)
        public.SOURCE = snapshot
    main = ROOT.parent.parent if ROOT.parent.name == 'worktrees' else ROOT
    adapter = Adapter(SimpleNamespace(max_size=256, case_timeout=args.timeout, main=main,
        worker=Path.home()/'.cache/olm-emu/worker-F46-pow/aex-guest-worker'))
    adapter.routes = ('smart',)
    adapter.oracle_routes = {'smart': 'smart'}
    deadline = time.monotonic()+1800
    report = dict(provenance=adapter.prepare(out, deadline), rows=[])
    witness, _ = load_corpus(ROOT/'tests/fuzz_corpus/radialblur/seed102_case000008_S01.json', adapter)
    cases = [('original', adapter.generate(102, 8)), ('reduced', witness)]
    for w,h in [(1,54), (54,1), (7,9)]:
        rng = random.Random(48+w+h)
        bits = [rng.randrange(2) for _ in range(w*h*4)]
        for depth in (8,16,32):
            fmt, top = {8:('B',255),16:('H',32768),32:('f',1.)}[depth]
            for size,noise in [(100,100),(100,0),(0,100),(50,100)]:
                case = copy.deepcopy(witness)
                case.update(geometry=[w,h], depth=depth,
                    pixels=b''.join(struct.pack('<'+fmt,b*top) for b in bits))
                for p in case['parameters']:
                    if p['slot'] == 2: p['value'] = [w/2,h/2]
                    if p['slot'] == 22: p['value'] = size
                    if p['slot'] == 24: p['value'] = noise
                cases.append((f'{w}x{h}-PF{depth}-size{size}-noise{noise}',case))
    if args.corpus:
        cases = [(path.name, load_corpus(path, adapter)[0])
                 for path in sorted((ROOT/'tests/fuzz_corpus/radialblur').glob('*.json'))]
    elif args.case:
        cases = [(args.case.name, load_corpus(args.case, adapter)[0])]
    elif args.indices:
        cases = [(str(i), adapter.generate(args.seed, i))
                 for i in map(int, args.indices.split(','))]
    try:
        for i,(name,case) in enumerate(cases):
            directory=out/str(i); directory.mkdir()
            result=evaluate(adapter,case,directory,deadline)
            report['rows'].append(dict(name=name,case={k:v for k,v in case.items() if k!='pixels'},
                input_sha256=sha(case['pixels']),result=result))
            (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
            print(name,result['routes']['smart']['status'],flush=True)
    finally:
        shutil.rmtree(out/'build',ignore_errors=True)
    return int(any(r['result']['routes']['smart']['status'] != 'exact'
                   for r in report['rows']))

if __name__ == '__main__':
    raise SystemExit(main())
