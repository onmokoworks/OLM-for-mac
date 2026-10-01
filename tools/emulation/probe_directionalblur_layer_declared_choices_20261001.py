#!/usr/bin/env python3
"""Separate declared Noise Type choices from accepted serialized value 3."""
import argparse,json,tempfile
from pathlib import Path
import probe_directionalblur_layer_20261001 as layer
import probe_directionalblur_general_features_20261001 as feature
sha=layer.sha
owner=layer.owner

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--worker',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args();cases=[];declarations=None
    with tempfile.TemporaryDirectory(prefix='dblur_choices_') as td:
        temp=Path(td)
        for depth in (16,32):
            data=owner.typed(owner.pixels(9,7,True),depth)
            for choice in (1,2):
                params={5:7,10:0,1:123.5,15:73.75,16:choice}
                generated,frame,payload=feature.native_render(args.worker,temp,data,params,9,7,depth)
                rows=[]
                for profile in ('inverse','channels'):
                    raw=owner.typed(layer.layer_pixels(9,7,profile),depth)
                    actual,done,typed,setup=layer.native_render(args.worker,temp,data,raw,params,9,7,depth)
                    if declarations is None:declarations=[p for p in setup['parameters'] if p['slot'] in (16,17)]
                    rows.append({'layer_profile':profile,'layer_sha256':sha(raw),'native_raw_sha256':sha(actual),'matches_unselected_layer':actual==generated,'frame_done':done,'parameter_payload':typed})
                cases.append({'depth':depth,'noise_type':choice,'geometry':[9,7],'parameters':params,'input_sha256':sha(data),'unselected_layer_raw_sha256':sha(generated),'unselected_frame_done':frame,'selected_layer_cases':rows})
    r={'schema':'directionalblur.layer-declared-choices/1','aex_sha256':sha(owner.AEX.read_bytes()),'worker_sha256':sha(args.worker.read_bytes()),'probe_sha256':sha(Path(__file__).read_bytes()),'layer_probe_sha256':sha(Path(layer.__file__).read_bytes()),'native_declarations':declarations,'declared_choice_count':2,'declared_label_count':3,'case_count':len(cases),'selected_layer_case_count':sum(len(c['selected_layer_cases']) for c in cases),'selected_layers_match_generated_count':sum(x['matches_unselected_layer'] for c in cases for x in c['selected_layer_cases']),'cases':cases,'claims_not_made':['Serialized Noise Type 3 witnesses do not prove normal UI selection','No native AE UI behavior verification','No full Layer feature completion']}
    args.output.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print('DECLARED CHOICES SELECTED LAYER MATCHES GENERATED',r['selected_layers_match_generated_count'],'/',r['selected_layer_case_count'])
if __name__=='__main__':main()
