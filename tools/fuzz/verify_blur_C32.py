#!/usr/bin/env python3
"""C32 independent PF32 admission matrix; F32 oracle, serial sanitized builds."""
import argparse
from collections import Counter
import itertools
import json
import os
from pathlib import Path
import random
import struct
import sys
import tempfile
import time
sys.dont_write_bytecode = True
import run
from adapters import olmblur
from core import raw_diff, sha
import verify_blur_legacy_C15 as legacy
from verify_blur_retained_C12 import verify as retained


def cases(a, mode):
    rng = random.Random(32431026)
    if mode == 'outside':
        for i,(bits,channel,old) in enumerate(itertools.product((0x41800001,0xc1800001,0x7f7fffff,0xff7fffff),range(4),(0,1))):
            params=a.defaults(3,5)
            for p in params:
                if p['slot']==5:p['value']=old
            data=bytearray(struct.pack('<4f',1.,.25,.5,.75)*15)
            struct.pack_into('<I',data,channel*4,bits)
            yield dict(index=i,geometry=[3,5],depth=32,parameters=params,pixels=bytes(data),input_padding=7,output_padding=11,profile='outside-finite-domain')
        return
    if mode == 'legacy':
        for c in legacy.cases(a, 32):
            edges = (-16., -1., -2**-126, -2**-149, -0., 0., 2**-149, 2**-126, 1., 16.)
            c['pixels'] = b''.join(struct.pack('<4f', *[rng.choice(edges) if c['profile'] == 'edge' else rng.uniform(-16,16) for _ in range(4)]) for _ in range(c['geometry'][0]*c['geometry'][1]))
            yield c
    else:
        words = (0, 0x80000000, 0x7f800000, 0xff800000, 0x7fc12345, 0xffc12346, 0x7fa12345, 0xffa12346)
        for i,(geometry,amount,repeat,bias,old) in enumerate(itertools.product(((1,1),(7,5),(1,25),(25,1)), (1.,3.000000238418579,5.,1000.), (1,3,10), (1,2), (0,1))):
            params=a.defaults(*geometry)
            for p in params: p['value']={1:amount,2:(1.,62.5,100.)[i%3],3:repeat,4:bias,5:old}[p['slot']]
            data=b''.join(struct.pack('<I',rng.choice(words)) for _ in range(4*geometry[0]*geometry[1]))
            yield dict(index=2*i,geometry=list(geometry),depth=32,parameters=params,pixels=data,input_padding=7,output_padding=11,profile='signed-inf-qnan-snan')
            mixed=words+(0x3f800000,0x3f000000,0x41800000,0xc1800000,1,0x80000001)
            data=b''.join(struct.pack('<I',rng.choice(mixed)) for _ in range(4*geometry[0]*geometry[1]))
            yield dict(index=2*i+1,geometry=list(geometry),depth=32,parameters=params,pixels=data,input_padding=7,output_padding=11,profile='mixed-finite-nonfinite')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--scratch',type=Path,required=True);p.add_argument('--report',type=Path,required=True)
    p.add_argument('--before',required=True);p.add_argument('--mode',choices=('legacy','nonfinite','outside'),required=True)
    p.add_argument('--gate-off',action='store_true');p.add_argument('--require-exact',action='store_true')
    p.add_argument('--legacy-value',type=int,choices=(0,1))
    args=p.parse_args();s=args.scratch.resolve();assert s.is_relative_to(run.ROOT/'orchestra/state')
    s.mkdir(parents=True,exist_ok=True);os.environ.update(TMPDIR=str(s),TMP=str(s),TEMP=str(s))
    worker=Path('/Users/onmk/.cache/olm-emu/worker-F32-deep/aex-guest-worker')
    a=olmblur.Adapter(argparse.Namespace(max_size=256,case_timeout=180,main=run.main_checkout(),worker=worker))
    a.env.update(TMPDIR=str(s),TMP=str(s),TEMP=str(s),ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
    rows=[]
    with tempfile.TemporaryDirectory(prefix='C32_matrix_',dir=s) as td:
        work=Path(td)
        for label in ('before','after'):
            (work/label/'variant').mkdir(parents=True)
            (work/label/'variant/ucrtmath').symlink_to(run.ROOT/'ucrtmath',target_is_directory=True)
        old,op=legacy.build(a,work/'before',args.before,diagnostic=False)
        new,np=legacy.build(a,work/'after',None,diagnostic=args.gate_off)
        for c in cases(a,args.mode):
            if args.legacy_value is not None and next(v['value'] for v in c['parameters'] if v['slot']==5)!=args.legacy_value:
                continue
            with tempfile.TemporaryDirectory(prefix='case_',dir=work) as cd:
                d=Path(cd);deadline=time.monotonic()+360
                oracle,reference=a.oracle(c,d,deadline,'smart');assert oracle['status']=='ok',oracle
                row={'case':{k:v for k,v in c.items() if k!='pixels'},'input_sha256':sha(c['pixels']),'oracle':oracle}
                for label,binary in (('before',old),('after',new)):
                    a.binary=binary;r,raw,guards=a.candidate(c,d,'smart',deadline)
                    status=('exact' if raw==reference else 'mismatch') if r['status']=='ok' else r['status']
                    row[label]={'status':status,'raw_sha256':sha(raw),'result':r,'guards':guards,'diff':raw_diff(reference,raw,32) if status=='mismatch' else None}
                rows.append(row)
                if c['index']%100==0:print('progress',c['index'],row['after']['status'],flush=True)
    report={'mode':args.mode,'gate_off':args.gate_off,'provenance':{'before':op,'after':np,'worker_sha256':sha(worker.read_bytes()),'aex_sha256':sha(a.aex.read_bytes())},'transitions':dict(Counter(r['before']['status']+' -> '+r['after']['status'] for r in rows)),'rows':rows,'retained':retained(s)}
    args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(report['transitions'],flush=True)
    if args.mode=='outside':
        assert all(r['before']['status']==r['after']['status']=='refusal' for r in rows)
    else:
        assert all(r['after']['status'] in ('exact','mismatch') for r in rows)
    assert all(r['before']['raw_sha256']==r['after']['raw_sha256'] for r in rows if r['before']['status']=='exact')
    assert report['retained']['status']['status']=='ok' and not report['retained']['stderr']
    assert len(report['retained']['lines'])==80 and all('exact=1' in x for x in report['retained']['lines'])
    if args.require_exact:assert all(r['after']['status']=='exact' for r in rows)

if __name__=='__main__':main()
