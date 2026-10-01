#!/usr/bin/env python3
"""Observe false full-row budget refusal on authored large SDR/HDR Layer worlds."""
import argparse,json,struct,subprocess,tempfile
from pathlib import Path
import probe_directionalblur_layer_general_20261001 as layer
import probe_directionalblur_hdr_20261001 as hdr
import test_dblur_generic_backonly_effectmain_20260821 as base
owner=layer.owner
sha=layer.sha
HARNESS=owner.ROOT/'tools/emulation/directionalblur_layer_span_budget_effectmain_harness_20261001.cpp'
def source(w,h):
    out=[]
    for y in range(h):
        for x in range(w):
            a=(.375 if (x+y)%2 else 1.0) if x%97==3 and y%71==5 else 0.0
            out.append(struct.pack('<4f',a,(20+(41*x+7*y)%220)/255,(12+(13*x+37*y)%232)/255,(8+(23*x+19*y)%240)/255))
    return b''.join(out)
def field(w,h,profile):
    return owner.typed(layer.layer_pixels(w,h,'inverse'),32) if profile=='sdr' else hdr.pixels(w,h,profile)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--worker',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args();cases=[]
    with tempfile.TemporaryDirectory(prefix='dblur_span_budget_') as td:
        temp=Path(td);previous=base.CPP
        try:
            base.CPP=HARNESS.read_text().replace('../../mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp','__PRODUCTION__');binary=base.build(temp,False)
        finally:base.CPP=previous
        w,h=720,480;data=source(w,h);params={1:17.25,5:7,10:11}
        for profile in ('sdr','positive_hdr','signed_rgb'):
            selected=field(w,h,profile)
            native,frame,payload,_=layer.native_render(args.worker,temp,data,selected,params,w,h,32)
            control,control_frame,_,_=layer.native_render(args.worker,temp,data,selected,{**params,15:0},w,h,32)
            q=subprocess.run([str(binary),str(w),str(h),'32',','.join(f'{s}={v}' for s,v in params.items()),'classic'],input=data+selected,check=True,capture_output=True)
            lines=dict(l.split(' ',1) for l in q.stdout.decode().splitlines());err=int(lines['ERROR']);raw=bytes.fromhex(lines['RAW'])
            cases.append({'geometry':[w,h],'layer_profile':profile,'depth':32,'parameters':params,'input_sha256':sha(data),'layer_sha256':sha(selected),'native_raw_sha256':sha(native),'native_disabled_control_raw_sha256':sha(control),'native_layer_changes_output':native!=control,'mac_error':err,'exact':not err and raw==native,'mac_raw_sha256':sha(raw) if not err else None,'frame_done':frame,'native_disabled_control_frame_done':control_frame,'parameter_payload':payload})
            print(profile,'MAC_ERROR',err,'EXACT',not err and raw==native,flush=True)
    report={'schema':'directionalblur.layer-coefficient-budget-owner/1','production_source_sha256':sha(owner.SOURCE.read_bytes()),'budget_sha256':sha((owner.ROOT/'core/dblur_generic_budget.h').read_bytes()),'rowdriver_sha256':sha((owner.ROOT/'core/dblur_rowdriver.cpp').read_bytes()),'probe_sha256':sha(Path(__file__).read_bytes()),'harness_sha256':sha(HARNESS.read_bytes()),'aex_sha256':sha(owner.AEX.read_bytes()),'worker_sha256':sha(args.worker.read_bytes()),'case_count':len(cases),'exact_count':sum(c['exact'] for c in cases),'cases':cases,'claims_not_made':['No actual Windows AE/native UCRT or installed bundle verification','No arbitrary finite float/overflow or all images completion','Type 3 exceeds native declared popup range; no normal UI proof']}
    args.output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
if __name__=='__main__':main()
