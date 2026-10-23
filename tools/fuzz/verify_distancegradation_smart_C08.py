#!/usr/bin/env python3
"""Reproduce C08 before/after Smart regressions, sanitizer runs and typed matrix."""
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
        source=source.replace('#include "OLMDistanceGradation.h"','#include "'+str(SOURCE.with_suffix('.h'))+'"').replace('"../../core/','"'+str(ROOT/'core')+'/').replace('"../../ucrtmath/', '"'+str(ROOT/'ucrtmath')+'/')
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


def blur_matrix(a):
    # Mixed-alpha geometry, every typed owner, RGB/Layer, background, interpolation.
    for depth in (8,16,32):
      top={8:255,16:32768,32:1.0}[depth]
      fmt={8:'<4B',16:'<4H',32:'<4f'}[depth]
      alphas=[0,top/2,top,top/4,0,top,top/2]
      colors=(.25,.5,.75) if depth==32 else (top//4,top//2,top*3//4)
      pixels=b''.join(struct.pack(fmt,v if depth==32 else int(v),*colors) for v in alphas)
      for geometry in ([7,1],[1,7]):
       for blur in (2,3):
        for inout in (1,2,3):
         for interp in (1,2,3):
          for mode in (1,2):
           for bg in (0,1):
            c=dict(geometry=geometry,depth=depth,profile='sdr',parameters=a.defaults(*geometry),pixels=pixels,input_padding=3,output_padding=5)
            values={1:0,2:inout,3:4,4:3,5:mode,6:bg,7:[255,28,53,238],8:[255,16,160,48],9:interp,11:blur,12:1}
            for q in c['parameters']:
             if q['slot'] in values:q['value']=values[q['slot']]
            yield f'{depth}/{geometry}/blur{blur}/inout{inout}/interp{interp}/mode{mode}/bg{bg}',c


def field_matrix(a):
    # Long runs include half-byte ties; 2D islands also exercise irrational EDTs.
    for geometry in ([17,1],[13,7]):
     w,h=geometry
     pixels=bytes(v for y in range(h) for x in range(w)
                  for v in (0 if (x==0 or (x==8 and y==0)) else (128 if (x+y)%3 else 255),37,113,221))
     for threshold in (3,6,13):
      for inout in (1,2,3):
       for invert in (0,1):
        for interp in (1,2,3):
         for mode in (1,2):
          c=dict(geometry=geometry,depth=8,profile='sdr',parameters=a.defaults(w,h),pixels=pixels,input_padding=3,output_padding=5)
          values={1:invert,2:inout,3:threshold,4:threshold,5:mode,6:int(mode==1),7:[255,28,53,238],8:[255,16,160,48],9:interp,11:1,12:0}
          for q in c['parameters']:
           if q['slot'] in values:q['value']=values[q['slot']]
          yield f'{geometry}/threshold{threshold}/inout{inout}/invert{invert}/interp{interp}/mode{mode}',c


def inactive_matrix(a):
    # The three cvSmooth modes have a 1x1 kernel at Size=0. Mode5 is excluded.
    below=struct.unpack('<f',struct.pack('<I',0x38d1b716))[0]
    at=struct.unpack('<f',struct.pack('<I',0x38d1b717))[0]
    for geometry in ([7,1],[1,7],[7,5]):
     w,h=geometry
     av=[0.,below,at,.0058823530562222,.5,1.,.25]
     pixels=b''.join(struct.pack('<4f',av[(x+y)%7],.125*(x%7),.0625*(y%7),.75) for y in range(h) for x in range(w))
     for blur in (2,3,4):
      for inout in (1,2,3):
       for invert in (0,1):
        for interp in (1,2,3):
         for mode in (1,2):
          for bg in (0,1):
           c=dict(geometry=geometry,depth=32,profile='sdr',parameters=a.defaults(w,h),pixels=pixels,input_padding=3,output_padding=5)
           values={1:invert,2:inout,3:4,4:3,5:mode,6:bg,7:[255,28,53,238],8:[255,16,160,48],9:interp,11:blur,12:0}
           for q in c['parameters']:
            if q['slot'] in values:q['value']=values[q['slot']]
           yield f'{geometry}/blur{blur}/inout{inout}/invert{invert}/interp{interp}/mode{mode}/bg{bg}',c


def main():
    p=argparse.ArgumentParser();p.add_argument('--scratch',type=Path,required=True);p.add_argument('--report',type=Path,required=True)
    p.add_argument('--inactive-gate-off',action='store_true');p.add_argument('--candidate-source',type=Path);p.add_argument('--strict-admission',action='store_true')
    p.add_argument('--before-ref',default='b4350d648947640ebdc3459c5e0451cbef54c64f');p.add_argument('--campaign',type=Path,action='append',default=[])
    p.add_argument('--inactive-negatives',action='store_true');p.add_argument('--inactive-matrix',action='store_true');p.add_argument('--field-matrix',action='store_true');p.add_argument('--blur-matrix',action='store_true');p.add_argument('--matrix',action='store_true');p.add_argument('--cutoff-matrix',action='store_true');p.add_argument('--corpus',action='store_true');p.add_argument('--update-corpus',action='store_true')
    args=p.parse_args();args.scratch=args.scratch.resolve();assert args.scratch.is_relative_to(ROOT/'orchestra/state/C08-dg-smart-r2')
    args.scratch.mkdir(parents=True,exist_ok=True);os.environ.update(TMPDIR=str(args.scratch),TMP=str(args.scratch),TEMP=str(args.scratch));tempfile.tempdir=str(args.scratch)
    before_source=subprocess.check_output(['git','show',args.before_ref+':mac/OLMDistanceGradation/OLMDistanceGradation.cpp'],cwd=ROOT).decode()
    a=Adapter(argparse.Namespace(max_size=256,case_timeout=30,main=main_checkout(),worker=default_worker()))
    report=dict(schema='olm.dg-smart-verification-C08/1',before_ref=args.before_ref,before_source_sha256=sha(before_source.encode()),campaigns=[],matrix=[],corpus=[])
    deadline=time.monotonic()+1800
    with tempfile.TemporaryDirectory(dir=args.scratch) as td:
      td=Path(td);prod=td/'prod';prod.mkdir();report['provenance']=a.prepare(prod,deadline)
      candidate_source=args.candidate_source.read_text() if args.candidate_source else None
      if args.inactive_gate_off:
        assert candidate_source is None
        candidate_source=replace_once(before_source,
            'p.blur_mode == BLUR_MODE_NONE &&\n\t       (p.interp_mode',
            '(p.blur_mode == BLUR_MODE_NONE ||\n\t        (p.blur_size == 0 && p.blur_mode >= BLUR_MODE_NO_SCALE &&\n\t         p.blur_mode <= BLUR_MODE_MEDIAN)) &&\n\t       (p.interp_mode')
        report['experiment']='inactive mode guard only'
      if candidate_source is not None:
        a=variant(a,td/'experiment',deadline,candidate_source)
        report.update(candidate_source_sha256=sha(candidate_source.encode()),candidate_sha256=sha(a.binary.read_bytes()))
      old=variant(a,td/'before',deadline,before_source);san=variant(a,td/'san',deadline,source=candidate_source,sanitized=True)
      wd=td/'case';wd.mkdir()
      def compare(c,reference_hash):
        bs,br,_=old.candidate(c,wd,'smart',deadline);ns,nr,_=a.candidate(c,wd,'smart',deadline);ss,sr,_=san.candidate(c,wd,'smart',deadline)
        assert ss==ns and sr==nr,('sanitizer',ss,ns)
        assert ns['status'] in ('ok','refusal'),ns
        before_exact=bs['status']=='ok' and sha(br)==reference_hash
        after_exact=ns['status']=='ok' and sha(nr)==reference_hash
        if before_exact:assert after_exact and br==nr,('base exact regression',c)
        if args.strict_admission and (br!=nr or bs['status']!=ns['status']):
          assert bs['status']=='refusal' and after_exact,('admission is not refusal->exact',bs,ns,c)
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
      if args.matrix or args.cutoff_matrix or args.blur_matrix or args.field_matrix or args.inactive_matrix:
        for label,c in (inactive_matrix(a) if args.inactive_matrix else field_matrix(a) if args.field_matrix else blur_matrix(a) if args.blur_matrix else cutoff_matrix(a) if args.cutoff_matrix else matrix(a)):
          oracle,reference=a.oracle(c,wd,deadline,'smart');assert oracle['status']=='ok',(label,oracle)
          result,_,raw=compare(c,sha(reference));result.update(label=label,input_sha256=sha(c['pixels']),oracle_sha256=sha(reference))
          if args.inactive_matrix:assert result['after_exact'],(label,result)
          if not result['after_exact']:result['diff']=raw_diff(reference,raw,c['depth'])
          report['matrix'].append(result)
          if len(report['matrix'])%72==0:print('MATRIX_PROGRESS',len(report['matrix']),flush=True)
        print('MATRIX',dict(Counter(f"{r['before_exact']}->{r['after_exact']}" for r in report['matrix'])),flush=True)
      if args.inactive_matrix or args.inactive_negatives:
        c0=next(inactive_matrix(a))[1]
        report['negative']=[]
        for label,slot,value,word in [('bilateral',11,5,None),('power',9,4,None),
              ('alpha-above-one',None,None,(0,0x3f800001)),('rgb-above-one',None,None,(1,0x3f800001)),
              ('rgb-negative-subnormal',None,None,(1,0x80000001)),('rgb-infinity',None,None,(1,0x7f800000)),
              ('rgb-nan',None,None,(1,0x7fc12345))]:
          c=copy.deepcopy(c0)
          if slot is not None:
            for q in c['parameters']:
              if q['slot']==slot:q['value']=value
          if word is not None:
            raw=bytearray(c['pixels']);struct.pack_into('<I',raw,word[0]*4,word[1]);c['pixels']=bytes(raw)
          result,ns,_=compare(c,None)
          assert result['before_status']==ns['status']=='refusal' and not result['changed'],(label,result)
          report['negative'].append(dict(label=label,**result))
        print('NEGATIVE',len(report['negative']),'unchanged clean refusals',flush=True)
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
