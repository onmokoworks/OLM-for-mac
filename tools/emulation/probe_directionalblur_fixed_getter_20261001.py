#!/usr/bin/env python3
"""Drive the real Windows parameter builder; compare fixed getters and renders."""
import argparse
import hashlib
import json
import math
import struct
import subprocess
import tempfile
from pathlib import Path
import probe_directionalblur_general_input_20261001 as owner
from aex_loader import AexLoader
from unicorn.x86_const import UC_X86_REG_RSP

ROOT=owner.ROOT
HARNESS=ROOT/'tools/emulation/directionalblur_fixed_getter_harness_20261001.cpp'
OFFSETS={3:0x30,7:0x40,12:0x44,15:0x2c,19:0x810c}
VALUES=(0,.25,.75,.9999847412109375,1,1.25,25.75,99.99998474121094,100)
SIGNED=(-32768,-17.25,-1,-.75,-.25,-.0000152587890625,0,.25,1.25,17.25,32767.99998474121)
def sha(data):return hashlib.sha256(data).hexdigest()
def fixed(value):return math.floor(value*65536+.5) if value>=0 else math.ceil(value*65536-.5)
def build_native(slot,value):
    loader=AexLoader(str(owner.AEX),verbose=False,fast=False)
    values={1:17.25,2:1,3:0,5:4,6:0,7:0,10:3,11:0,12:0,15:0,16:1,18:1,19:0,20:3};values[slot]=value
    calls=[];checkins=[]
    def checkout(ld,args):
        sp=ld.uc.reg_read(UC_X86_REG_RSP);out=struct.unpack('<Q',ld.read_bytes(sp+0x30,8))[0];s=args[1]
        buf=bytearray(0xb0);v=values[s]
        if s in (1,3,7,12,15,19):struct.pack_into('<i',buf,0x38,fixed(v))
        elif s in (2,20):struct.pack_into('<d',buf,0x38,v)
        else:struct.pack_into('<i',buf,0x38,v)
        ld.write_bytes(out,bytes(buf));calls.append(s);return 0
    def checkin(ld,args):checkins.append(args[1]);return 0
    cb=loader.install_callback('fixed.checkout',checkout);ci=loader.install_callback('fixed.checkin',checkin)
    ind=loader.bump_alloc(0x200,align=16);loader.write_bytes(ind,b'\0'*0x200);loader.write_bytes(ind,struct.pack('<QQ',cb,ci));loader.write_bytes(ind+0xe4,struct.pack('<i',1));loader.write_bytes(ind+0xf0,struct.pack('<i',24))
    ctx=loader.bump_alloc(0x8200,align=16);loader.write_bytes(ctx,b'\0'*0x8200)
    result=loader.call_function(0x180006c50,int_args=[ind,0,0,0,ctx],max_instructions=20000)
    if result['rax']!=0 or calls!=list(values) or len(checkins)!=14:raise RuntimeError('builder callback contract failed')
    imports=sorted({c.name for c in loader.import_log})
    if imports!=['memset']:raise RuntimeError('unexpected builder imports: '+str(imports))
    raw=loader.read_bytes(ctx,0x8200);bits=struct.unpack_from('<I',raw,OFFSETS[slot])[0]
    return {'normalized_bits':bits,'context_sha256':sha(raw),'checkout_slots':calls,'checkin_count':len(checkins),'executed_imports':imports}
def compile_harness(binary,sanitize=False):
    original=owner.HARNESS
    try:owner.HARNESS=HARNESS;owner.compile_harness(binary,sanitize)
    finally:owner.HARNESS=original
