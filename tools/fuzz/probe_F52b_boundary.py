#!/usr/bin/env python3
"""Record the retained F52 oracle's output-rectangle allocation boundary."""
import json
from pathlib import Path
import time
from types import SimpleNamespace

from adapters.olmcolorkey import Adapter
from core import sha
from run import ROOT, main_checkout


def main():
    scratch = ROOT/'orchestra/state/F52b-geometry-plumbing-all-plugins/oracle-boundary'
    scratch.mkdir(parents=True,exist_ok=True)
    worker = Path.home()/'.cache/olm-emu/worker-F52-geom/aex-guest-worker'
    a = Adapter(SimpleNamespace(max_size=256,case_timeout=10,main=main_checkout(),worker=worker))
    a.env.update(TMPDIR=str(scratch),TMP=str(scratch),TEMP=str(scratch))
    case = a.generate(1,0)
    case.update(geometry=[1,1],depth=8,pixels=bytes([255,32,64,128]),parameters=a.defaults(1,1))
    rows = []
    for rect in ([0,0,1,1],[0,0,2,1]):
        a.session_arguments = lambda case,directory: ['--request-rect',','.join(map(str,rect))]
        result,raw = a.oracle(case,scratch,time.monotonic()+30,'smart')
        rows.append(dict(request=rect,result=result,output_sha256=sha(raw),output_bytes=len(raw)))
    print(json.dumps(dict(worker_sha256=sha(worker.read_bytes()),rows=rows),indent=2))
    assert rows[0]['result']['status']=='ok', rows[0]
    assert rows[1]['result']['status']=='reject', rows[1]
    assert 'rectangle outside sampled world' in rows[1]['result']['diagnostic']


if __name__ == '__main__':
    main()
