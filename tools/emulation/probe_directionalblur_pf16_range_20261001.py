#!/usr/bin/env python3
"""Witness raw uint16 worlds beyond AE's nominal 32768 white, without clamping."""
import argparse,json,struct,subprocess,tempfile
from pathlib import Path
import probe_directionalblur_layer_general_20261001 as layer
import probe_directionalblur_fixed_getter_20261001 as fixed
owner=layer.owner
sha=layer.sha

def pixels(w,h,profile):
    if profile=='sdr':return owner.typed(owner.pixels(w,h,True),16)
    result=[]
    for i,(r,g,b,a) in enumerate(owner.pixels(w,h,True)):
        values=[(a*32768+127)//255,*[(c*32768+127)//255 for c in (r,g,b)]]
        if profile=='rgb_extended':values[1:]=[32769+(v*32766//32768) for v in values[1:]]
        elif profile=='alpha_extended':values[0]=(32769,49152,65535)[i%3]
        elif profile=='all_extended':values=[(0,32768,32769,49152,65535)[(i+j)%5] for j in range(4)]
        elif profile=='boundary':values=[(32767,32768,32769,65534,65535)[(i+j)%5] for j in range(4)]
        else:raise ValueError(profile)
        result.append(struct.pack('<4H',*values))
    return b''.join(result)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--worker',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args();cases=[]
    with tempfile.TemporaryDirectory(prefix='dblur_pf16_range_') as td:
        temp=Path(td);binary=temp/'mac';previous=fixed.HARNESS
        try:fixed.HARNESS=layer.HARNESS;fixed.compile_harness(binary)
        finally:fixed.HARNESS=previous
        for w,h in ((9,7),(37,29)):
            for profile in ('rgb_extended','alpha_extended','all_extended','boundary'):
                for placement in ('source','layer','both'):
                    data=pixels(w,h,profile if placement!='layer' else 'sdr');field=pixels(w,h,profile if placement!='source' else 'sdr')
                    for mode,controls in [('front',{5:7,10:0,1:123.5}),('back',{5:0,10:11,1:-17.25}),('dual',{5:7,10:11,1:17.25})]:
                        for name,more in [('layer',{}),('combined',{3:37.75,7:31.75,12:63.75,6:5,11:7,2:2.25})]:
                            params={**controls,**more};native,frame,payload,_=layer.native_render(args.worker,temp,data,field,params,w,h,16)
                            run=subprocess.run([str(binary),str(w),str(h),'16',','.join(f'{s}={v}' for s,v in params.items())],input=data+field,check=True,capture_output=True)
                            lines=dict(l.split(' ',1) for l in run.stdout.decode().splitlines());raw=bytes.fromhex(lines['RAW']);err=int(lines['ERROR'])
                            cases.append({'geometry':[w,h],'depth':16,'profile':profile,'placement':placement,'mode':mode,'feature':name,'parameters':params,'input_sha256':sha(data),'layer_sha256':sha(field),'native_raw_sha256':sha(native),'mac_raw_sha256':sha(raw) if not err else None,'mac_error':err,'public_dispatch_error':int(lines['PUBLIC_ERROR']),'mac_route':int(lines['ROUTE']),'exact':not err and raw==native,'different_bytes':sum(a!=b for a,b in zip(raw,native)) if not err else None,'first_differences':[{'offset':i,'native':a,'mac':b} for i,(a,b) in enumerate(zip(native,raw)) if a!=b][:12],'frame_done':frame,'parameter_payload':payload})
    r={'schema':'directionalblur.pf16-range-owner/1','production_source_sha256':sha(owner.SOURCE.read_bytes()),'budget_sha256':sha((owner.ROOT/'core/dblur_generic_budget.h').read_bytes()),'probe_sha256':sha(Path(__file__).read_bytes()),'harness_sha256':sha(layer.HARNESS.read_bytes()),'aex_sha256':sha(owner.AEX.read_bytes()),'worker_sha256':sha(args.worker.read_bytes()),'case_count':len(cases),'exact_count':sum(c['exact'] for c in cases),'public_exact_count':sum(c['exact'] and not c['public_dispatch_error'] for c in cases),'cases':cases,'claims_not_made':['No normal AE UI production of non-SDR uint16 worlds proved','Core bypass is analysis only','No Windows AE/native UCRT proof','No arbitrary geometry/settings completion']}
    args.output.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print('EXACT',r['exact_count'],'/',len(cases),'PUBLIC',r['public_exact_count'])
if __name__=='__main__':main()
