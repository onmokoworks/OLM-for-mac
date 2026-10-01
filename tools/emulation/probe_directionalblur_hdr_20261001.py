#!/usr/bin/env python3
"""Measure arbitrary signed/HDR float worlds against the exported AEX owner."""
import argparse,json,struct,subprocess,tempfile
from pathlib import Path
import probe_directionalblur_general_features_20261001 as feature
import probe_directionalblur_fixed_getter_20261001 as fixed
owner=feature.owner
sha=feature.sha

def pixels(width,height,profile):
    out=[]
    for i,(r,g,b,a) in enumerate(owner.pixels(width,height,True)):
        rgb=[c/255*8+.125 for c in (r,g,b)];alpha=a/255
        if profile=='signed_rgb':rgb=[(-v if (i+j)%3==0 else v) for j,v in enumerate(rgb)]
        elif profile=='extended_alpha':alpha=-.5 if i%4==0 else alpha*2
        elif profile=='extreme_finite':rgb=[v*1e28*(-1 if (i+j)%3==0 else 1) for j,v in enumerate(rgb)]
        elif profile=='float_boundary':rgb=[struct.unpack('<f',struct.pack('<I',(0x80000000,0x3f800001,0x80000001,0x00000001,0x3f7fffff)[(i+j)%5]))[0] for j in range(3)]
        elif profile!='positive_hdr':raise ValueError(profile)
        out.append(struct.pack('<4f',alpha,*rgb))
    return b''.join(out)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--worker',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args();cases=[]
    with tempfile.TemporaryDirectory(prefix='dblur_hdr_') as td:
        temp=Path(td);binary=temp/'mac';previous=fixed.HARNESS
        try:fixed.HARNESS=feature.HARNESS;fixed.compile_harness(binary)
        finally:fixed.HARNESS=previous
        for w,h in ((9,7),(37,29)):
            for profile in ('positive_hdr','signed_rgb','extended_alpha','extreme_finite','float_boundary'):
                data=pixels(w,h,profile)
                for mode,controls in [('front',{5:7,10:0,1:123.5}),('back',{5:0,10:11,1:-17.25}),('dual',{5:7,10:11,1:17.25})]:
                    for name,more in [('neutral',{}),('components',{3:37.75,7:31.75,12:63.75}),('noise',{15:73.75,16:2,18:7}),('combined',{3:37.75,7:31.75,12:63.75,15:73.75,6:5,11:7,2:2.25})]:
                        params={**controls,**more};native,frame,payload=feature.native_render(args.worker,temp,data,params,w,h,32)
                        run=subprocess.run([str(binary),str(w),str(h),'32',','.join(f'{s}={v}' for s,v in params.items())],input=data,check=True,capture_output=True)
                        lines=dict(l.split(' ',1) for l in run.stdout.decode().splitlines());raw=bytes.fromhex(lines['RAW']);err=int(lines['ERROR'])
                        cases.append({'geometry':[w,h],'profile':profile,'mode':mode,'feature':name,'parameters':params,'input_sha256':sha(data),'native_raw_sha256':sha(native),'mac_raw_sha256':sha(raw) if not err else None,'mac_error':err,'public_dispatch_error':int(lines['PUBLIC_ERROR']),'mac_route':int(lines['ROUTE']),'exact':not err and raw==native,'different_bytes':sum(a!=b for a,b in zip(raw,native)) if not err else None,'first_differences':[{'offset':i,'native':a,'mac':b} for i,(a,b) in enumerate(zip(native,raw)) if a!=b][:12],'frame_done':frame,'parameter_payload':payload})
    r={'schema':'directionalblur.hdr-owner/1','production_source_sha256':sha(owner.SOURCE.read_bytes()),'probe_sha256':sha(Path(__file__).read_bytes()),'harness_sha256':sha(feature.HARNESS.read_bytes()),'aex_sha256':sha(owner.AEX.read_bytes()),'worker_sha256':sha(args.worker.read_bytes()),'case_count':len(cases),'exact_count':sum(c['exact'] for c in cases),'cases':cases,'claims_not_made':['Core bypass is analysis only','No Windows AE/native UCRT proof','No arbitrary float or nonfinite completion']}
    args.output.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print('EXACT',r['exact_count'],'/',len(cases))
if __name__=='__main__':main()
