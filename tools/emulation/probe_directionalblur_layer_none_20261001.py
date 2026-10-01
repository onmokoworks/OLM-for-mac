#!/usr/bin/env python3
"""Observe Type-3 Noise with the actual native default None Layer."""
import argparse,json,tempfile
from pathlib import Path
import probe_directionalblur_general_features_20261001 as feature
owner=feature.owner
sha=feature.sha
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--worker',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args();cases=[]
    with tempfile.TemporaryDirectory(prefix='dblur_layer_none_') as td:
        temp=Path(td)
        for w,h in ((9,7),(16,16),(37,29)):
            for mode,controls in [('front',{5:7,10:0,1:123.5}),('back',{5:0,10:11,1:-17.25}),('dual',{5:7,10:11,1:17.25})]:
                for name,more in [('noise',{}),('components',{3:37.75,7:31.75,12:63.75}),('fade',{3:37.75,7:31.75,12:63.75,6:5,11:7,2:2.25})]:
                    params={**controls,**more,15:73.75,16:3}
                    for depth in (16,32):
                        data=owner.typed(owner.pixels(w,h,True),depth)
                        raw,frame,payload=feature.native_render(args.worker,temp,data,params,w,h,depth)
                        control,control_frame,_=feature.native_render(args.worker,temp,data,{**params,15:0},w,h,depth)
                        cases.append({'geometry':[w,h],'depth':depth,'mode':mode,'feature':name,'parameters':params,'input_sha256':sha(data),'native_raw_sha256':sha(raw),'native_disabled_control_raw_sha256':sha(control),'exact':raw==control,'frame_done':frame,'native_disabled_control_frame_done':control_frame,'parameter_payload':payload})
    report={'schema':'directionalblur.none-layer-native-owner/1','aex_sha256':sha(owner.AEX.read_bytes()),'worker_sha256':sha(args.worker.read_bytes()),'probe_sha256':sha(Path(__file__).read_bytes()),'case_count':len(cases),'exact_count':sum(c['exact'] for c in cases),'cases':cases,'claims_not_made':['Type 3 exceeds declared popup range; no legal normal UI proof','No arbitrary selected-Layer host callback failure completion','No actual AE/native UCRT/installed verification']}
    args.output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print('NATIVE NONE LAYER = DISABLED',report['exact_count'],'/',len(cases))
if __name__=='__main__':main()
