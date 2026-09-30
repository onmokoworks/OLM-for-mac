#!/usr/bin/env python3
"""Measure general deep feature differences before public admission changes."""
import argparse,json,struct,subprocess,tempfile
from pathlib import Path
import probe_directionalblur_fixed_getter_20261001 as fixed
owner=fixed.owner
sha=fixed.sha
HARNESS=owner.ROOT/'tools/emulation/directionalblur_general_features_harness_20261001.cpp'
def native_render(worker,temp,data,overrides,w,h,depth):
    values={1:17.25,2:1,3:0,5:4,6:0,7:0,10:3,11:0,12:0,15:0,16:1,18:1,19:0,20:3};values.update(overrides)
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
    ap=argparse.ArgumentParser();ap.add_argument('--worker',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    cases=[]
    features=[('size',{3:37.75}),('front_sharp',{7:31.75}),('back_sharp',{12:63.75}),('noise1',{15:73.75}),('combined1',{3:37.75,7:31.75,12:63.75,15:73.75}),('combined2',{3:37.75,7:31.75,12:63.75,15:73.75,16:2,18:7,19:-17.25}),('fade',{6:5,11:7}),('combined_fade',{3:37.75,7:31.75,12:63.75,15:73.75,6:5,11:7}),('limits',{3:100,7:100,12:100,15:100,6:100,11:100,16:2,18:1000,19:32767,20:10}),('gain',{3:50,7:50,12:50,15:50,2:2.25,20:1.25})]
    with tempfile.TemporaryDirectory(prefix='dblur_features_') as td:
        temp=Path(td);binary=temp/'mac';previous=fixed.HARNESS
        try:fixed.HARNESS=HARNESS;fixed.compile_harness(binary)
        finally:fixed.HARNESS=previous
        for w,h in ((1,9),(9,7),(37,29)):
            for mode,controls in [('front',{5:7,10:0,1:123.5}),('back',{5:0,10:11,1:-17.25}),('dual',{5:7,10:11,1:17.25})]:
                for name,feature in features:
                    params={**controls,**feature}
                    for depth in (16,32):
                        data=owner.typed(owner.pixels(w,h,True),depth);win,frame,payload=native_render(args.worker,temp,data,params,w,h,depth)
                        run=subprocess.run([str(binary),str(w),str(h),str(depth),','.join(f'{s}={v}' for s,v in params.items())],input=data,check=True,capture_output=True);lines=dict(l.split(' ',1) for l in run.stdout.decode().splitlines());raw=bytes.fromhex(lines['RAW']);error=int(lines['ERROR'])
                        cases.append({'geometry':[w,h],'mode':mode,'feature':name,'depth':depth,'parameters':params,'input_sha256':sha(data),'native_raw_sha256':sha(win),'candidate_raw_sha256':sha(raw) if not error else None,'candidate_error':error,'public_dispatch_error':int(lines['PUBLIC_ERROR']),'mac_route':int(lines['ROUTE']),'exact':not error and raw==win,'different_bytes':sum(a!=b for a,b in zip(raw,win)) if not error else None,'first_differences':[{'offset':i,'native':a,'candidate':b} for i,(a,b) in enumerate(zip(win,raw)) if a!=b][:12],'frame_done':frame,'parameter_payload':payload})
    r={'schema':'directionalblur.general-features-candidate/1','production_source_sha256':sha(owner.SOURCE.read_bytes()),'probe_sha256':sha(Path(__file__).read_bytes()),'harness_sha256':sha(HARNESS.read_bytes()),'aex_sha256':sha(owner.AEX.read_bytes()),'worker_sha256':sha(args.worker.read_bytes()),'loader_sha256':sha((owner.ROOT/'tools/emulation/aex_loader.py').read_bytes()),'case_count':len(cases),'exact_count':sum(c['exact'] for c in cases),'cases':cases,'claims_not_made':['Analysis-only core bypass does not restore public admission','No Windows AE/native UCRT proof','No arbitrary-input completion']}
    args.output.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print('EXACT',r['exact_count'],'/',len(cases))
if __name__=='__main__':main()
