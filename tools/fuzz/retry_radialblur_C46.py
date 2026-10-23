#!/usr/bin/env python3
"""Retry original Smart outputs without changing the retained worker or inputs."""
import argparse
import json
import os
from pathlib import Path
import sys
import time
from types import SimpleNamespace
sys.dont_write_bytecode=True
from adapters.radialblur import Adapter,ROOT
from core import sha


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--seed',type=int,default=1)
    p.add_argument('--indices',default='117')
    p.add_argument('--seconds',type=int,default=120)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    out=args.output.resolve()
    assert out.is_relative_to(ROOT/'orchestra/state/C46-radial-smart-r8')
    out.mkdir(parents=True,exist_ok=False)
    os.environ.update(TMPDIR=str(out),TMP=str(out),TEMP=str(out))
    w=Path.home()/'.cache/olm-emu/worker-F46-pow/aex-guest-worker'
    adapter=Adapter(SimpleNamespace(main=ROOT.parent.parent,worker=w,max_size=256,case_timeout=args.seconds))
    rows=[]
    for index in map(int,args.indices.split(',')):
        c=adapter.generate(args.seed,index)
        start=time.monotonic()
        actual,raw=adapter.oracle(c,out,start+args.seconds+30,'smart')
        rows.append(dict(seed=args.seed,index=index,input_sha256=sha(c['pixels']),elapsed=time.monotonic()-start,result=actual,raw_sha256=sha(raw) if raw else None))
    report=dict(worker_sha256=sha(w.read_bytes()),rows=rows)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)

if __name__=='__main__': main()
