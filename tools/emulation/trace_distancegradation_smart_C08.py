#!/usr/bin/env python3
"""C08 natural Smart owner capture, relocated callback replay, and Mac pairing.

Only pointer relocation in the captured refcon; no numerical AEX detours. The
callback replay must reproduce the full public owner's final output hash.
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
from verify_distancegradation_smart_C03 import variant
from core import sha, raw_diff
from run import main_checkout, default_worker
from aex_loader import AexLoader
from unicorn.x86_const import UC_X86_REG_XMM1, UC_X86_REG_XMM2, UC_X86_REG_XMM3, UC_X86_REG_XMM5, UC_X86_REG_XMM6, UC_X86_REG_XMM7, UC_X86_REG_XMM12, UC_X86_REG_XMM13, UC_X86_REG_XMM14
from PIL import Image


def bits(v): return struct.pack('<f',v).hex()
def reg(ld,r):return ld.uc.reg_read(r).to_bytes(16,'little')[:4].hex()


def main():
    p=argparse.ArgumentParser();p.add_argument('--scratch',type=Path,required=True);p.add_argument('--report',type=Path,required=True)
    p.add_argument('--blur-mode',type=int,default=1)
    p.add_argument('--blur-size',type=int,default=0)
    p.add_argument('--family',choices=['layer','mask'],default='layer')
    p.add_argument('--background',type=int,choices=[0,1],default=0)
    args=p.parse_args();args.scratch=args.scratch.resolve();args.scratch.mkdir(parents=True,exist_ok=True)
    assert args.scratch.is_relative_to(ROOT/'orchestra/state/C08-dg-smart-r2')
    os.environ.update(TMPDIR=str(args.scratch),TMP=str(args.scratch),TEMP=str(args.scratch));tempfile.tempdir=str(args.scratch)
    a=Adapter(argparse.Namespace(max_size=256,case_timeout=30,main=main_checkout(),worker=default_worker()))
    report={'schema':'olm.dg-smart-stage-C08/1','rows':[]}
    with tempfile.TemporaryDirectory(dir=args.scratch) as td:
        td=Path(td);deadline=time.monotonic()+300;report['provenance']=a.prepare(td,deadline)
        diagnostic=SOURCE.read_text().replace('// d_alpha: source ownership follows', 'if (const char *mp = getenv("OLM_DG_C08_MASK_PATH")) { FILE *mf = fopen(mp, "wb"); if (mf) { fwrite(mask.data(), 1, mask.size(), mf); fclose(mf); } }\n\t// d_alpha: source ownership follows',1)
        a=variant(a,td/'mask-build',deadline,diagnostic)
        report.update(family=args.family,blur_mode=args.blur_mode,blur_size=args.blur_size)
        for mode in (1,2):
          for inout in (1,2,3):
            w,h=3,1
            src=bytes([0,64,128,192,1 if args.family=='mask' else 128,64,128,192,255,64,128,192])
            case=dict(geometry=[w,h],depth=8,profile='sdr',parameters=a.defaults(w,h),pixels=src,input_padding=3,output_padding=5)
            for q in case['parameters']:
                if q['slot']==11:q['value']=args.blur_mode
                if q['slot']==12:q['value']=args.blur_size
                if q['slot']==5:q['value']=mode
                if q['slot']==2:q['value']=inout
                if q['slot']==6:q['value']=args.background
                if q['slot']==8:q['value']=[255,16,160,48]
            params=[]
            for q in case['parameters']:
                name=next(d['name'] for d in a.binding['parameters'] if d['slot']==q['slot'])
                params.append(name+'='+(','.join(map(str,q['value'])) if isinstance(q['value'],list) else str(q['value'])))
            inp=td/'input.png';im=Image.new('RGBA',(w,h));im.putdata([(r,g,b,al) for al,r,g,b in struct.iter_unpack('<4B',src)]);im.save(inp)
            watches=['function=0x1171d00,arg=stack6,size=224',f'function=0x1171d00,arg=stack5,deref=24,size={len(src)}',f'function=0x1170380,arg=r9,deref=24,size={len(src)}',f'function=0x11749a0,arg=r8,deref=88,size={((w+3)//4)*4*h}']
            cmd=[str(a.worker),'render-trace-png',str(a.aex),str(inp),str(td/'output.png'),'--pixel-format','argb8']
            for watch in watches:cmd+=['--watch',watch]
            proc=subprocess.run(cmd+params,capture_output=True,timeout=30,check=True,env=a.env)
            trace=json.loads(proc.stdout);t=next(t for t in trace['execution_traces'] if t['selector']=='SMART_RENDER')
            assert not t['trace_configuration']['unhookable_watches']
            ws={v['watch_id']:v for v in t['memory_witnesses']}
            state=bytearray.fromhex(ws['watch-1']['after']['hex']);source=bytes.fromhex(ws['watch-2']['before']['hex']);field=bytes.fromhex(ws['watch-3']['before']['hex'])
            assert source==src and state[0x90]==0 and trace['render_error']==0 and trace['guards_intact']
            ld=AexLoader(str(a.aex),verbose=False,fast=True)
            cutoff=ld.read_bytes(0x181504a84,4);assert cutoff==struct.pack('<f',0.0001)
            report['ownership_cutoff_hex']=cutoff.hex()
            def world(data):
                address=ld.bump_alloc(len(data),align=16);ld.write_bytes(address,data)
                header=ld.host_alloc(0x80,align=16);body=bytearray(0x80)
                struct.pack_into('<QIIII',body,0x18,address,w*4,w,h,8);ld.write_bytes(header,bytes(body));return header
            struct.pack_into('<QQ',state,0,world(source),world(field))
            ref=ld.host_alloc(len(state),align=16);ld.write_bytes(ref,bytes(state))
            stages=[];current={}
            def hook(loader,rip,size):
                if rip==0x181170a5b:current['source_argb_bits']=[reg(loader,r) for r in (UC_X86_REG_XMM7,UC_X86_REG_XMM12,UC_X86_REG_XMM13,UC_X86_REG_XMM14)]
                if rip==0x181170b1b:current['interpolated_bits']=reg(loader,UC_X86_REG_XMM2)
                if rip==0x181170c11:current['composed_argb_bits']=[reg(loader,r) for r in (UC_X86_REG_XMM6,UC_X86_REG_XMM1,UC_X86_REG_XMM5,UC_X86_REG_XMM3)]
            for address in (0x181170a5b,0x181170b1b,0x181170c11):ld.add_code_hook(address,hook)
            raw=b''
            for x in range(w):
                current={};out=ld.bump_alloc(4,align=16);ld.write_bytes(out,b'\xee'*4)
                ld.call_function(0x181170870,int_args=[ref,x,0,0,out],max_instructions=200000)
                pixel=ld.read_bytes(out,4);raw+=pixel;current['output_hex']=pixel.hex();stages.append(current)
            assert sha(raw)==trace['raw_pixel_sha256'],(mode,inout,raw.hex(),trace['raw_pixel_sha256'])
            debug=td/'mac.trace';debug.unlink(missing_ok=True)
            mask_path=td/'mask.bin';mask_path.unlink(missing_ok=True)
            a.env.update(OLM_DG_C08_MASK_PATH=str(mask_path),OLM_DG_DEBUG_DUMP_PATH=str(debug),OLM_DG_SHADE_DEBUG_PATH=str(debug),OLM_DG_DEBUG_POINTS='0,0;1,0;2,0')
            status,mac,_=a.candidate(case,td,'smart',deadline);assert status['status']=='ok'
            shades=[dict(token.split('=',1) for token in line.split()[1:]) for line in debug.read_text().splitlines() if line.startswith('shade ')]
            for x,s in enumerate(shades):
                stages[x]['mac_source_argb_bits']=[bits(float(s['src_'+ch])) for ch in 'argb']
                stages[x]['mac_composed_argb_bits']=[bits(float(s['out_'+ch])) for ch in 'argb']
                stages[x]['mac_field_bits']=bits(float(s['field_x']))
                stages[x]['aex_field_bits']=bits(field[x*4+1]/255)
                assert stages[x]['source_argb_bits']==stages[x]['mac_source_argb_bits']
                # Field equality is evidence to report, not an input assumption.
            report['rows'].append(dict(mode=mode,inout=inout,background=args.background,source_hex=source.hex(),field_hex=field.hex(),
                refcon_numerical_hex=state[0x90:].hex(),aex_hex=raw.hex(),mac_hex=mac.hex(),diff=raw_diff(raw,mac,8),
                public_callback_sha256=sha(raw),source_and_field_equal=all(v['mac_field_bits']==v['aex_field_bits'] for v in stages),mac_mask_hex=mask_path.read_bytes().hex(),aex_mask_hex=ws['watch-4']['after']['hex'],stages=stages,watches=watches))
    args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('PASS',len(report['rows']),'natural public/callback bindings; source equal')
    for row in report['rows']:print(row['mode'],row['inout'],row['aex_hex'],row['mac_hex'])

if __name__=='__main__':main()
