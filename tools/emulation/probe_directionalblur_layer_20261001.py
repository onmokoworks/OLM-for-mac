#!/usr/bin/env python3
"""Compare independent selected Layer Noise worlds against exported AEX Smart."""
import argparse,json,struct,subprocess,tempfile
from pathlib import Path
import probe_directionalblur_general_features_20261001 as feature
import probe_directionalblur_fixed_getter_20261001 as fixed
owner=feature.owner
sha=feature.sha
HARNESS=owner.ROOT/'tools/emulation/directionalblur_layer_harness_20261001.cpp'
def layer_pixels(w,h,profile):
    px=owner.pixels(w,h,True)
    if profile=='inverse':return [(255-r,255-g,255-b,255-a) for r,g,b,a in px]
    if profile=='channels':return [(b,255-r,g,255-a) for r,g,b,a in px]
    raise ValueError(profile)
def native_render(worker,temp,data,layer,overrides,w,h,depth):
    temp=Path(tempfile.mkdtemp(prefix="native_",dir=temp))
    values={1:17.25,2:1,3:0,5:4,6:0,7:0,10:3,11:0,12:0,15:73.75,16:3,18:1,19:0,20:3};values.update(overrides)
    payload='v4|'+';'.join(f'param_{s}@{s}:{"angle" if s in (1,19) else "f64"}={v}' for s,v in values.items())
    lp=temp/'layer.raw';lp.write_bytes(layer)
    manifest=temp/'layers.json';manifest.write_text(json.dumps({'v':1,'layers':[{'slot':17,'width':w,'height':h,'path':str(lp)}]}))
    req={'v':4,'type':'render_frame','frame_index':0,'current_time':{'value':0,'scale':24,'step':1,'total':1},'parameters':payload}
    message=json.dumps(req).encode();ip=temp/'input.raw';op=temp/'output.raw';ip.write_bytes(data)
    fmt={8:'argb8',16:'argb16',32:'argb32f'}[depth]
    run=subprocess.run([str(worker),'session',str(owner.AEX),str(ip),str(op),str(w),str(h),'24','--pixel-format',fmt,'--fixture-layers-v1',str(manifest),'--fixture-render-path','smart'],input=struct.pack('<I',len(message))+message,capture_output=True)
    if run.returncode:raise RuntimeError(run.stderr.decode()[-3000:])
    messages=[];pos=0
    while pos<len(run.stdout):
        n=struct.unpack_from('<I',run.stdout,pos)[0];pos+=4;messages.append(json.loads(run.stdout[pos:pos+n]));pos+=n
    frame=next(m for m in messages if m['type']=='frame_done');raw=op.read_bytes()
    if frame['render_error'] or frame['status']!='ok' or frame['output']['render_path']!='smartfx' or not frame['output']['guards_intact'] or frame['output']['checksum']!=sha(raw):raise RuntimeError('native render failed')
    setup=next(m for m in messages if m['type']=='session_ready')['setup']
    return raw,frame,payload,setup
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--worker',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args();cases=[];declarations=None
    with tempfile.TemporaryDirectory(prefix='dblur_layer_') as td:
        temp=Path(td);binary=temp/'mac';previous=fixed.HARNESS
        try:fixed.HARNESS=HARNESS;fixed.compile_harness(binary)
        finally:fixed.HARNESS=previous
        for w,h in ((9,7),(37,29)):
            for profile in ('inverse','channels'):
                for mode,controls in [('front',{5:7,10:0,1:123.5}),('back',{5:0,10:11,1:-17.25}),('dual',{5:7,10:11,1:17.25})]:
                    for name,more in [('noise',{}),('components',{3:37.75,7:31.75,12:63.75}),('fade',{3:37.75,7:31.75,12:63.75,6:5,11:7,2:2.25})]:
                        params={**controls,**more}
                        for depth in (16,32):
                            data=owner.typed(owner.pixels(w,h,True),depth);layer=owner.typed(layer_pixels(w,h,profile),depth)
                            native,frame,payload,setup=native_render(args.worker,temp,data,layer,params,w,h,depth)
                            if declarations is None:declarations=[p for p in setup['parameters'] if p['slot'] in (16,17)]
                            run=subprocess.run([str(binary),str(w),str(h),str(depth),','.join(f'{s}={v}' for s,v in params.items())],input=data+layer,check=True,capture_output=True);lines=dict(l.split(' ',1) for l in run.stdout.decode().splitlines());raw=bytes.fromhex(lines['RAW']);err=int(lines['ERROR'])
                            cases.append({'geometry':[w,h],'depth':depth,'layer_profile':profile,'mode':mode,'feature':name,'parameters':params,'input_sha256':sha(data),'layer_sha256':sha(layer),'native_raw_sha256':sha(native),'mac_raw_sha256':sha(raw) if not err else None,'mac_error':err,'public_dispatch_error':int(lines['PUBLIC_ERROR']),'mac_route':int(lines['ROUTE']),'exact':not err and raw==native,'different_bytes':sum(a!=b for a,b in zip(raw,native)) if not err else None,'first_differences':[{'offset':i,'native':a,'mac':b} for i,(a,b) in enumerate(zip(native,raw)) if a!=b][:12],'frame_done':frame,'parameter_payload':payload})
    r={'schema':'directionalblur.independent-layer-owner/1','production_source_sha256':sha(owner.SOURCE.read_bytes()),'probe_sha256':sha(Path(__file__).read_bytes()),'harness_sha256':sha(HARNESS.read_bytes()),'aex_sha256':sha(owner.AEX.read_bytes()),'worker_sha256':sha(args.worker.read_bytes()),'native_layer_parameter_declarations':declarations,'case_count':len(cases),'exact_count':sum(c['exact'] for c in cases),'cases':cases,'claims_not_made':['Core bypass is analysis only','No mismatched Layer size/origin completion','No Windows AE/native UCRT proof']}
    args.output.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print('EXACT',r['exact_count'],'/',len(cases));print('LAYER PARAMETERS',declarations)
if __name__=='__main__':main()
