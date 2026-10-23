#!/usr/bin/env python3
"""Bind a captured PF32 Smart callback to typed nonfinite public outputs.

The unmodified public worker can trace PNG only. Capture the real builder and
field using an SDR proxy whose mask comes from original cvConvertScale; replace only world pointers/source bytes for
callback replay. Require the entire replay to match the separate typed public
render. This is not a natural full-owner HDR memory capture.
"""
from __future__ import annotations
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
from adapters.olmdistancegradation import Adapter, SOURCE
from core import sha, raw_diff
from run import main_checkout, default_worker
from verify_distancegradation_smart_C08 import variant
from probe_distancegradation_C19 import matrix
import numpy as np
from cv_bridge import build_ipl, read_ipl
from windows_runtime import WindowsOpenCVRuntime
from aex_loader import AexLoader
from unicorn.x86_const import UC_X86_REG_XMM7, UC_X86_REG_XMM6, UC_X86_REG_XMM2, UC_X86_REG_XMM3, UC_X86_REG_XMM0, UC_X86_REG_XMM1
from PIL import Image


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--scratch',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    p.add_argument('--source-ref')
    p.add_argument('--source',type=Path)
    p.add_argument('--case-index',type=int)
    p.add_argument('--seed',type=int,default=1)
    p.add_argument('--label',action='append',default=[])
    args=p.parse_args();args.scratch=args.scratch.resolve()
    assert args.scratch.is_relative_to(ROOT/'orchestra/state')
    args.scratch.mkdir(parents=True,exist_ok=True)
    os.environ.update(TMPDIR=str(args.scratch),TMP=str(args.scratch),TEMP=str(args.scratch))
    tempfile.tempdir=str(args.scratch)
    a=Adapter(argparse.Namespace(max_size=256,case_timeout=30,main=main_checkout(),worker=default_worker()))
    source=args.source.read_text() if args.source else (subprocess.check_output(['git','show',args.source_ref+':mac/OLMDistanceGradation/OLMDistanceGradation.cpp'],cwd=ROOT).decode() if args.source_ref else SOURCE.read_text())
    # Source is a diagnostic candidate supplied explicitly by the caller.
    report=dict(schema='olm.dg-smart-trace-C19/1',source_ref=args.source_ref,source_sha256=sha(source.encode()),rows=[])
    source=source.replace('// d_alpha: source ownership follows',
        'if (const char *mp=getenv("OLM_DG_C19_MASK")) { FILE *f=fopen(mp,"wb"); if(f) { fwrite(mask.data(),1,mask.size(),f); fclose(f); } }\n\t// d_alpha: source ownership follows',1)
    with tempfile.TemporaryDirectory(dir=args.scratch) as td:
      td=Path(td);prod=td/'prod';prod.mkdir();deadline=time.monotonic()+600
      report['provenance']=a.prepare(prod,deadline)
      a=variant(a,td/'candidate',deadline,source)
      ld=AexLoader(str(a.aex),verbose=False,fast=True)
      ld.register_libm_impls(max_threads=1)
      WindowsOpenCVRuntime(ld).install()
      ld.enable_crt_initializer_imports()
      report['conversion_boundaries']=[]
      boundary_bits=[0,0x80000000,0x3bc0c0bf,0x3bc0c0c0,0x3bc0c0c1,0x3f000000,
                     0x3f800000,0x7f800000,0xff800000,0x7fc12345,0xff812346,
                     0x4b00807f,0x4b008080,0x4b008081,0x7f7fffff,0xff7fffff,1]
      for width in (1,7,17):
        for start in range(0,len(boundary_bits),width):
          bits=boundary_bits[start:start+width]
          alpha=np.array(bits,dtype='<u4').view('<f4').reshape(1,-1)
          ip=build_ipl(ld,alpha);op=build_ipl(ld,np.zeros(alpha.shape,dtype=np.uint8))
          ld.call_function(0x18117c580,[ip,op],float_args={2:(255.,'d'),3:(0.,'d')})
          report['conversion_boundaries'].append(dict(width=len(bits),input_bits=[f'{v:08x}' for v in bits],
              output_hex=read_ipl(ld,op).tobytes().hex(),imports=sorted(set(v.name for v in ld.import_log))))
      ownership=[]
      products=[]
      powers=[]
      def power_hook(loader,rip,size):
          value=loader.uc.reg_read(UC_X86_REG_XMM0)&0xffffffff
          if rip==0x181170ea3:
              powers.append(dict(input=f'{value:08x}',exponent=f'{loader.uc.reg_read(UC_X86_REG_XMM1)&0xffffffff:08x}'))
          else:powers[-1]['result']=f'{value:08x}'
      for address in (0x181170ea3,0x181170ea8):ld.add_code_hook(address,power_hook)
      def product_hook(loader,rip,size):
          reg = UC_X86_REG_XMM6 if rip in (0x181170f8b,0x181170f8f) else UC_X86_REG_XMM3
          value = loader.uc.reg_read(reg)&0xffffffff
          if rip in (0x181170f8b,0x181170f1c):
              products.append(dict(instruction=hex(rip),sample=f'{value:08x}',
                                   weight=f'{loader.uc.reg_read(UC_X86_REG_XMM2)&0xffffffff:08x}'))
          else:
              products[-1]['result']=f'{value:08x}'
      for address in (0x181170f8b,0x181170f8f,0x181170f1c,0x181170f20):
          ld.add_code_hook(address,product_hook)
      def hook(loader,rip,size):
          ownership.append(loader.uc.reg_read(UC_X86_REG_XMM7).to_bytes(16,'little')[:4].hex())
      ld.add_code_hook(0x181170e1e,hook)
      for label,c in ([(f'campaign/seed{args.seed}/case{args.case_index}',a.generate(args.seed,args.case_index))] if args.case_index is not None else matrix(a)):
        if args.case_index is None:
            if label not in (args.label or ['alpha-infinity/7x1/owner1/mode1/bg0/interp2','alpha-nan/7x1/owner2/mode2/bg0/interp2','rgb-nonfinite/7x1/owner1/mode2/bg1/interp2']):continue
        w,h=c['geometry']
        alpha=np.frombuffer(c['pixels'],dtype='<f4').reshape(h,w,4)[:,:,0].copy()
        ip=build_ipl(ld,alpha);op=build_ipl(ld,np.zeros((h,w),dtype=np.uint8))
        ld.call_function(0x18117c580,[ip,op],float_args={2:(255.,'d'),3:(0.,'d')})
        conversion_imports=sorted(set(v.name for v in ld.import_log))
        converted=read_ipl(ld,op).copy()
        proxy=[(64,128,192,255 if int(v)>1 else 0) for v in converted.reshape(-1)]
        im=Image.new('RGBA',(w,h));im.putdata(proxy);im.save(td/'proxy.png')
        params=[]
        for q in c['parameters']:
            name=next(d['name'] for d in a.binding['parameters'] if d['slot']==q['slot'])
            params.append(name+'='+(','.join(map(str,q['value'])) if isinstance(q['value'],list) else str(q['value'])))
        watches=['function=0x1172a10,arg=stack6,size=224',f'rva=0x1173642,arg=rdx,deref=88,size={len(c["pixels"])}']
        cmd=[str(a.worker),'render-trace-png',str(a.aex),str(td/'proxy.png'),str(td/'out.png'),'--pixel-format','argb32f']
        for watch in watches:cmd+=['--watch',watch]
        proc=subprocess.run(cmd+params,capture_output=True,check=True,timeout=30,env=a.env)
        trace=json.loads(proc.stdout)
        assert trace['render_error']==0 and trace['guards_intact']
        t=next(t for t in trace['execution_traces'] if t['selector']=='SMART_RENDER')
        assert not t['trace_configuration']['unhookable_watches']
        ws={v['watch_id']:v for v in t['memory_witnesses']}
        state=bytearray.fromhex(ws['watch-1']['after']['hex'])
        field=bytes.fromhex(ws['watch-2']['after']['hex'])
        def world(data):
            addr=ld.bump_alloc(len(data),align=16);ld.write_bytes(addr,data)
            header=ld.host_alloc(0x80,align=16);body=bytearray(0x80)
            struct.pack_into('<QIIII',body,0x18,addr,w*16,w,h,32)
            ld.write_bytes(header,bytes(body));return header
        struct.pack_into('<QQ',state,0,world(c['pixels']),world(field))
        ref=ld.host_alloc(len(state),align=16);ld.write_bytes(ref,bytes(state))
        raw=b'';ownership.clear();products.clear();powers.clear();callback_imports=set()
        for y in range(h):
          for x in range(w):
            out=ld.bump_alloc(16,align=16);ld.write_bytes(out,b'\xee'*16)
            ld.call_function(0x181170c90,int_args=[ref,x,y,0,out],max_instructions=200000)
            callback_imports.update(v.name for v in ld.import_log)
            raw+=ld.read_bytes(out,16)
        oracle,public=a.oracle(c,td,deadline,'smart')
        assert oracle['status']=='ok' and public==raw,(label,oracle,raw_diff(public,raw,32))
        debug=td/'mac.trace';debug.unlink(missing_ok=True)
        mask_path=td/'mask.bin';mask_path.unlink(missing_ok=True)
        a.env.update(OLM_DG_C19_MASK=str(mask_path),OLM_DG_DEBUG_DUMP_PATH=str(debug),OLM_DG_SHADE_DEBUG_PATH=str(debug),
                     OLM_DG_DEBUG_POINTS=';'.join(f'{x},{y}' for y in range(h) for x in range(w)))
        status,mac,_=a.candidate(c,td,'smart',deadline);assert status['status']=='ok'
        shades=[dict(token.split('=',1) for token in line.split()[1:]) for line in debug.read_text().splitlines() if line.startswith('shade ')]
        mac_field=b''.join(struct.pack('<f',float(s['field_x'])) for s in shades)
        expected_field=b''.join(field[x*16+4:x*16+8] for x in range(w*h))
        row=dict(label=label,source_hex=c['pixels'].hex(),aex_refcon_tail_hex=state[0x90:].hex(),
                 aex_degenerate_mask=state[0x90],field_hex=field.hex(),ownership_bits=list(ownership),
                 field_diff=raw_diff(expected_field,mac_field,32),aex_hex=raw.hex(),mac_hex=mac.hex(),
                 output_diff=raw_diff(raw,mac,32),public_callback_sha256=sha(raw),watches=watches)
        row['converted_alpha_hex']=converted.tobytes().hex()
        expected_mask=(converted>1).astype(np.uint8).tobytes()
        row['mac_mask_hex']=mask_path.read_bytes().hex()
        row['mask_diff']=raw_diff(expected_mask,mask_path.read_bytes(),8)
        row['conversion_imports']=conversion_imports
        row['input_sha256']=sha(c['pixels'])
        row['mac_sha256']=sha(mac)
        row['original_products']=list(products)
        row['original_powers']=list(powers)
        row['callback_imports']=sorted(callback_imports)
        report['rows'].append(row)
        print(label,'degenerate',state[0x90],'field equal',expected_field==mac_field,'output equal',raw==mac,flush=True)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')


if __name__=='__main__':main()
