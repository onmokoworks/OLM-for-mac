#!/usr/bin/env python3
"""Pair Smart cvSmooth planes; PF16 uses a same-mask PNG proxy with a
full typed public/callback output binding, since the worker traces PNG8 only.
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
from adapters.olmdistancegradation import Adapter,SOURCE
from adapters.public import replace_once
from core import sha,raw_diff
from run import main_checkout,default_worker
from verify_distancegradation_smart_C08 import variant
from PIL import Image
from aex_loader import AexLoader


def main():
    p=argparse.ArgumentParser();p.add_argument('--scratch',type=Path,required=True);p.add_argument('--report',type=Path,required=True)
    p.add_argument('--source',type=Path);p.add_argument('--index',type=int,action='append',default=[])
    p.add_argument('--seed',type=int,default=1)
    p.add_argument('--case-json',type=Path,help='Explicit typed case with hex-encoded pixels')
    p.add_argument('--plane-prefix-bytes',type=int,help='Capture a bounded PF8 plane prefix when the full plane exceeds the worker watch limit')
    args=p.parse_args();args.scratch=args.scratch.resolve()
    assert args.scratch.is_relative_to(ROOT/'orchestra/state')
    args.scratch.mkdir(parents=True,exist_ok=True)
    os.environ.update(TMPDIR=str(args.scratch),TMP=str(args.scratch),TEMP=str(args.scratch));tempfile.tempdir=str(args.scratch)
    a=Adapter(argparse.Namespace(max_size=256,case_timeout=30,main=main_checkout(),worker=default_worker()))
    source=(args.source or SOURCE).read_text();report=dict(schema='olm.dg-blur-C14/1',source_sha256=sha(source.encode()),rows=[])
    dump='if (const char *dp=getenv("OLM_DG_C14_BLUR")) { FILE *f=fopen(dp,"ab"); if(f) { for(float v:df.x) { float scaled=v*(p.pixel_size==sizeof(PF_Pixel16)?32768.0f:255.0f); fwrite(&scaled,4,1,f); } fclose(f); } }'
    if 'const bool smart_pf8_scaled' in source:
        dump=dump.replace('v*(p.pixel_size', 'v*(smart_pf8_scaled?1.0f:p.pixel_size')
    source=replace_once(source,'if (blurred) df.pre_blur_x = df.x;',dump+'\n\tif (blurred) df.pre_blur_x = df.x;')
    source=replace_once(source,'// The Windows typed paths merge the float field',dump+'\n\t// The Windows typed paths merge the float field')
    deadline=time.monotonic()+600
    with tempfile.TemporaryDirectory(dir=args.scratch) as td:
      td=Path(td);prod=td/'prod';prod.mkdir();report['provenance']=a.prepare(prod,deadline);a=variant(a,td/'candidate',deadline,source)
      for index in ([0] if args.case_json else args.index or [45,200]):
        if args.case_json:
            c=json.loads(args.case_json.read_text());c['pixels']=bytes.fromhex(c['pixels'])
        else:c=a.generate(args.seed,index)
        assert c['depth'] in (8,16)
        w,h=c['geometry'];n=w*h*4;depth=c['depth']
        capture_n=args.plane_prefix_bytes or n
        assert 0<capture_n<=n and capture_n%4==0
        if args.plane_prefix_bytes:assert depth==8
        im=Image.new('RGBA',(w,h))
        im.putdata([(r,g,b,al) for al,r,g,b in struct.iter_unpack('<4B',c['pixels'])] if depth==8 else
                   [(64,128,192,255 if al/32768*255>=1.5 else 0) for al,r,g,b in struct.iter_unpack('<4H',c['pixels'])])
        im.save(td/'in.png')
        params=[]
        for q in c['parameters']:
            name=next(d['name'] for d in a.binding['parameters'] if d['slot']==q['slot'])
            params.append(name+'='+(','.join(map(str,q['value'])) if isinstance(q['value'],list) else str(q['value'])))
        site='0x1172901' if depth==8 else '0x1171bf1'
        watches=[f'rva={site},arg=rcx,deref=88,size={capture_n}',f'rva={site},arg=rdx,deref=88,size={capture_n}']
        if depth==16:
            watches+=['function=0x1170ff0,arg=stack6,size=224']
            watches+=[f'rva=0x1171c65,arg=rdx,size={w*8},occurrence={y+1}' for y in range(h)]
        cmd=[str(a.worker),'render-trace-png',str(a.aex),str(td/'in.png'),str(td/'out.png'),'--pixel-format',f'argb{depth}']
        for watch in watches:cmd+=['--watch',watch]
        proc=subprocess.run(cmd+params,capture_output=True,check=True,timeout=30,env=a.env);trace=json.loads(proc.stdout)
        assert trace['render_error']==0 and trace['guards_intact']
        t=next(t for t in trace['execution_traces'] if t['selector']=='SMART_RENDER')
        assert not t['trace_configuration']['unhookable_watches']
        ws={v['watch_id']:v for v in t['memory_witnesses']}
        pre=bytes.fromhex(ws['watch-1']['before']['hex']);post=bytes.fromhex(ws['watch-2']['after']['hex'])
        oracle,public=a.oracle(c,td,deadline,'smart');assert oracle['status']=='ok'
        callback_hash=None
        if depth==8:
            assert sha(public)==trace['raw_pixel_sha256']
        else:
            state=bytearray.fromhex(ws['watch-3']['after']['hex'])
            field=b''.join(bytes.fromhex(ws[f'watch-{y+4}']['before']['hex']) for y in range(h))
            ld=AexLoader(str(a.aex),verbose=False,fast=True);ld.register_libm_impls()
            def world(data):
                addr=ld.bump_alloc(len(data),align=16);ld.write_bytes(addr,data)
                header=ld.host_alloc(0x80,align=16);body=bytearray(0x80)
                struct.pack_into('<QIIII',body,0x18,addr,w*8,w,h,16)
                ld.write_bytes(header,bytes(body));return header
            struct.pack_into('<QQ',state,0,world(c['pixels']),world(field))
            ref=ld.host_alloc(len(state),align=16);ld.write_bytes(ref,bytes(state));replay=b''
            for y in range(h):
                for x in range(w):
                    out=ld.bump_alloc(8,align=16)
                    ld.call_function(0x181170480,int_args=[ref,x,y,0,out],max_instructions=200000)
                    replay+=ld.read_bytes(out,8)
            assert replay==public,raw_diff(public,replay,16)
            callback_hash=sha(replay)
        path=td/'mac.bin';path.unlink(missing_ok=True);a.env['OLM_DG_C14_BLUR']=str(path)
        status,mac,_=a.candidate(c,td,'smart',deadline);assert status['status']=='ok'
        planes=path.read_bytes();assert len(planes)==n*2
        assert len(pre)==len(post)==capture_n
        row=dict(index=index,geometry=[w,h],depth=depth,proxy_callback_sha256=callback_hash,input_sha256=sha(c['pixels']),oracle_sha256=sha(public),mac_sha256=sha(mac),
                 captured_plane_bytes=capture_n,full_plane_bytes=n,
                 aex_pre_hex=pre.hex(),aex_post_hex=post.hex(),mac_pre_hex=planes[:capture_n].hex(),mac_post_hex=planes[n:n+capture_n].hex(),
                 pre_diff=raw_diff(pre,planes[:capture_n],32),post_diff=raw_diff(post,planes[n:n+capture_n],32),output_diff=raw_diff(public,mac,depth),watches=watches)
        report['rows'].append(row);print('CASE',index,'PRE',row['pre_diff'],'POST',row['post_diff'],'OUTPUT',row['output_diff'],flush=True)
    args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')


if __name__=='__main__':main()
