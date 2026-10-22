#!/usr/bin/env python3
"""Independent typed public-route radius boundary matrix, with both revisions.

All arithmetic uses actual production workers. The small-frame gate is bypassed
in both diagnostic builds, so each row compares the general operation itself.
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
import subprocess
import sys
import tempfile
import time
sys.dont_write_bytecode=True
import run
import triage_olmblur as triage
from adapters import olmblur
from core import raw_diff,sha
WORKER=Path.home()/'.cache/olm-emu/radial_noop_highdepth_reference_20261002/target/release/aex-guest-worker'


def cases(adapter,depth):
    rng=random.Random(12102026)
    amounts=(1.,1.+2**-23,3.-2**-22,3.,3.+2**-22,5.,5.+2**-21,19.659519213989434,30.,1000.)
    for i,(geometry,amount,repeat,bias) in enumerate(itertools.product(((1,1),(7,5),(25,1),(1,25),(25,7),(7,25)),amounts,(1,2,3,4,9,10),(1,2))):
        w,h=geometry;profile=('random','edge','opaque','transparent')[i%4];pixels=bytearray()
        for pixel in range(w*h):
            if depth in (8,16):
                top=255 if depth==8 else 65535
                values=(0,1,top//2,top//2+1,top-1,top)
                rgb=[rng.choice(values) if profile=='edge' else rng.randrange(top+1) for _ in range(3)]
                alpha=0 if profile=='transparent' else top if profile=='opaque' else rng.choice(values)
                pixels.extend(struct.pack('<4B' if depth==8 else '<4H',alpha,*rgb))
            else:
                values=(0.,-0.,2**-149,2**-126,.5,1.)
                rgb=[rng.choice(values) if profile=='edge' else rng.random() for _ in range(3)]
                alpha=0. if profile=='transparent' else 1. if profile=='opaque' else rng.choice(values)
                pixels.extend(struct.pack('<4f',alpha,*rgb))
        params=adapter.defaults(w,h)
        for p in params:p['value']={1:amount,2:(1.,62.5,100.)[i%3],3:repeat,4:bias,5:0}[p['slot']]
        yield dict(index=i,geometry=list(geometry),depth=depth,parameters=params,pixels=bytes(pixels),input_padding=7,output_padding=11,profile=profile)


def build(a,work,revision,diagnostic=True):
    original=olmblur.SOURCE;cores=olmblur.CORES
    target=work/'variant/mac/OLMBlur';target.mkdir(parents=True);cr=work/'variant/core';cr.mkdir()
    for f in (run.ROOT/'core').iterdir():
        if f.is_file():(cr/f.name).symlink_to(f)
    for f in cores:
        if revision:
            (cr/f.name).unlink();(cr/f.name).write_bytes(subprocess.check_output(['git','show',revision+':core/'+f.name]))
    for name in ('OLMBlur.h','OLMBlur_Strings.cpp','OLMBlur_Strings.h'):shutil.copyfile(original.with_name(name),target/name)
    source=(subprocess.check_output(['git','show',revision+':mac/OLMBlur/OLMBlur.cpp']).decode() if revision else original.read_text())
    anchor=next(l for l in source.splitlines() if 'return "generic-small-fixture";' in l)
    if diagnostic:source=source.replace(anchor,'\t// C12 diagnostic gate bypass.').replace('!SmallDefaultPF32Source(input_world)','false')
    olmblur.SOURCE=target/'OLMBlur.cpp';olmblur.SOURCE.write_text(source);olmblur.CORES=[cr/f.name for f in cores]
    binary=triage.build_binary(a,work,sanitize=True)
    provenance={'revision':revision,'compiled_source_sha256':sha(source.encode()),'core_sha256':{f.name:sha(f.read_bytes()) for f in olmblur.CORES},'candidate_sha256':sha(binary.read_bytes())}
    olmblur.SOURCE=original;olmblur.CORES=cores
    return binary,provenance


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--scratch',type=Path,required=True);p.add_argument('--report',type=Path,required=True)
    p.add_argument('--before',required=True);p.add_argument('--depth',type=int,choices=(8,16,32),required=True);p.add_argument('--require-exact',action='store_true');p.add_argument('--diagnostic-after',action='store_true');p.add_argument('--single-decay-only',action='store_true');p.add_argument('--source-boundaries',action='store_true')
    args=p.parse_args();s=args.scratch.resolve();assert s.is_relative_to(run.ROOT/'orchestra/state/C12-olmblur-smart-r3')
    s.mkdir(parents=True,exist_ok=True);os.environ.update(TMPDIR=str(s),TMP=str(s),TEMP=str(s))
    a=olmblur.Adapter(argparse.Namespace(max_size=256,case_timeout=60,main=run.main_checkout(),worker=WORKER))
    a.env.update(TMPDIR=str(s),TMP=str(s),TEMP=str(s),ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
    with tempfile.TemporaryDirectory(prefix='radius_',dir=s) as td:
        work=Path(td);old,op=build(a,work/'before',args.before,diagnostic=not args.source_boundaries);new,np=build(a,work/'after',None,diagnostic=args.diagnostic_after)
        # Each thread has independent adapters/env and directories; binaries are read-only.
        def one(c):
            adapter=olmblur.Adapter(a.args) if hasattr(a,'args') else olmblur.Adapter(argparse.Namespace(max_size=256,case_timeout=60,main=run.main_checkout(),worker=WORKER))
            adapter.env=dict(a.env)
            with tempfile.TemporaryDirectory(prefix='case_',dir=work) as cd:
                directory=Path(cd);deadline=time.monotonic()+180
                oracle,reference=adapter.oracle(c,directory,deadline,'smart');assert oracle['status']=='ok',oracle
                row={'case':{k:v for k,v in c.items() if k!='pixels'},'input_sha256':sha(c['pixels']),'oracle':dict(oracle,raw_sha256=sha(reference))}
                for label,binary in [('before',old),('after',new)]:
                    adapter.binary=binary;result,raw,guards=adapter.candidate(c,directory,'smart',deadline)
                    status=('exact' if raw==reference else 'mismatch') if result['status']=='ok' else result['status']
                    row[label]={'status':status,'result':result,'raw_sha256':sha(raw),'diff':raw_diff(reference,raw,c['depth']) if status=='mismatch' else None}
                return row
        selected=[c for c in cases(a,args.depth) if not args.single_decay_only or next(p['value'] for p in c['parameters'] if p['slot']==3)<=2]
        if args.source_boundaries:
            import copy
            from verify_blur_small_C10 import boundary_cases
            selected=[]
            for c in boundary_cases(a):
                if c['profile']!='source-neighbour':continue
                for repeat in (1,2):
                    c=copy.deepcopy(c)
                    for param in c['parameters']:
                        if param['slot']==1:param['value']=9.406514031388419
                        if param['slot']==3:param['value']=repeat
                    c['index']=len(selected);selected.append(c)
        with ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(one,selected))
    transitions=dict(Counter(r['before']['status']+' -> '+r['after']['status'] for r in rows))
    report={'schema':'olmblur-radius-matrix-C12/1','depth':args.depth,'provenance':{'before':op,'after':np,'aex_sha256':sha(a.aex.read_bytes()),'worker_sha256':sha(WORKER.read_bytes())},'transitions':transitions,'rows':rows}
    args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(transitions)
    if args.source_boundaries:
        assert all(r['before']['status']==r['after']['status']=='refusal' for r in rows)
        return
    assert all(r['after']['status'] in ('exact','mismatch') for r in rows),'sanitizer/refusal/oracle failure'
    assert all(r['before']['status']!='exact' or r['after']['status']=='exact' for r in rows),'base-exact regression'
    if args.require_exact:assert all(r['after']['status']=='exact' for r in rows)

if __name__=='__main__':main()
