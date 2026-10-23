#!/usr/bin/env python3
"""Independent missing-layer Type3/NV0 matrix, original F46 and sanitized SDK."""
import argparse
from collections import Counter
import json
import os
import shutil
import time
from types import SimpleNamespace
import random
import struct
import sys
from pathlib import Path
sys.dont_write_bytecode = True
import verify_radialblur_smart_C06 as verify


def cases(adapter, matrix=None):
    for w, h in ((3, 5), (7, 1), (5, 3)):
        for depth in (8, 16, 32):
            rng = random.Random(46100 + w * 100 + depth)
            values = [[rng.choice([0, 16384, 32768]), *[rng.randrange(32769) for _ in range(3)]] for i in range(w*h)]
            pixels = b''.join(struct.pack('<4B', *[v*255//32768 for v in row]) if depth == 8 else struct.pack('<4H', *row) if depth == 16 else struct.pack('<4f', *[v/32768 for v in row]) for row in values)
            for blur in (1, 2):
                for size in (0., 50.):
                    for fade in (0, 3):
                        for repeat in (0, 1):
                            params = adapter.defaults(w, h)
                            changes = {1:blur, 4:7, 10:3, (6 if matrix == 'offsets' else 7):fade, (12 if matrix == 'offsets' else 13):fade, 15:repeat, 22:size, 24:0., 25:3}
                            for p in params:
                                if p['slot'] in changes: p['value'] = changes[p['slot']]
                            yield dict(seed=46100, index=0, geometry=[w,h], depth=depth, profile='sdr', parameters=params, pixels=pixels, input_padding=0, output_padding=0)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source',type=Path,default=verify.public.SOURCE)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--independent',action='store_true')
    ap.add_argument('--matrix',choices=['fade','offsets'],default='fade')
    args=ap.parse_args()
    out=args.output.resolve()
    assert out.is_relative_to(verify.ROOT/'orchestra/state/C46-radial-smart-r8')
    out.mkdir(parents=True,exist_ok=False)
    os.environ.update(TMPDIR=str(out),TMP=str(out),TEMP=str(out),OLM_RADIAL_CANDIDATE_SANITIZE='1')
    verify.public.SOURCE=args.source.resolve()
    worker=Path.home()/'.cache/olm-emu/worker-F46-pow/aex-guest-worker'
    adapter=verify.Adapter(SimpleNamespace(main=verify.MAIN,worker=worker,max_size=256,case_timeout=30))
    deadline=time.monotonic()+3600
    report=dict(provenance=adapter.prepare(out,deadline),matrix=args.matrix,rows=[],failures=[])
    work=out/'case';work.mkdir()
    counts=Counter()
    for index,case in enumerate(cases(adapter,args.matrix)):
        oracle,reference=adapter.oracle(case,work,deadline,'smart')
        row=dict(index=index,case={k:v for k,v in case.items() if k!='pixels'},input_sha256=verify.sha(case['pixels']),oracle=oracle,layouts=[])
        for ip,op in ((0,0),(1,5),(3,11)):
            result,raw,guards=adapter.candidate(dict(case,input_padding=ip,output_padding=op),work,'smart',deadline)
            status=result['status']
            if status=='ok': status=('exact' if raw==reference else 'mismatch') if oracle['status']=='ok' else 'uncompared'
            entry=dict(input_padding=ip,output_padding=op,result=result,status=status,guards=guards,raw_sha256=verify.sha(raw),clean=not result.get('sanitizer'))
            if status=='mismatch':entry['diff']=verify.raw_diff(reference,raw,case['depth'])
            if status not in ('exact','uncompared') or not entry['clean']:report['failures'].append([index,ip,status])
            counts[status]+=1;row['layouts'].append(entry)
        report['rows'].append(row)
        if (index+1)%24==0: print(index+1,dict(counts),flush=True)
    report['counts']=dict(counts)
    report['status']='fail' if report['failures'] else 'pass-comparable-only'
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    shutil.rmtree(out/'build')
    print(report['status'],dict(counts),flush=True)
    return bool(report['failures'])

if __name__ == '__main__':
    raise SystemExit(main())
