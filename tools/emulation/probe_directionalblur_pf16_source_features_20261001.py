#!/usr/bin/env python3
"""Supplement the raw PF16 Layer witnesses with generated Noise and no Layer."""
import argparse,json,subprocess,tempfile
from pathlib import Path
import probe_directionalblur_pf16_range_20261001 as range_probe
import probe_directionalblur_general_features_20261001 as feature
import probe_directionalblur_fixed_getter_20261001 as fixed
owner=range_probe.owner
sha=range_probe.sha

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--worker',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args();cases=[]
    with tempfile.TemporaryDirectory(prefix='dblur_pf16_source_') as td:
        temp=Path(td);binary=temp/'mac';previous=fixed.HARNESS
        try:fixed.HARNESS=feature.HARNESS;fixed.compile_harness(binary)
        finally:fixed.HARNESS=previous
        for w,h in ((9,7),(37,29)):
            for profile in ('rgb_extended','alpha_extended','all_extended','boundary'):
                data=range_probe.pixels(w,h,profile)
                for mode,controls in [('front',{5:7,10:0,1:123.5}),('back',{5:0,10:11,1:-17.25}),('dual',{5:7,10:11,1:17.25})]:
                    for name,more in [('no_layer',{15:0,16:1}),('generated_1',{15:73.75,16:1,18:7}),('generated_2',{15:73.75,16:2,18:7})]:
                        params={**controls,3:37.75,7:31.75,12:63.75,6:5,11:7,2:2.25,**more}
                        native,frame,payload=feature.native_render(args.worker,temp,data,params,w,h,16)
                        run=subprocess.run([str(binary),str(w),str(h),'16',','.join(f'{s}={v}' for s,v in params.items())],input=data,check=True,capture_output=True)
                        lines=dict(l.split(' ',1) for l in run.stdout.decode().splitlines());raw=bytes.fromhex(lines['RAW']);err=int(lines['ERROR'])
                        cases.append({'geometry':[w,h],'depth':16,'profile':profile,'placement':'source','mode':mode,'feature':name,'parameters':params,'input_sha256':sha(data),'native_raw_sha256':sha(native),'mac_raw_sha256':sha(raw) if not err else None,'mac_error':err,'public_dispatch_error':int(lines['PUBLIC_ERROR']),'mac_route':int(lines['ROUTE']),'exact':not err and raw==native,'different_bytes':sum(a!=b for a,b in zip(raw,native)) if not err else None,'frame_done':frame,'parameter_payload':payload})
    r={'schema':'directionalblur.pf16-source-features-owner/1','production_source_sha256':sha(owner.SOURCE.read_bytes()),'budget_sha256':sha((owner.ROOT/'core/dblur_generic_budget.h').read_bytes()),'probe_sha256':sha(Path(__file__).read_bytes()),'harness_sha256':sha(feature.HARNESS.read_bytes()),'aex_sha256':sha(owner.AEX.read_bytes()),'worker_sha256':sha(args.worker.read_bytes()),'case_count':len(cases),'exact_count':sum(c['exact'] for c in cases),'public_exact_count':sum(c['exact'] and not c['public_dispatch_error'] for c in cases),'cases':cases,'claims_not_made':['No fully neutral non-SDR PF16 admission restored','No normal AE UI production of non-SDR uint16 worlds proved','No Windows AE/native UCRT proof','No arbitrary geometry/settings completion']}
    args.output.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print('EXACT',r['exact_count'],'/',len(cases),'PUBLIC',r['public_exact_count'])
if __name__=='__main__':main()
