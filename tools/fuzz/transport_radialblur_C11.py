#!/usr/bin/env python3
"""Find a PNG-lossless PF32 witness for the retained trace CLI, without rounding its oracle."""
import argparse
import json
import os
from pathlib import Path
import random
import shutil
import struct
import sys
import time
from types import SimpleNamespace
sys.dont_write_bytecode=True
from adapters.radialblur import Adapter, public
from core import evaluate
from verify_radialblur_smart_C06 import ROOT, MAIN, WORKER


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--fixture',type=Path,required=True)
    ap.add_argument('--source',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args();out=args.output.resolve()
    assert out.is_relative_to(ROOT/'orchestra/state/C11-radial-smart-r2')
    out.mkdir(parents=True,exist_ok=False)
    os.environ.update(TMPDIR=str(out),TMP=str(out),TEMP=str(out))
    public.SOURCE=args.source.resolve()
    adapter=Adapter(SimpleNamespace(main=MAIN,worker=WORKER,max_size=256,case_timeout=60))
    adapter.routes=('smart',);adapter.oracle_routes={'smart':'smart'}
    deadline=time.monotonic()+1200;provenance=adapter.prepare(out,deadline)
    saved=json.loads(args.fixture.read_text())['rows'][0]
    base=dict(saved['case'],pixels=bytes.fromhex(saved['input_hex']))
    assert base['depth']==32
    values=[v for v, in struct.iter_unpack('<f',base['pixels'])]
    rng=random.Random(1131);rows=[];attempts=[]
    for n in range(65):
        if n==0:
            pixels=b''.join(struct.pack('<f',round(v*255)/255) for v in values)
        else:
            pixel=struct.pack('<4f',128/255,*[rng.randrange(256)/255 for _ in range(3)])
            pixels=pixel*(len(values)//4)
        case=dict(base,pixels=pixels)
        result=evaluate(adapter,case,out,deadline)
        attempts.append(dict(index=n,result=result))
        if result['routes']['smart']['status']=='mismatch':
            rows.append(dict(index=base['index'],case={k:v for k,v in case.items() if k!='pixels'},
                             input_hex=pixels.hex(),reduced=result,expected_smart_sha256=result['oracle']['raw_sha256']))
            break
    report=dict(provenance=provenance,rows=rows,attempts=attempts)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    shutil.rmtree(out/'build')
    print('RESULT',len(attempts),'attempts',len(rows),'traceable witnesses')
    return not rows


if __name__=='__main__':raise SystemExit(main())
