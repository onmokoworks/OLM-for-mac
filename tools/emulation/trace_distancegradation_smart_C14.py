#!/usr/bin/env python3
"""Bind a captured PF32 Smart callback to typed extended-input public outputs.

The unmodified public worker can trace PNG only. Capture the real builder and
field using a same-mask SDR proxy; replace only world pointers/source bytes for
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
from verify_distancegradation_smart_C14 import matrix, gate_source
from aex_loader import AexLoader
from unicorn.x86_const import UC_X86_REG_XMM7
from PIL import Image


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--scratch',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    p.add_argument('--source-ref')
    p.add_argument('--source',type=Path)
    p.add_argument('--case-index',type=int)
    p.add_argument('--case-json',type=Path,help='Explicit PF32 public case with pixels_hex; mutually exclusive with case-index')
    p.add_argument('--seed',type=int,default=1)
    p.add_argument('--geometry',type=int,nargs=2,help='Independent cropped-prefix case; source must contain enough pixels')
    p.add_argument('--blur-size',type=int)
    args=p.parse_args();args.scratch=args.scratch.resolve()
    assert args.case_json is None or args.case_index is None
    targeted = args.case_index is not None or args.case_json is not None
    assert args.scratch.is_relative_to(ROOT/'orchestra/state')
    args.scratch.mkdir(parents=True,exist_ok=True)
    os.environ.update(TMPDIR=str(args.scratch),TMP=str(args.scratch),TEMP=str(args.scratch))
    tempfile.tempdir=str(args.scratch)
    a=Adapter(argparse.Namespace(max_size=256,case_timeout=30,main=main_checkout(),worker=default_worker()))
    source=args.source.read_text() if args.source else (subprocess.check_output(['git','show',args.source_ref+':mac/OLMDistanceGradation/OLMDistanceGradation.cpp'],cwd=ROOT).decode() if args.source_ref else SOURCE.read_text())
    source=gate_source(source,'finite')
    report=dict(schema='olm.dg-smart-trace-C14/1',source_ref=args.source_ref,source_sha256=sha(source.encode()),rows=[])
    if targeted:
        dump='if(const char *dp=getenv("OLM_DG_C14_PF32_BLUR")) { FILE *f=fopen(dp,"ab"); if(f) { fwrite(df.x.data(),4,df.x.size(),f); fclose(f); } }'
        source=source.replace('if (blurred) df.pre_blur_x = df.x;',dump+'\n\tif (blurred) df.pre_blur_x = df.x;')
        source=source.replace('// The Windows typed paths merge the float field',dump+'\n\t// The Windows typed paths merge the float field')
    with tempfile.TemporaryDirectory(dir=args.scratch) as td:
      td=Path(td);prod=td/'prod';prod.mkdir();deadline=time.monotonic()+600
      report['provenance']=a.prepare(prod,deadline)
      a=variant(a,td/'candidate',deadline,source)
      ld=AexLoader(str(a.aex),verbose=False,fast=True)
      ld.register_libm_impls()
      ownership=[]
      def hook(loader,rip,size):
          ownership.append(loader.uc.reg_read(UC_X86_REG_XMM7).to_bytes(16,'little')[:4].hex())
      ld.add_code_hook(0x181170e1e,hook)
      if args.case_json:
          explicit=json.loads(args.case_json.read_text());explicit['pixels']=bytes.fromhex(explicit.pop('pixels_hex'))
          assert explicit['depth']==32 and len(explicit['pixels'])==explicit['geometry'][0]*explicit['geometry'][1]*16
          cases=[('explicit/'+args.case_json.name,explicit)]
      else:
          cases=[(f'campaign/seed{args.seed}/case{args.case_index}',a.generate(args.seed,args.case_index))] if targeted else matrix(a)
      for label,c in cases:
        if not targeted:
            if c['geometry']!=[7,1] or not label.endswith('mode2/bg0'):continue
            if c['profile'] not in ('alpha-signed','uniform-hdr','uniform-negative'):continue
        if args.geometry:
            assert min(args.geometry)>0 and len(c['pixels'])>=args.geometry[0]*args.geometry[1]*16
            c['geometry']=args.geometry
            c['pixels']=c['pixels'][:args.geometry[0]*args.geometry[1]*16]
        if args.blur_size is not None:
            for q in c['parameters']:
                if q['slot']==12:q['value']=args.blur_size
        w,h=c['geometry']
        proxy=[(64,128,192,0 if al<1.5/255 else 255) for al,r,g,b in struct.iter_unpack('<4f',c['pixels'])]
        im=Image.new('RGBA',(w,h));im.putdata(proxy);im.save(td/'proxy.png')
        params=[]
        for q in c['parameters']:
            name=next(d['name'] for d in a.binding['parameters'] if d['slot']==q['slot'])
            params.append(name+'='+(','.join(map(str,q['value'])) if isinstance(q['value'],list) else str(q['value'])))
        watches=['function=0x1172a10,arg=stack6,size=224',f'rva=0x1173642,arg=rdx,deref=88,size={min(4096,len(c["pixels"]))}']
        plane_capture_bytes=min(4096,w*h*4)
        if targeted:
            watches+=[f'rva=0x1173611,arg=rcx,deref=88,size={plane_capture_bytes}',f'rva=0x1173611,arg=rdx,deref=88,size={plane_capture_bytes}', f'rva=0x12c97d3,arg=rcx,deref=16,size={plane_capture_bytes}', f'rva=0x12c97d3,arg=rdx,deref=16,size={plane_capture_bytes}', 'function=0x12c9930,arg=rcx,size=96']
        field_row_ids=[]
        if len(c['pixels'])>4096:
            assert w*16<=4096
            for y in range(h):
                field_row_ids.append(f'watch-{len(watches)+1}')
                watches.append(f'rva=0x1173685,arg=rdx,size={w*16},occurrence={y+1}')
        cmd=[str(a.worker),'render-trace-png',str(a.aex),str(td/'proxy.png'),str(td/'out.png'),'--pixel-format','argb32f']
        for watch in watches:cmd+=['--watch',watch]
        proc=subprocess.run(cmd+params,capture_output=True,timeout=30,env=a.env)
        assert proc.returncode==0,proc.stderr[-2000:]
        trace=json.loads(proc.stdout)
        assert trace['render_error']==0 and trace['guards_intact']
        t=next(t for t in trace['execution_traces'] if t['selector']=='SMART_RENDER')
        assert not t['trace_configuration']['unhookable_watches']
        ws={v['watch_id']:v for v in t['memory_witnesses']}
        state=bytearray.fromhex(ws['watch-1']['after']['hex'])
        field=(b''.join(bytes.fromhex(ws[k]['before']['hex']) for k in field_row_ids)
               if field_row_ids else bytes.fromhex(ws['watch-2']['after']['hex']))
        def world(data):
            addr=ld.bump_alloc(len(data),align=16);ld.write_bytes(addr,data)
            header=ld.host_alloc(0x80,align=16);body=bytearray(0x80)
            struct.pack_into('<QIIII',body,0x18,addr,w*16,w,h,32)
            ld.write_bytes(header,bytes(body));return header
        struct.pack_into('<QQ',state,0,world(c['pixels']),world(field))
        ref=ld.host_alloc(len(state),align=16);ld.write_bytes(ref,bytes(state))
        raw=b'';ownership.clear()
        for y in range(h):
          for x in range(w):
            out=ld.bump_alloc(16,align=16);ld.write_bytes(out,b'\xee'*16)
            ld.call_function(0x181170c90,int_args=[ref,x,y,0,out],max_instructions=200000)
            raw+=ld.read_bytes(out,16)
        oracle,public=a.oracle(c,td,deadline,'smart')
        assert oracle['status']=='ok' and public==raw,(label,oracle,raw_diff(public,raw,32))
        debug=td/'mac.trace';debug.unlink(missing_ok=True)
        blurpath=td/'mac-blur.bin';blurpath.unlink(missing_ok=True)
        a.env.update(OLM_DG_DEBUG_DUMP_PATH=str(debug),OLM_DG_SHADE_DEBUG_PATH=str(debug),OLM_DG_C14_PF32_BLUR=str(blurpath),
                     OLM_DG_DEBUG_POINTS=';'.join(f'{x},{y}' for y in range(h) for x in range(w)))
        status,mac,_=a.candidate(c,td,'smart',deadline);assert status['status']=='ok'
        shades=[dict(token.split('=',1) for token in line.split()[1:]) for line in debug.read_text().splitlines() if line.startswith('shade ')]
        mac_field=b''.join(struct.pack('<f',float(s['field_x'])) for s in shades)
        expected_field=b''.join(field[x*16+4:x*16+8] for x in range(w*h))
        row=dict(label=label,geometry=c['geometry'],parameters=c['parameters'],source_hex=c['pixels'].hex(),aex_refcon_tail_hex=state[0x90:].hex(),
                 aex_degenerate_mask=state[0x90],field_hex=field.hex(),ownership_bits=list(ownership),
                 field_diff=raw_diff(expected_field,mac_field,32),aex_hex=raw.hex(),mac_hex=mac.hex(),
                 output_diff=raw_diff(raw,mac,32),public_callback_sha256=sha(raw),watches=watches)
        if targeted:
            planes=blurpath.read_bytes();assert len(planes)==w*h*8
            pre=bytes.fromhex(ws['watch-3']['before']['hex']);post=bytes.fromhex(ws['watch-4']['after']['hex'])
            row['backend_witnesses']={k:v for k,v in ws.items() if int(k.split('-')[1])>=5}
            row.update(aex_pre_hex=pre.hex(),aex_post_hex=post.hex(),mac_pre_hex=planes[:w*h*4].hex(),mac_post_hex=planes[w*h*4:].hex(),
                       plane_capture_bytes=plane_capture_bytes,plane_total_bytes=w*h*4,
                       pre_diff=raw_diff(pre,planes[:plane_capture_bytes],32),post_diff=raw_diff(post,planes[w*h*4:w*h*4+plane_capture_bytes],32))
        report['rows'].append(row)
        print(label,'degenerate',state[0x90],'field equal',expected_field==mac_field,'output equal',raw==mac,flush=True)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')


if __name__=='__main__':main()
