#!/usr/bin/env python3
"""Reproduce C03 before/after Smart regressions, sanitizer runs and typed matrix."""
from __future__ import annotations
import argparse
from collections import Counter
import copy
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import time
sys.dont_write_bytecode=True
from adapters.olmdistancegradation import Adapter,SOURCE,SHIM_DIR,FIELDGEN
from adapters.public import ROOT,replace_once
from core import sha,raw_diff,load_corpus
from run import main_checkout,default_worker


def variant(base,path,deadline,source=None,sanitized=False):
    path.mkdir();a=copy.copy(base);a.env=dict(base.env);a.binary,_=a.build(path,deadline)
    if source is not None:
        source=source.replace('#include "OLMDistanceGradation.h"','#include "'+str(SOURCE.with_suffix('.h'))+'"').replace('"../../core/','"'+str(ROOT/'core')+'/')
        cpp=path/'candidate.cpp';cpp.write_text(source);host=path/'host.cpp';host.write_text(replace_once(host.read_text(),str(SOURCE),str(cpp)))
    flags=['-fsanitize=address,undefined','-fno-sanitize-recover=all'] if sanitized else []
    a.compile(['clang++','-std=c++17','-O2','-fno-fast-math','-ffp-contract=off',*flags,'-I',SHIM_DIR,path/'host.cpp',FIELDGEN,'-o',a.binary],deadline)
    a.env.update(ASAN_OPTIONS='detect_leaks=0',UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
    return a


def matrix(a):
    for depth in (8,16,32):
      top={8:255,16:32768,32:1.0}[depth];fmt={8:'<4B',16:'<4H',32:'<4f'}[depth]
      for geometry in ([3,1],[1,3],[7,3]):
       for low in (False,True):
        n=geometry[0]*geometry[1];av=[0,(1 if depth!=32 else 0.0001) if low else top/2,top]
        colors=(.25,.5,.75) if depth==32 else (top//4,top//2,top*3//4)
        pixels=b''.join(struct.pack(fmt,av[i%3] if depth==32 else int(av[i%3]),*colors) for i in range(n))
        for inout in (1,2,3):
         for invert in (0,1):
          for interp in (1,2,3):
           c=dict(geometry=geometry,depth=depth,profile='sdr',parameters=a.defaults(*geometry),pixels=pixels,input_padding=3,output_padding=5)
           values={1:invert,2:inout,3:4,4:3,5:2,6:0,9:interp}
           for p in c['parameters']:
            if p['slot'] in values:p['value']=values[p['slot']]
           yield f'{depth}/{geometry}/low{low}/inout{inout}/invert{invert}/interp{interp}',c



def cutoff_matrix(a):
    """Independent ownership cutoff neighbors, colors, owners and backgrounds."""
    below=struct.unpack('<f',struct.pack('<I',0x38d1b716))[0]
    at=struct.unpack('<f',struct.pack('<I',0x38d1b717))[0]
    above=struct.unpack('<f',struct.pack('<I',0x38d1b718))[0]
    for depth in (8,16,32):
      top={8:255,16:32768,32:1.0}[depth]
      fmt={8:'<4B',16:'<4H',32:'<4f'}[depth]
      alphas={8:[0,1,2,128,255],16:[0,1,3,4,32768],32:[0.,below,at,above,1.]}[depth]
      colors=(.25,.5,.75) if depth==32 else (top//4,top//2,top*3//4)
      pixels=b''.join(struct.pack(fmt,alpha,*colors) for alpha in alphas)
      for geometry in ([5,1],[1,5]):
       for inout in (1,2,3):
        for invert in (0,1):
         for interp in (1,2,3):
          for mode in (1,2):
           for bg in (0,1):
            c=dict(geometry=geometry,depth=depth,profile='sdr',parameters=a.defaults(*geometry),pixels=pixels,input_padding=3,output_padding=5)
            values={1:invert,2:inout,3:4,4:3,5:mode,6:bg,7:[255,28,53,238],8:[255,16,160,48],9:interp}
            for q in c['parameters']:
             if q['slot'] in values:q['value']=values[q['slot']]
            yield f'{depth}/{geometry}/inout{inout}/invert{invert}/interp{interp}/mode{mode}/bg{bg}',c


def main():
    p=argparse.ArgumentParser();p.add_argument('--scratch',type=Path,required=True);p.add_argument('--report',type=Path,required=True)
    p.add_argument('--before-ref',default='1b656d418ba44543da2225097108796f0937d9cc');p.add_argument('--campaign',type=Path,action='append',default=[])
    p.add_argument('--matrix',action='store_true');p.add_argument('--cutoff-matrix',action='store_true');p.add_argument('--corpus',action='store_true');p.add_argument('--update-corpus',action='store_true')
    args=p.parse_args();args.scratch=args.scratch.resolve();assert args.scratch.is_relative_to(ROOT/'orchestra/state/C03-dg-smart')
    args.scratch.mkdir(parents=True,exist_ok=True);os.environ.update(TMPDIR=str(args.scratch),TMP=str(args.scratch),TEMP=str(args.scratch));tempfile.tempdir=str(args.scratch)
    before_source=subprocess.check_output(['git','show',args.before_ref+':mac/OLMDistanceGradation/OLMDistanceGradation.cpp'],cwd=ROOT).decode()
    a=Adapter(argparse.Namespace(max_size=256,case_timeout=30,main=main_checkout(),worker=default_worker()))
    report=dict(schema='olm.dg-smart-verification-C03/1',before_ref=args.before_ref,before_source_sha256=sha(before_source.encode()),campaigns=[],matrix=[],corpus=[])
    deadline=time.monotonic()+1800
    with tempfile.TemporaryDirectory(dir=args.scratch) as td:
      td=Path(td);prod=td/'prod';prod.mkdir();report['provenance']=a.prepare(prod,deadline)
      old=variant(a,td/'before',deadline,before_source);san=variant(a,td/'san',deadline,sanitized=True)
      wd=td/'case';wd.mkdir()
      def compare(c,reference_hash):
        bs,br,_=old.candidate(c,wd,'smart',deadline);ns,nr,_=a.candidate(c,wd,'smart',deadline);ss,sr,_=san.candidate(c,wd,'smart',deadline)
        assert ss==ns and sr==nr,('sanitizer',ss,ns)
        assert ns['status'] in ('ok','refusal'),ns
        before_exact=bs['status']=='ok' and sha(br)==reference_hash
        after_exact=ns['status']=='ok' and sha(nr)==reference_hash
        if before_exact:assert after_exact and br==nr,('base exact regression',c)
        return dict(before_status=bs['status'],after_status=ns['status'],before_sha256=sha(br),after_sha256=sha(nr),
                    before_exact=before_exact,after_exact=after_exact,changed=br!=nr or bs['status']!=ns['status'],sanitized_equal=True),ns,nr
      for campaign in args.campaign:
        data=json.loads(campaign.read_text());rows=[]
        for row in data['cases']:
          c=a.generate(data['seed'],row['index']);assert sha(c['pixels'])==row['input_sha256']
          oracle=row['result']['oracles']['smart'] if 'oracles' in row['result'] else row['result']['oracle']
          reference=oracle.get('raw_sha256') if oracle['status']=='ok' else None
          result,_,_=compare(c,reference);result.update(index=row['index'],oracle=oracle)
          rows.append(result)
        counts=dict(Counter(f"{r['before_exact']}->{r['after_exact']}" for r in rows))
        report['campaigns'].append(dict(seed=data['seed'],campaign_sha256=sha(campaign.read_bytes()),counts=counts,rows=rows));print('CAMPAIGN',data['seed'],counts,flush=True)
      if args.matrix or args.cutoff_matrix:
        for label,c in (cutoff_matrix(a) if args.cutoff_matrix else matrix(a)):
          oracle,reference=a.oracle(c,wd,deadline,'smart');assert oracle['status']=='ok',(label,oracle)
          result,_,raw=compare(c,sha(reference));result.update(label=label,input_sha256=sha(c['pixels']),oracle_sha256=sha(reference))
          if not result['after_exact']:result['diff']=raw_diff(reference,raw,c['depth'])
          report['matrix'].append(result)
        print('MATRIX',dict(Counter(f"{r['before_exact']}->{r['after_exact']}" for r in report['matrix'])),flush=True)
      if args.corpus or args.update_corpus:
        for path in sorted((ROOT/'tests/fuzz_corpus/olmdistancegradation').glob('*.json')):
          c,saved=load_corpus(path,a);oracle=saved['result'].get('oracles',{}).get('smart',saved['result']['oracle'])
          result,ns,nr=compare(c,oracle.get('raw_sha256'));result['path']=str(path.relative_to(ROOT))
          if result['changed']:assert result['after_exact'],('corpus change is not toward exact',path,result)
          report['corpus'].append(result)
          if args.update_corpus and result['changed']:
            saved['result']['routes']['smart']={**ns,'status':'exact','raw_sha256':sha(nr)}
            saved['provenance']=report['provenance']
            path.write_text(json.dumps(saved,indent=2,sort_keys=True)+'\n')
        print('CORPUS',dict(Counter(f"{r['before_exact']}->{r['after_exact']}" for r in report['corpus'])),flush=True)
    args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print('PASS',flush=True)

if __name__=='__main__':main()
