#!/usr/bin/env python3
"""Independent sanitized Smart Override controls and current-worker corpus replay."""
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
from adapters.radialblur import Adapter, ROOT, public
from core import evaluate, load_corpus, save_corpus, sha


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--corpus', action='store_true')
    p.add_argument('--save-witness', action='store_true', help='Save the four freshly compared campaign gains to the corpus')
    p.add_argument('--witness-case', help='With --save-witness, retry one seed:index pair')
    p.add_argument('--revision', help='Optional source revision for a baseline measurement')
    p.add_argument('--high-work', action='store_true', help='Independent high-quality, dual-fade Override controls')
    p.add_argument('--sparse', action='store_true', help='Use an independent single opaque impulse amid transparent RGB')
    args = p.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT/'orchestra/state/C49-radial-smart-r9')
    out.mkdir(parents=True, exist_ok=False)
    os.environ.update(TMPDIR=str(out), TMP=str(out), TEMP=str(out), OLM_RADIAL_CANDIDATE_SANITIZE='1')
    if args.revision:
        source=public.SOURCE
        body=subprocess.check_output(['git','show',args.revision+':mac/OLMRadialBlur/OLMRadialBlur.cpp'],cwd=ROOT).decode()
        body=re.sub(r'^#include "([^\"]+)"',lambda m:'#include "'+str((source.parent/m[1]).resolve())+'"',body,flags=re.MULTILINE)
        snapshot=out/'baseline.cpp'; snapshot.write_text(body)
        snapshot.with_suffix('.h').write_bytes(source.with_suffix('.h').read_bytes())
        for name in ('OLMRadialBlur.h','OLMRadialBlur_Strings.h','OLMRadialBlur_Strings.cpp'):
            (out/name).symlink_to(source.parent/name)
        public.SOURCE=snapshot
    a = Adapter(SimpleNamespace(main=ROOT.parent.parent, max_size=256, case_timeout=60,
        worker=Path.home()/'.cache/olm-emu/worker-F46-pow/aex-guest-worker'))
    a.routes = ('smart',)
    a.oracle_routes = {'smart':'smart'}
    if args.save_witness:
        a.routes = ('classic','smart')
        a.oracle_routes = {'classic':'classic','smart':'smart'}
    deadline = time.monotonic()+1800
    report = dict(provenance=a.prepare(out, deadline), rows=[])
    cases = []
    for w,h in ((7,9),(19,11)):
        for depth in (8,16,32):
            rng = random.Random(49+w+h+depth)
            fmt, top = {8:('B',255),16:('H',32768),32:('f',1.)}[depth]
            pixels = b''.join(struct.pack('<'+fmt, rng.random() if depth==32 else rng.randrange(top+1)) for _ in range(w*h*4))
            if args.sparse:
                sparse=bytearray(pixels)
                for index in range(w*h):
                    struct.pack_into('<'+fmt,sparse,index*4*(depth//8),top if index==(h//2)*w+w//2 else 0)
                pixels=bytes(sparse)
            for strength in ((188,) if args.high_work else (1,1395,2000)):
                for repeat in (0,1):
                    case = copy.deepcopy(a.generate(105,71))
                    case.update(geometry=[w,h],depth=depth,pixels=pixels,input_padding=3,output_padding=5)
                    values = {2:[w/2,h/2],4:strength,5:3,6:38,7:3,10:17,11:2,12:16,13:3,
                              15:repeat,17:1.,18:0.,20:30.5,21:1.,22:50.,24:50.,25:2,27:125,28:0.,29:25.}
                    if args.high_work:
                        values.update({6:17,7:66,10:3,12:23,13:99,20:50.,22:0.,24:16.5,25:1})
                    for param in case['parameters']:
                        if param['slot'] in values: param['value']=values[param['slot']]
                    cases.append((f'{w}x{h}-PF{depth}-strength{strength}-repeat{repeat}',case))
    if args.corpus:
        cases = [(path.name,load_corpus(path,a)[0]) for path in sorted((ROOT/'tests/fuzz_corpus/radialblur').glob('*.json'))]
    if args.save_witness:
        selected = [tuple(map(int,args.witness_case.split(':')))] if args.witness_case else ((105,71),(105,150),(1,148),(1,117))
        cases = [(f'seed{seed}-case{index}',a.generate(seed,index)) for seed,index in selected]
    try:
        for i,(name,case) in enumerate(cases):
            directory=out/str(i); directory.mkdir()
            result=evaluate(a,case,directory,deadline)
            report['rows'].append(dict(name=name,input_sha256=sha(case['pixels']),result=result))
            (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
            if args.save_witness and result['routes']['smart']['status']=='exact':
                provenance=dict(report['provenance'],case_timeout_seconds=60)
                path=ROOT/f'tests/fuzz_corpus/radialblur/C49_seed{case["seed"]}_case{case["index"]:06d}.json'
                save_corpus(path,a,case,case,result,
                    dict(attempts=0,accepted=[],outcomes={},bounded=True,minimality_claimed=False),provenance)
            print(name,result['routes']['smart']['status'],flush=True)
    finally:
        shutil.rmtree(out/'build',ignore_errors=True)
    return int(any(r['result']['routes']['smart']['status']!='exact' or r['result']['routes']['smart'].get('sanitizer') for r in report['rows']))


if __name__=='__main__':
    raise SystemExit(main())