def native_render(worker,temp,data,slot,value,w,h,depth):
    values={1:17.25,2:1,3:0,5:4,6:0,7:0,10:3,11:0,12:0,15:0,16:1,18:1,19:0,20:3};values[slot]=value
    payload='v4|'+';'.join(f'param_{s}@{s}:{"angle" if s in (1,19) else "f64"}={v}' for s,v in values.items())
    req={'v':4,'type':'render_frame','frame_index':0,'current_time':{'value':0,'scale':24,'step':1,'total':1},'parameters':payload}
    message=json.dumps(req).encode();ip=temp/'input.raw';op=temp/'output.raw';ip.write_bytes(data)
    fmt={8:'argb8',16:'argb16',32:'argb32f'}[depth]
    run=subprocess.run([str(worker),'session',str(owner.AEX),str(ip),str(op),str(w),str(h),'24','--pixel-format',fmt],input=struct.pack('<I',len(message))+message,capture_output=True,check=True)
    messages=[];pos=0
    while pos<len(run.stdout):
        n=struct.unpack_from('<I',run.stdout,pos)[0];pos+=4;messages.append(json.loads(run.stdout[pos:pos+n]));pos+=n
    frame=next(m for m in messages if m['type']=='frame_done');raw=op.read_bytes()
    if frame['render_error'] or frame['status']!='ok' or frame['output']['render_path']!='smartfx' or not frame['output']['guards_intact'] or frame['output']['checksum']!=sha(raw):raise RuntimeError('native render failed')
    return raw,frame,payload
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--worker',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--core-candidate',action='store_true');args=ap.parse_args()
    getters=[];renders=[]
    with tempfile.TemporaryDirectory(prefix='dblur_fixed_') as td:
        temp=Path(td);binary=temp/'mac';compile_harness(binary)
        for slot in OFFSETS:
            for value in (SIGNED if slot==19 else VALUES):
                native=build_native(slot,value);control=build_native(slot,math.floor(value))
                data=owner.typed(owner.pixels(7,5,True),8)
                run=subprocess.run([str(binary),'7','5','8',str(slot),str(value)],input=data,check=True,capture_output=True)
                lines=dict(l.split(' ',1) for l in run.stdout.decode().splitlines())
                getters.append({'slot':slot,'value':value,'fixed_bits':fixed(value),'native':native,'whole_control_context_sha256':control['context_sha256'],'native_equals_whole_control':native['context_sha256']==control['context_sha256'],'mac_value':float(lines['INFO']),'mac_normalized_bits':int(lines['BITS']),'getter_exact':int(lines['BITS'])==native['normalized_bits']})
            # Includes sub-unit values and a nonzero feature still requiring
            # a general implementation; record rejection without hiding it.
            for w,h in (((7,5),(9,7),(37,29)) if args.core_candidate else ((7,5),)):
                for value in ((-.25,.75,1.25) if slot==19 else (.25,.75,25.75)):
                    for depth in (8,16,32):
                        data=owner.typed(owner.pixels(w,h,True),depth);win,frame,payload=native_render(args.worker,temp,data,slot,value,w,h,depth)
                        run=subprocess.run([str(binary),str(w),str(h),str(depth),str(slot),str(value)]+(['1'] if args.core_candidate else []),input=data,check=True,capture_output=True);lines=dict(l.split(' ',1) for l in run.stdout.decode().splitlines());err=int(lines['ERROR']);raw=bytes.fromhex(lines['RAW'])
                        renders.append({'slot':slot,'value':value,'depth':depth,'geometry':[w,h],'input_sha256':sha(data),'windows_raw_sha256':sha(win),'mac_error':err,'public_dispatch_error':int(lines['PUBLIC_ERROR']),'mac_materialized_value':float(lines['INFO']),'mac_route':int(lines['ROUTE']),'mac_raw_sha256':sha(raw) if not err else None,'raw_exact':not err and sha(raw)==sha(win),'frame_done':frame,'parameter_payload':payload,'different_bytes':sum(a!=b for a,b in zip(raw,win)) if not err else None,'first_differences':[{'offset':i,'windows':a,'mac':b} for i,(a,b) in enumerate(zip(win,raw)) if a!=b][:12] if not err else [],'classification':'feature_rejected' if err else ('exact' if raw==win else 'numeric_difference')})
    r={'schema':'directionalblur.fixed-getter/1','core_candidate':args.core_candidate,'aex_sha256':sha(owner.AEX.read_bytes()),'worker_sha256':sha(args.worker.read_bytes()),'production_source_sha256':sha(owner.SOURCE.read_bytes()),'probe_sha256':sha(Path(__file__).read_bytes()),'harness_sha256':sha(HARNESS.read_bytes()),'loader_sha256':sha((ROOT/'tools/emulation/aex_loader.py').read_bytes()),'getter_cases':getters,'render_cases':renders,'getter_exact_count':sum(c['getter_exact'] for c in getters),'render_exact_count':sum(c['raw_exact'] for c in renders),'claims_not_made':['No Windows AE/native UCRT proof','Mac dispatcher seam does not prove public checkout','Nonzero general features remain separately tested and incomplete']}
    args.output.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print('GETTER',r['getter_exact_count'],'/',len(getters),'RENDER',r['render_exact_count'],'/',len(renders));print('render classifications',{k:sum(c['classification']==k for c in renders) for k in ('exact','feature_rejected','numeric_difference')})
if __name__=='__main__':main()
