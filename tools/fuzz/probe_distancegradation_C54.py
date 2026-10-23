#!/usr/bin/env python3
"""C54 public Smart Box/Bilateral probes and sanitizer comparisons."""
import argparse
import copy
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import time
sys.dont_write_bytecode = True
from adapters.olmdistancegradation import Adapter, SOURCE
from adapters.public import ROOT
from core import sha, raw_diff
from run import main_checkout, default_worker
from verify_distancegradation_smart_C08 import variant


def matrix(a, mode):
    if mode == 'target':
        yield 'seed105/150', a.generate(105, 150)
        return
    for depth in ((32,) if mode == 'bilateral' else (8, 16, 32)):
      top = {8:255,16:32768,32:1.}[depth]
      fmt = {8:'<4B',16:'<4H',32:'<4f'}[depth]
      for w,h,size in ([(7,3,33),(1,7,392),(7,3,500)] if mode == 'bilateral' else [(7,3,3),(3,1,31),(1,7,501),(23,16,3896)]):
       for owner in (1,2,3):
        for interp in (1,2,3):
         for render in (1,2):
          c=dict(geometry=[w,h],depth=depth,profile='C54-independent',parameters=a.defaults(w,h),input_padding=3,output_padding=5)
          av=[0,top//2 if depth!=32 else .5,top,0,top//4 if depth!=32 else .25,top,0]
          rgb=[top//4,top//2,top*3//4] if depth!=32 else [-.5,2.,.75]
          c['pixels']=b''.join(struct.pack(fmt,av[(x+2*y)%7],*rgb) for y in range(h) for x in range(w))
          values={1:(owner+render)%2,2:owner,3:4,4:3,5:render,6:render%2,7:[255,28,53,238],8:[255,16,160,48],9:interp,11:5 if mode=='bilateral' else 2,12:size}
          for q in c['parameters']:
              if q['slot'] in values:q['value']=values[q['slot']]
          yield f'{depth}/{w}x{h}/size{size}/owner{owner}/interp{interp}/render{render}',c


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--mode',choices=['target','box','bilateral'],required=True)
    p.add_argument('--scratch',type=Path,required=True);p.add_argument('--report',type=Path,required=True)
    p.add_argument('--source',type=Path,default=SOURCE)
    p.add_argument('--before',type=Path);p.add_argument('--limit',type=int)
    p.add_argument('--label');p.add_argument('--allow-existing-mismatch',action='store_true')
    p.add_argument('--case-out',type=Path)
    p.add_argument('--exclude-large-pf16',action='store_true')
    args=p.parse_args();args.scratch=args.scratch.resolve()
    assert args.scratch.is_relative_to(ROOT/'orchestra/state')
    args.scratch.mkdir(parents=True,exist_ok=True)
    os.environ.update(TMPDIR=str(args.scratch),TMP=str(args.scratch),TEMP=str(args.scratch));tempfile.tempdir=str(args.scratch)
    a=Adapter(argparse.Namespace(max_size=256,case_timeout=180,main=main_checkout(),worker=default_worker()))
    source=args.source.read_text();report=dict(mode=args.mode,exclude_large_pf16=args.exclude_large_pf16,source_sha256=sha(source.encode()),rows=[])
    deadline=time.monotonic()+7200
    try:
      with tempfile.TemporaryDirectory(dir=args.scratch) as td:
        td=Path(td);prod=td/'prod';prod.mkdir();report['provenance']=a.prepare(prod,deadline)
        current=variant(a,td/'candidate',deadline,source)
        san=variant(a,td/'san',deadline,source,sanitized=True)
        before=variant(a,td/'before',deadline,args.before.read_text()) if args.before else None
        wd=td/'case';wd.mkdir()
        for index,(label,c) in enumerate(matrix(a,args.mode)):
            if args.limit is not None and index>=args.limit:break
            if args.label and label != args.label:continue
            if args.exclude_large_pf16 and c['depth']==16 and c['parameters'][-1]['value']>2047:continue
            if args.case_out:args.case_out.write_text(json.dumps(dict(c,pixels=c['pixels'].hex()),indent=2)+'\n')
            oracle,reference=a.oracle(c,wd,deadline,'smart')
            start=time.monotonic();status,raw,guards=current.candidate(c,wd,'smart',deadline);seconds=time.monotonic()-start
            sanitized,sr,_=san.candidate(c,wd,'smart',deadline)
            row=dict(label=label,input_sha256=sha(c['pixels']),geometry=c['geometry'],parameters=c['parameters'],oracle=oracle,candidate=status,guards=guards,seconds=seconds,
                sanitized=sanitized,sanitized_equal=status==sanitized and raw==sr,candidate_sha256=sha(raw),oracle_sha256=sha(reference),exact=oracle['status']=='ok' and status['status']=='ok' and raw==reference)
            if before:
                start=time.monotonic();bs,br,_=before.candidate(c,wd,'smart',deadline)
                row.update(before_seconds=time.monotonic()-start,before=bs,before_sha256=sha(br),before_equal=bs==status and br==raw)
            if oracle['status']=='ok' and status['status']=='ok':row['diff']=raw_diff(reference,raw,c['depth'])
            report['rows'].append(row)
            print(index,label,row['exact'],row.get('diff'),flush=True)
            assert row['sanitized_equal'],row
            assert row['exact'] or (args.allow_existing_mismatch and before and row['before_equal']),row
            if before:assert row['before_equal'],row
        report['completed']=True
    finally:
        args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('COMPLETE',len(report['rows']),flush=True)

if __name__=='__main__':main()
