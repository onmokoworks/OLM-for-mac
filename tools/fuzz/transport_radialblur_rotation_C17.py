#!/usr/bin/env python3
"""Seek a lossless PNG-transport PF16 Rotation mismatch at the center boundary."""
import argparse, json, os, random, shutil, struct, sys, time
from pathlib import Path
from types import SimpleNamespace
sys.dont_write_bytecode=True
from adapters.radialblur import Adapter, public
from core import evaluate, sha
from verify_radialblur_smart_C06 import ROOT, MAIN, WORKER
from verify_radialblur_centers_C17 import cases

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--campaign-index',type=int)
    args=ap.parse_args();out=args.output.resolve()
    assert out.is_relative_to(ROOT/'orchestra/state/C17-radial-smart-r3')
    out.mkdir(parents=True,exist_ok=False);os.environ.update(TMPDIR=str(out),TMP=str(out),TEMP=str(out))
    public.SOURCE=args.source.resolve()
    adapter=Adapter(SimpleNamespace(main=MAIN,worker=WORKER,max_size=256,case_timeout=60));adapter.routes=('smart',);adapter.oracle_routes={'smart':'smart'}
    deadline=time.monotonic()+2400;report=dict(provenance=adapter.prepare(out,deadline),attempts=[])
    base=list(cases(adapter))[30] if args.campaign_index is None else adapter.generate(1,args.campaign_index);rng=random.Random(1730)
    for n in range(65):
        packed=(bytes(round(v/32768*255) for v, in struct.iter_unpack('<H',base['pixels'])) if n==0 else bytes(rng.randrange(256) for _ in range(len(base['pixels'])//2)))
        pixels=b''.join(struct.pack('<H',(v*32768+127)//255) for v in packed)
        case=dict(base,pixels=pixels)
        result=evaluate(adapter,case,out,deadline)
        report['attempts'].append(dict(index=n,result=result))
        if n == 0:
            report['control'] = dict(case={k:v for k,v in case.items() if k!='pixels'},input_hex=pixels.hex(),input_sha256=sha(pixels),result=result)
        print(n,result['routes']['smart']['status'],flush=True)
        if result['routes']['smart']['status']=='mismatch':
            report.update(case={k:v for k,v in case.items() if k!='pixels'},input_hex=pixels.hex(),input_sha256=sha(pixels),result=result)
            break
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');shutil.rmtree(out/'build')
if __name__=='__main__':main()
