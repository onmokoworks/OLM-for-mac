#!/usr/bin/env python3
"""C10 independent public Smart default-schedule admission probes.

No source-image admission. Diagnostic builds bypass only the small-frame gate.
All inputs are generated deterministically here, including typed extrema.
"""
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
import sys
import tempfile
import time
sys.dont_write_bytecode = True
import run
import triage_olmblur as triage
from adapters import olmblur
from core import raw_diff, sha

WORKER = Path.home()/'.cache/olm-emu/radial_noop_highdepth_reference_20261002/target/release/aex-guest-worker'


def cases(adapter, depths):
    rng = random.Random(10102026)
    geometries = ((1,1),(1,2),(2,1),(1,23),(23,1),(2,3),(5,7),(24,24))
    for depth, geometry, smooth, bias, profile in itertools.product(
            depths, geometries, (1.,62.5,100.), (1,2),
            ('random','edges','opaque','transparent','wide')):
        w,h = geometry
        top = 255 if depth == 8 else 32768
        pixels = bytearray()
        for i in range(w*h):
            if depth in (8,16):
                if profile == 'wide' and depth == 16: top = 65535
                edges = (0,1,top//2,top-1,top)
                rgb = [rng.choice(edges) if profile == 'edges' else rng.randrange(top+1) for _ in range(3)]
                alpha = top if profile == 'opaque' else 0 if profile == 'transparent' else rng.choice(edges)
                pixels.extend(struct.pack('<4B' if depth == 8 else '<4H',alpha,*rgb))
            else:
                edges = (0.,-0.,1.401298464324817e-45,1.1754943508222875e-38,.5,1.)
                rgb = [rng.choice(edges) if profile == 'edges' else rng.uniform(-8.,8.) if profile == 'wide' else rng.random() for _ in range(3)]
                alpha = 1. if profile == 'opaque' else 0. if profile == 'transparent' else rng.choice(edges)
                pixels.extend(struct.pack('<4f',alpha,*rgb))
        params = adapter.defaults(w,h)
        for p in params: p['value'] = {1:5.,2:smooth,3:2,4:bias,5:0}[p['slot']]
        yield dict(geometry=list(geometry),depth=depth,parameters=params,pixels=bytes(pixels),
                   input_padding=7,output_padding=11,profile=profile,rule='default-schedule')
    # Nonfinite input is tested separately: it is not silently counted as finite.
    for geometry,bias in itertools.product(geometries,(1,2)):
        if 32 not in depths: break
        w,h=geometry; params=adapter.defaults(w,h)
        for p in params:p['value']={1:5.,2:100.,3:2,4:bias,5:0}[p['slot']]
        words=(0,0x80000000,0x3f800000,0x7f800000,0xff800000,0x7fc12345,0xffc54321,0x7f812345)
        pixels=b''.join(struct.pack('<4I',rng.choice(words),*[rng.choice(words) for _ in range(3)]) for i in range(w*h))
        yield dict(geometry=list(geometry),depth=32,parameters=params,pixels=pixels,input_padding=3,
                   output_padding=5,profile='nonfinite',rule='default-schedule')


def boundary_cases(adapter):
    for depth, slot, value in itertools.product((8,16,32), (1,), (5.-1/65536,5.+1/65536)):
        params=adapter.defaults(7,5)
        for p in params:
            if p['slot']==slot:p['value']=value
        pixel=struct.pack('<4B',255,1,127,254) if depth==8 else struct.pack('<4H',32768,1,16384,32767) if depth==16 else struct.pack('<4f',1.,.1,.5,.9)
        yield dict(geometry=[7,5],depth=depth,parameters=params,pixels=pixel*35,input_padding=7,output_padding=11,profile='amount-neighbour',rule='negative')
    for depth,(slot,value) in itertools.product((8,16,32), ((3,1),(3,3),(5,1))):
        params=adapter.defaults(7,5)
        for p in params:
            if p['slot']==slot:p['value']=value
        pixel=struct.pack('<4B',255,1,127,254) if depth==8 else struct.pack('<4H',32768,1,16384,32767) if depth==16 else struct.pack('<4f',1.,.1,.5,.9)
        yield dict(geometry=[7,5],depth=depth,parameters=params,pixels=pixel*35,input_padding=3,output_padding=5,profile='tuple-neighbour',rule='negative')
    for channel,word in itertools.product(range(4),(0x80000001,0x3f800001,0x7f7fffff,0x7f800000,0xff800000,0x7fc12345,0x7f812345)):
        pixel=bytearray(struct.pack('<4f',1.,.1,.5,.9));struct.pack_into('<I',pixel,channel*4,word)
        yield dict(geometry=[7,5],depth=32,parameters=adapter.defaults(7,5),pixels=bytes(pixel)*35,input_padding=7,output_padding=11,profile='source-neighbour',rule='negative')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--scratch',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    p.add_argument('--diagnostic',action='store_true')
    p.add_argument('--boundary-only',action='store_true')
    p.add_argument('--depths',type=int,nargs='+',default=[8,16,32])
    p.add_argument('--require-exact',action='store_true')
    p.add_argument('--admitted-depths',type=int,nargs='+',default=[32])
    args=p.parse_args();args.scratch=args.scratch.resolve()
    assert args.scratch.is_relative_to(run.ROOT/'orchestra/state/C10-olmblur-smart-r2')
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
            source=original.read_text()
            anchor=next(line for line in source.splitlines() if 'return "generic-small-fixture";' in line)
            assert source.count(anchor)==1
            olmblur.SOURCE=target/'OLMBlur.cpp'
            olmblur.SOURCE.write_text(source.replace(anchor,'\t// C10 diagnostic gate bypass.').replace('!SmallDefaultPF32Source(input_world)', 'false'))
            for name in ('OLMBlur.h','OLMBlur_Strings.cpp','OLMBlur_Strings.h'):
                shutil.copyfile(original.with_name(name),target/name)
        adapter.binary=triage.build_binary(adapter,build,sanitize=True)
        provenance={'source_sha256':sha(original.read_bytes()),'compiled_source_sha256':sha(olmblur.SOURCE.read_bytes()),
                    'candidate_sha256':sha(adapter.binary.read_bytes()),'aex_sha256':sha(adapter.aex.read_bytes()),
                    'worker_sha256':sha(adapter.worker.read_bytes()),
                    'core_sha256':{str(v.relative_to(run.ROOT)):sha(v.read_bytes()) for v in olmblur.CORES}}
        def one(item):
            i,c=item
            with tempfile.TemporaryDirectory(prefix='case_',dir=build) as name:
                directory=Path(name)
                oracle,reference=adapter.oracle(c,directory,deadline,'smart')
                result,raw,guards=adapter.candidate(c,directory,'smart',deadline)
            status=result['status']
            if status=='ok':status=('exact' if reference==raw else 'mismatch') if oracle['status']=='ok' else 'uncompared'
            pvals={p['slot']:p['value'] for p in c['parameters']}
            domain=c['depth']!=32 or all(0.<=v<=1. for v in struct.unpack('<'+'f'*(len(c['pixels'])//4),c['pixels']))
            baseline=c['depth'] in (8,16) and (c['geometry']==[1,1] or pvals[3]==1) and pvals[5]==0
            admitted=(pvals[1]==5. and pvals[3]==2 and pvals[5]==0 and c['depth'] in args.admitted_depths and domain) or baseline
            return {'index':i,'expected_admitted':admitted,'case':{k:v for k,v in c.items() if k!='pixels'},'input_sha256':sha(c['pixels']),
                    'oracle':dict(oracle,raw_sha256=sha(reference)), 'status':status,
                    'candidate':dict(result,raw_sha256=sha(raw)), 'guards':guards,
                    'diff':raw_diff(reference,raw,c['depth']) if status=='mismatch' else None}
        with ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(one,enumerate(boundary_cases(adapter) if args.boundary_only else cases(adapter,args.depths))))
    counts=dict(Counter(r['status'] for r in rows))
    by_depth={str(d):dict(Counter(r['status'] for r in rows if r['case']['depth']==d)) for d in args.depths}
    report={'schema':'olmblur-small-C10/1','diagnostic':args.diagnostic,'provenance':provenance,
            'counts':counts,'by_depth':by_depth,'cases':rows}
    args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(counts,by_depth)
    if args.require_exact:
        assert all(r['status']==('exact' if args.diagnostic or r['expected_admitted'] else 'refusal') for r in rows)


if __name__=='__main__':main()
