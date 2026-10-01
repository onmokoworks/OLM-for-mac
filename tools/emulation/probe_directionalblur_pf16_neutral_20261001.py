#!/usr/bin/env python3
"""Compare the existing neutral kernel on authored raw uint16 range inputs."""
import argparse,json,subprocess,tempfile
from pathlib import Path
import probe_directionalblur_pf16_range_20261001 as range_probe
import probe_directionalblur_general_features_20261001 as feature
import probe_directionalblur_fixed_getter_20261001 as fixed
owner=range_probe.owner
sha=range_probe.sha
HARNESS=owner.ROOT/'tools/emulation/directionalblur_pf16_neutral_harness_20261001.cpp'
def specifications(w,h):
    for mode,controls in [('front',{5:7,10:0,1:123.5}),('back',{5:0,10:11,1:-17.25}),('dual',{5:7,10:11,1:17.25})]:
        for gain in (0,1,2.25):yield mode,{**controls,2:gain}
    if (w,h)==(16,16):
        for back in (1,2,8):yield 'retained_back',{5:0,10:back,1:45,2:1}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--worker',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args();cases=[]
    with tempfile.TemporaryDirectory(prefix='dblur_pf16_neutral_') as td:
        temp=Path(td);binary=temp/'mac';previous=fixed.HARNESS
        try:fixed.HARNESS=HARNESS;fixed.compile_harness(binary)
        finally:fixed.HARNESS=previous
        for w,h in ((9,7),(16,16),(37,29)):
            for profile in ('sdr','rgb_extended','alpha_extended','all_extended','boundary'):
                data=range_probe.pixels(w,h,profile)
                for mode,controls in specifications(w,h):
                    params={**controls,3:0,6:0,7:0,11:0,12:0,15:0,16:1}
                    native,frame,payload=feature.native_render(args.worker,temp,data,params,w,h,16)
                    run=subprocess.run([str(binary),str(w),str(h),'16',','.join(f'{s}={v}' for s,v in params.items())],input=data,check=True,capture_output=True)
                    lines=dict(l.split(' ',1) for l in run.stdout.decode().splitlines());raw=bytes.fromhex(lines['RAW']);err=int(lines['ERROR'])
                    cases.append({'geometry':[w,h],'depth':16,'profile':profile,'mode':mode,'parameters':params,'input_sha256':sha(data),'native_raw_sha256':sha(native),'mac_raw_sha256':sha(raw) if not err else None,'mac_error':err,'public_dispatch_error':int(lines['PUBLIC_ERROR']),'mac_route':int(lines['ROUTE']),'exact':not err and raw==native,'different_bytes':sum(a!=b for a,b in zip(raw,native)) if not err else None,'first_differences':[{'offset':i,'native':a,'mac':b} for i,(a,b) in enumerate(zip(native,raw)) if a!=b][:12],'frame_done':frame,'parameter_payload':payload})
    r={'schema':'directionalblur.pf16-neutral-owner/1','production_source_sha256':sha(owner.SOURCE.read_bytes()),'probe_sha256':sha(Path(__file__).read_bytes()),'harness_sha256':sha(HARNESS.read_bytes()),'aex_sha256':sha(owner.AEX.read_bytes()),'worker_sha256':sha(args.worker.read_bytes()),'case_count':len(cases),'exact_count':sum(c['exact'] for c in cases),'public_exact_count':sum(c['exact'] and not c['public_dispatch_error'] for c in cases),'cases':cases,'claims_not_made':['No normal AE UI production of non-SDR uint16 worlds proved','Rejected public inputs use the existing neutral kernel for analysis only','No Windows AE/native UCRT proof','No arbitrary geometry/settings completion']}
    args.output.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print('EXACT',r['exact_count'],'/',len(cases),'PUBLIC',r['public_exact_count'])
if __name__=='__main__':main()
