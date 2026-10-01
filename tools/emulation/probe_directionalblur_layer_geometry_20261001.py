#!/usr/bin/env python3
"""Measure independent differently sized Layers at the exported AEX Smart entry."""
import argparse,json,struct,subprocess,tempfile
from pathlib import Path
import probe_directionalblur_layer_general_20261001 as layer_owner
import probe_directionalblur_fixed_getter_20261001 as fixed
owner=layer_owner.owner
sha=layer_owner.sha
HARNESS=owner.ROOT/'tools/emulation/directionalblur_layer_geometry_harness_20261001.cpp'
def crop_layer(data,w,h,lw,lh,depth):
    ps=8 if depth==16 else 16
    out=bytearray(w*h*ps)
    for y in range(min(h,lh)):
        out[y*w*ps:y*w*ps+min(w,lw)*ps]=data[y*lw*ps:y*lw*ps+min(w,lw)*ps]
    return bytes(out)
def native_render(worker,temp,data,layer,overrides,w,h,depth,lw,lh):
    temp=Path(tempfile.mkdtemp(prefix="native_",dir=temp))
    values={1:17.25,2:1,3:0,5:4,6:0,7:0,10:3,11:0,12:0,15:73.75,16:3,18:1,19:0,20:3};values.update(overrides)
    payload='v4|'+';'.join(f'param_{s}@{s}:{"angle" if s in (1,19) else "f64"}={v}' for s,v in values.items())
    lp=temp/'layer.raw';lp.write_bytes(layer)
    manifest=temp/'layers.json';manifest.write_text(json.dumps({'v':1,'layers':[{'slot':17,'width':lw,'height':lh,'path':str(lp)}]}))
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
    ap=argparse.ArgumentParser();ap.add_argument('--worker',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args();cases=[]
    with tempfile.TemporaryDirectory(prefix='dblur_layer_geometry_') as td:
        temp=Path(td);binary=temp/'mac';previous=fixed.HARNESS
        try:fixed.HARNESS=HARNESS;fixed.compile_harness(binary)
        finally:fixed.HARNESS=previous
        for w,h in ((9,7),(37,29)):
            for shape,(lw,lh) in [('smaller',(w-4,h-3)),('larger',(w+4,h+2)),('wide_short',(w+5,h-2)),('narrow_tall',(w-3,h+4))]:
                for profile in ('inverse','channels'):
                    for mode,controls in [('front',{5:7,10:0,1:123.5}),('back',{5:0,10:11,1:-17.25}),('dual',{5:7,10:11,1:17.25})]:
                        for name,more in [('noise',{}),('components',{3:37.75,7:31.75,12:63.75}),('fade',{3:37.75,7:31.75,12:63.75,6:5,11:7,2:2.25})]:
                            params={**controls,**more}
                            for depth in (16,32):
                                data=owner.typed(owner.pixels(w,h,True),depth);field=owner.typed(layer_owner.layer_pixels(lw,lh,profile),depth);cropped=crop_layer(field,w,h,lw,lh,depth)
                                native,frame,payload,_=native_render(args.worker,temp,data,field,params,w,h,depth,lw,lh)
                                control,control_frame,_,_=native_render(args.worker,temp,data,cropped,params,w,h,depth,w,h)
                                run=subprocess.run([str(binary),str(w),str(h),str(depth),','.join(f'{s}={v}' for s,v in params.items()),str(lw),str(lh)],input=data+field,check=True,capture_output=True)
                                lines=dict(l.split(' ',1) for l in run.stdout.decode().splitlines());raw=bytes.fromhex(lines['RAW']);err=int(lines['ERROR'])
                                cases.append({'geometry':[w,h],'layer_geometry':[lw,lh],'layer_shape':shape,'depth':depth,'layer_profile':profile,'mode':mode,'feature':name,'parameters':params,'input_sha256':sha(data),'layer_sha256':sha(field),'cropped_layer_sha256':sha(cropped),'native_raw_sha256':sha(native),'native_cropped_control_raw_sha256':sha(control),'native_cropped_control_exact':native==control,'mac_raw_sha256':sha(raw) if not err else None,'mac_error':err,'public_dispatch_error':int(lines['PUBLIC_ERROR']),'mac_route':int(lines['ROUTE']),'exact':not err and raw==native,'different_bytes':sum(a!=b for a,b in zip(raw,native)) if not err else None,'first_differences':[{'offset':i,'native':a,'mac':b} for i,(a,b) in enumerate(zip(native,raw)) if a!=b][:12],'frame_done':frame,'native_cropped_control_frame_done':control_frame,'parameter_payload':payload})
    report={'schema':'directionalblur.independent-layer-geometry-owner/1','production_source_sha256':sha(owner.SOURCE.read_bytes()),'core_rowdriver_sha256':sha((owner.ROOT/'core/dblur_rowdriver.cpp').read_bytes()),'probe_sha256':sha(Path(__file__).read_bytes()),'harness_sha256':sha(HARNESS.read_bytes()),'aex_sha256':sha(owner.AEX.read_bytes()),'worker_sha256':sha(args.worker.read_bytes()),'case_count':len(cases),'exact_count':sum(c['exact'] for c in cases),'native_cropped_control_exact_count':sum(c['native_cropped_control_exact'] for c in cases),'cases':cases,'claims_not_made':['Analysis crop adapter alone is not restoration of original Layer geometry admission','Type 3 exceeds native declared popup range; no normal UI proof','No nonzero origin or ROI/downsample completion','No actual AE/native UCRT/installed bundle verification']}
    args.output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print('EXACT',report['exact_count'],'/',len(cases),'NATIVE CROP CONTROLS',report['native_cropped_control_exact_count'])
if __name__=='__main__':main()
