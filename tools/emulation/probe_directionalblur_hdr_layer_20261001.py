#!/usr/bin/env python3
"""Compare independent signed/HDR Layers through the real AEX Smart entry."""
import argparse,json,subprocess,tempfile
from pathlib import Path
import probe_directionalblur_hdr_20261001 as hdr
import probe_directionalblur_layer_general_20261001 as layer
import probe_directionalblur_fixed_getter_20261001 as fixed
owner=layer.owner
sha=layer.sha
HARNESS=layer.HARNESS
PROFILES=('positive_hdr','signed_rgb','extended_alpha','extreme_finite','float_boundary')
def input_pixels(w,h,profile):
    return owner.typed(owner.pixels(w,h,True),32) if profile=='sdr' else hdr.pixels(w,h,profile)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--worker',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args();cases=[]
    with tempfile.TemporaryDirectory(prefix='dblur_hdr_layer_') as td:
        temp=Path(td);binary=temp/'mac';previous=fixed.HARNESS
        try:fixed.HARNESS=HARNESS;fixed.compile_harness(binary)
        finally:fixed.HARNESS=previous
        for w,h in ((9,7),(37,29)):
            for layer_profile in PROFILES:
                field=hdr.pixels(w,h,layer_profile)
                for input_profile in ('sdr',layer_profile):
                    data=input_pixels(w,h,input_profile)
                    for mode,controls in [('front',{5:7,10:0,1:123.5}),('back',{5:0,10:11,1:-17.25}),('dual',{5:7,10:11,1:17.25})]:
                        for name,more in [('noise',{}),('components',{3:37.75,7:31.75,12:63.75}),('fade',{3:37.75,7:31.75,12:63.75,6:5,11:7,2:2.25})]:
                            params={**controls,**more}
                            native,frame,payload,_=layer.native_render(args.worker,temp,data,field,params,w,h,32)
                            q=subprocess.run([str(binary),str(w),str(h),'32',','.join(f'{s}={v}' for s,v in params.items())],input=data+field,check=False,capture_output=True)
                            lines=dict(l.split(' ',1) for l in q.stdout.decode().splitlines()) if q.returncode==0 else {};raw=bytes.fromhex(lines.get('RAW',''));err=int(lines['ERROR']) if q.returncode==0 else q.returncode
                            cases.append({'geometry':[w,h],'input_profile':input_profile,'layer_profile':layer_profile,'mode':mode,'feature':name,'parameters':params,'input_sha256':sha(data),'layer_sha256':sha(field),'native_raw_sha256':sha(native),'mac_raw_sha256':sha(raw) if not err else None,'mac_error':err,'mac_process_returncode':q.returncode,'public_dispatch_error':int(lines['PUBLIC_ERROR']) if q.returncode==0 else None,'mac_route':int(lines['ROUTE']) if q.returncode==0 else None,'exact':not err and raw==native,'different_bytes':sum(a!=b for a,b in zip(raw,native)) if not err else None,'first_differences':[{'offset':i,'native':a,'mac':b} for i,(a,b) in enumerate(zip(native,raw)) if a!=b][:12],'frame_done':frame,'parameter_payload':payload})
    r={'schema':'directionalblur.hdr-layer-owner/1','production_source_sha256':sha(owner.SOURCE.read_bytes()),'probe_sha256':sha(Path(__file__).read_bytes()),'harness_sha256':sha(HARNESS.read_bytes()),'aex_sha256':sha(owner.AEX.read_bytes()),'worker_sha256':sha(args.worker.read_bytes()),'case_count':len(cases),'exact_count':sum(c['exact'] for c in cases),'cases':cases,'claims_not_made':['Type 3 exceeds native declared popup range; no legal normal UI proof','No arbitrary finite float, overflow, nonfinite completion','No different Layer geometry/origin or downsample completion','No actual Windows AE/native UCRT or installed bundle verification']}
    args.output.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print('EXACT',r['exact_count'],'/',len(cases))
if __name__=='__main__':main()
