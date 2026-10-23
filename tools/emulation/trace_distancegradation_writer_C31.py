#!/usr/bin/env python3
"""Bind PF16 HDR public output to its actual callback, then compare pre-store bits.

Uses a same-mask PNG proxy for builder/field capture, then relocates worlds and
requires full callback output equality with the separate typed public render.
This is not a natural typed full-owner memory capture.
"""
import argparse
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import time
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/fuzz'))
from adapters.olmdistancegradation import Adapter
from core import sha,raw_diff
from run import main_checkout,default_worker
from verify_distancegradation_smart_C08 import variant
from probe_distancegradation_C31 import mask_matrix
from aex_loader import AexLoader
from unicorn.x86_const import UC_X86_REG_XMM1,UC_X86_REG_XMM4,UC_X86_REG_XMM5,UC_X86_REG_XMM6
from PIL import Image


def main():
    p=argparse.ArgumentParser();p.add_argument('--scratch',type=Path,required=True);p.add_argument('--report',type=Path,required=True);p.add_argument('--source',type=Path,required=True)
    p.add_argument('--uniform',action='store_true')
    args=p.parse_args();args.scratch=args.scratch.resolve()
    assert args.scratch.is_relative_to(ROOT/'orchestra/state')
    args.scratch.mkdir(parents=True,exist_ok=True)
    os.environ.update(TMPDIR=str(args.scratch),TMP=str(args.scratch),TEMP=str(args.scratch));tempfile.tempdir=str(args.scratch)
    a=Adapter(argparse.Namespace(max_size=256,case_timeout=30,main=main_checkout(),worker=default_worker()))
    report={'schema':'olm.dg-C31-writer/1','source_sha256':sha(args.source.read_bytes())}
    deadline=time.monotonic()+600
    with tempfile.TemporaryDirectory(dir=args.scratch) as tmp:
      td=Path(tmp);prod=td/'prod';prod.mkdir();report['provenance']=a.prepare(prod,deadline);a=variant(a,td/'candidate',deadline,args.source.read_text())
      label,c=next((label,c) for label,c in mask_matrix(a) if label=='7x3/owner1/invert0/mode1/bg0/interp2/blur2')
      w,h=c['geometry'];alphas=(0,191,192,193,32768,65535,192,192,0,32767,1)
      c['pixels']=b''.join(struct.pack('<4H',alphas[(x+3*y)%len(alphas)],12345,32768,54321) for y in range(h) for x in range(w))
      if args.uniform:
        c['pixels']=b''.join(struct.pack('<4H',65535,r,g,b) for al,r,g,b in struct.iter_unpack('<4H',c['pixels']))
        for q in c['parameters']:
          if q['slot']==6:q['value']=1
          if q['slot']==9:q['value']=1
          if q['slot']==11:q['value']=1
          if q['slot']==12:q['value']=0
      im=Image.new('RGBA',(w,h));im.putdata([(64,128,192,255 if al>=192 else 0) for al,r,g,b in struct.iter_unpack('<4H',c['pixels'])]);im.save(td/'proxy.png')
      params=[]
      for q in c['parameters']:
        name=next(d['name'] for d in a.binding['parameters'] if d['slot']==q['slot'])
        params.append(name+'='+(','.join(map(str,q['value'])) if isinstance(q['value'],list) else str(q['value'])))
      watches=['function=0x1170ff0,arg=stack6,size=224']+[f'rva=0x1171c65,arg=rdx,size={w*8},occurrence={y+1}' for y in range(h)]
      cmd=[str(a.worker),'render-trace-png',str(a.aex),str(td/'proxy.png'),str(td/'out.png'),'--pixel-format','argb16']
      for watch in watches:cmd+=['--watch',watch]
      proc=subprocess.run(cmd+params,capture_output=True,check=True,timeout=30,env=a.env)
      trace=json.loads(proc.stdout);assert trace['render_error']==0 and trace['guards_intact']
      t=next(t for t in trace['execution_traces'] if t['selector']=='SMART_RENDER');assert not t['trace_configuration']['unhookable_watches']
      ws={v['watch_id']:v for v in t['memory_witnesses']}
      state=bytearray.fromhex(ws['watch-1']['after']['hex'])
      field=b''.join(bytes.fromhex(ws[f'watch-{y+2}']['before']['hex']) for y in range(h))
      ld=AexLoader(str(a.aex),verbose=False,fast=True);ld.register_libm_impls()
      def world(data):
        addr=ld.bump_alloc(len(data),align=16);ld.write_bytes(addr,data)
        header=ld.host_alloc(0x80,align=16);body=bytearray(0x80);struct.pack_into('<QIIII',body,0x18,addr,w*8,w,h,16);ld.write_bytes(header,bytes(body));return header
      struct.pack_into('<QQ',state,0,world(c['pixels']),world(field));ref=ld.host_alloc(len(state),align=16);ld.write_bytes(ref,bytes(state))
      pre=[]
      def hook(loader,rip,size):
        pre.append([f'{loader.uc.reg_read(reg)&0xffffffff:08x}' for reg in (UC_X86_REG_XMM6,UC_X86_REG_XMM1,UC_X86_REG_XMM4,UC_X86_REG_XMM5)])
      ld.add_code_hook(0x1811707f4,hook)
      replay=b''
      for y in range(h):
        for x in range(w):
          out=ld.bump_alloc(8,align=16);ld.call_function(0x181170480,int_args=[ref,x,y,0,out],max_instructions=200000);replay+=ld.read_bytes(out,8)
      oracle,public=a.oracle(c,td,deadline,'smart');assert oracle['status']=='ok' and replay==public,raw_diff(public,replay,16)
      capture=td/'boundary.jsonl'
      a.env.update(OLM_DG_PF16_BOUNDARY_CAPTURE_PATH=str(capture),OLM_DG_PF16_BOUNDARY_CAPTURE_CASE_ID='C31-hdr',OLM_DG_DEBUG_POINTS=';'.join(f'{x},{y}' for y in range(h) for x in range(w)))
      status,raw,_=a.candidate(c,td,'smart',deadline);assert status['status']=='ok'
      mac=[json.loads(line) for line in capture.read_text().splitlines()]
      macpre=[[r['pre_store'][ch]['bits'][2:].zfill(8) for ch in ('a','r','g','b')] for r in mac]
      report.update(original_degenerate_mask=state[0x90],input_sha256=sha(c['pixels']),input_hex=c['pixels'].hex(),parameters=c['parameters'],geometry=[w,h],field_hex=field.hex(),state_tail_hex=state[0x90:].hex(),
                    public_callback_sha256=sha(replay),original_pre_store=pre,mac_pre_store=macpre,pre_store_equal=pre==macpre,mac_boundary=mac,
                    original_hex=public.hex(),mac_hex=raw.hex(),output_diff=raw_diff(public,raw,16),imports=sorted(set(x.name for x in ld.import_log)),
                    scale_hex=ld.read_bytes(0x181504ac4,4).hex(),watches=watches)
    args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('pre-store equal',report['pre_store_equal'],'output',report['output_diff'],'imports',report['imports'])

if __name__=='__main__':main()
