#!/usr/bin/env python3
"""Independent public Smart matrix for the non-Legacy single-pass/singleton rules."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import itertools
import json
import os
from pathlib import Path
import random
import shutil
import struct
import subprocess
import sys
import tempfile
import time
sys.dont_write_bytecode = True
import run
import triage_olmblur as triage
from adapters import olmblur
from core import raw_diff, sha

BASE = '53715716482c3278e9af0771fad16e30db7261d0'
WORKER = Path.home()/'.cache/olm-emu/radial_frozen_reference_bd878da/target/release/aex-guest-worker'


def cases(adapter):
    rng = random.Random(170017)
    for depth,geometry,amount,smooth,bias,profile in itertools.product(
            (8,16), ((1,1),(1,13),(13,1),(7,5),(24,24)),
            (1.,5.,29.999984741210938,1000.), (1.,100.), (1,2), ('mixed','opaque','wide16')):
        if depth==8 and profile=='wide16':continue
        w,h=geometry;top=255 if depth==8 else 65535 if profile=='wide16' else 32768
        pixels=b''.join(struct.pack('<4B' if depth==8 else '<4H',
                top if profile=='opaque' else (0,1,top)[i%3],
                *[rng.choice((0,1,top//2,top-1,top,rng.randrange(top+1))) for _ in range(3)])
                for i in range(w*h))
        params=adapter.defaults(w,h)
        for p in params:p['value']={1:amount,2:smooth,3:1,4:bias,5:0}[p['slot']]
        yield dict(geometry=list(geometry),depth=depth,parameters=params,pixels=pixels,
                   input_padding=7,output_padding=11,profile=profile,rule='singlepass')
    # Repeated singleton covers the no-neighbour geometry independently of
    # the single-pass branch, including fractional Amount and both alpha paths.
    for depth,amount,smooth,repeat,bias,alpha in itertools.product(
            (8,16),(1.,5.,29.999984741210938,1000.),(1.,100.),(2,10),(1,2),(0,1,2)):
        top=255 if depth==8 else 65535
        params=adapter.defaults(1,1)
        for p in params:p['value']={1:amount,2:smooth,3:repeat,4:bias,5:0}[p['slot']]
        yield dict(geometry=[1,1],depth=depth,parameters=params,
                   pixels=struct.pack('<4B' if depth==8 else '<4H',(0,1,top)[alpha],0,top//2,top),
                   input_padding=3,output_padding=5,profile='edges',rule='singleton')


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--scratch',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    p.add_argument('--diagnostic',action='store_true')
    p.add_argument('--rule',choices=('singlepass','singleton'),default='singlepass')
    args=p.parse_args();args.scratch=args.scratch.resolve()
    assert args.scratch.is_relative_to(run.ROOT/'orchestra/state/F17-fuzz-per-route-oracle')
    args.scratch.mkdir(parents=True,exist_ok=True)
    os.environ.update(TMPDIR=str(args.scratch),TMP=str(args.scratch),TEMP=str(args.scratch))
    adapter=olmblur.Adapter(argparse.Namespace(max_size=256,case_timeout=20,main=run.main_checkout(),worker=WORKER))
    adapter.env.update(TMPDIR=str(args.scratch),TMP=str(args.scratch),TEMP=str(args.scratch),
        ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
    deadline=time.monotonic()+3600
    original=olmblur.SOURCE
    with tempfile.TemporaryDirectory(prefix='matrix_',dir=args.scratch) as td:
        build=Path(td)
        if args.diagnostic:
            target=build/'variant/mac/OLMBlur';target.mkdir(parents=True)
            (build/'variant/core').symlink_to(run.ROOT/'core',target_is_directory=True)
            body=subprocess.check_output(['git','show',BASE+':mac/OLMBlur/OLMBlur.cpp']).decode()
            anchor='\tif (width <= 24 && height <= 24) return "generic-small-fixture";'
            assert body.count(anchor)==1
            olmblur.SOURCE=target/'OLMBlur.cpp'
            olmblur.SOURCE.write_text(body.replace(anchor,'\t// F17 matrix gate bypass.'))
            for name in ('OLMBlur.h','OLMBlur_Strings.cpp','OLMBlur_Strings.h'):
                shutil.copyfile(original.with_name(name),target/name)
        adapter.binary=triage.build_binary(adapter,build,sanitize=True)
        provenance={'source_sha256':sha(olmblur.SOURCE.read_bytes()),'candidate_sha256':sha(adapter.binary.read_bytes()),
                    'aex_sha256':sha(adapter.aex.read_bytes()),'worker_sha256':sha(adapter.worker.read_bytes())}
        def one(item):
            i,c=item
            with tempfile.TemporaryDirectory(prefix='case_',dir=build) as name:
                directory=Path(name)
                oracle,reference=adapter.oracle(c,directory,deadline,'smart')
                result,raw,guards=adapter.candidate(c,directory,'smart',deadline)
            expected=c['rule']!='negative' and (args.rule=='singlepass' or c['geometry']==[1,1])
            status=result['status']
            if status=='ok':status=('exact' if reference==raw else 'mismatch') if oracle['status']=='ok' else 'uncompared'
            return {'index':i,'case':{k:v for k,v in c.items() if k!='pixels'},'input_sha256':sha(c['pixels']),
                    'expected_admitted':expected,'oracle':dict(oracle,raw_sha256=sha(reference)),
                    'status':status,'candidate':dict(result,raw_sha256=sha(raw)), 'guards':guards,
                    'diff':raw_diff(reference,raw,c['depth']) if status=='mismatch' else None}
        matrix=list(cases(adapter))
        if not args.diagnostic:
            for depth,geometry,repeat,legacy in itertools.product((8,16,32),((1,1),(7,5)),(1,2),(0,1)):
                if depth in (8,16) and not legacy and (repeat==1 or geometry==(1,1)):continue
                c=adapter.generate(17,len(matrix))
                c.update(geometry=list(geometry),depth=depth,parameters=adapter.defaults(*geometry),
                         pixels=(bytes((255,1,127,254)) if depth==8 else struct.pack('<4H',32768,1,16384,32767)
                                 if depth==16 else struct.pack('<4f',1.,.1,.5,.9))*(geometry[0]*geometry[1]),rule='negative')
                for param in c['parameters']:
                    param['value']={1:5.,2:100.,3:repeat,4:1,5:legacy}[param['slot']]
                matrix.append(c)
        with ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(one,enumerate(matrix)))
    counts=Counter(r['status'] for r in rows)
    by_rule={rule:dict(Counter(r['status'] for r in rows if r['case']['rule']==rule)) for rule in ('singlepass','singleton','negative')}
    report={'schema':'olmblur-small-matrix/1','diagnostic':args.diagnostic,'rule':args.rule,
            'provenance':provenance,'counts':dict(counts),'by_rule':by_rule,'cases':rows}
    args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(dict(counts),by_rule)
    if not args.diagnostic:
        assert all(r['status']==('exact' if r['expected_admitted'] else 'refusal') for r in rows)


if __name__=='__main__':main()
