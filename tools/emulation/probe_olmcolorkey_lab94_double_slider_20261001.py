#!/usr/bin/env python3
"""Authored DOUBLE slider values within native FLOAT32 Lab94 boundary bins."""
import argparse,json,tempfile
from pathlib import Path
import probe_olmcolorkey_typed_controls_20261001 as owner
import probe_olmcolorkey_lab_state_boundary_20261001 as independent
from colorkey_lab94_scalar_candidate_20261001 import candidate_source
BASE_REPORT=owner.ROOT/'reports/colorkey_lab94_controlled_owner_20261001.json'
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--worker',type=Path,required=True);ap.add_argument('--report',type=Path,required=True);args=ap.parse_args();base=json.loads(BASE_REPORT.read_text());assert owner.sha(args.worker.read_bytes())==base['controlled_worker_sha256'];source=owner.SOURCE.read_text();candidate=candidate_source(source);cases=[];owner.fixture=independent.fixture
    with tempfile.TemporaryDirectory(prefix='olmck_lab94_double_slider_') as td:
        temp=Path(td);executables={'production':owner.compile_public(temp/'production',source),'candidate':owner.compile_public(temp/'candidate',candidate)}
        for search in base['searches']:
            assert search['first_matched_bits']==search['last_unmatched_bits']+1
            lo=independent.number(search['last_unmatched_bits']);hi=independent.number(search['first_matched_bits']);precision=int(search['label'][-1]);depth=search['depth']
            for per_color in (False,True):
                for numerator in range(-8,25):
                    threshold=lo+(hi-lo)*(numerator/16)
                    c={'fixture':{'id':'lab94_double_slider','width':1,'height':1,'opaque':True,'rgb':[44,75,119]},'depth':depth,'label':f'lab94_scalar_precision{precision}_percolor{per_color}_fraction{numerator}/16','double_threshold_hex':threshold.hex(),'materialized_threshold_bits':independent.bits(threshold),'parameters':independent.controls(4,False,precision,'single',True,per_color,threshold,replace=False)}
                    native,frame,payload,close=owner.native_render(args.worker,temp,c);raw,_=owner.fixture(c['fixture'],depth);c.update(input_sha256=owner.sha(raw),actual_sha256=owner.sha(native),raw_pixel_bytes=len(native),parameter_payload=payload,frame_done=frame,session_clean=close['session_clean'],unsupported_suite_calls=close['unsupported_suite_calls'],reference_kind='controlled-host-f32-atan2f',results={name:independent.compare(exe,temp,c,native) for name,exe in executables.items()});cases.append(c)
            print('LAB94_DOUBLE_SLIDER',precision,depth,len(cases),sum(c['results']['production']['classic']['exact'] for c in cases),flush=True)
    summary={name:{route:sum(c['results'][name][route]['exact'] for c in cases) for route in ('classic','smart')} for name in executables}
    r={'schema':'olmcolorkey.lab94-double-slider/1','case_count':len(cases),'summary':summary,'source_sha256':owner.sha(source.encode()),'candidate_source_sha256':owner.sha(candidate.encode()),'aex_sha256':owner.sha(owner.AEX.read_bytes()),'controlled_worker_sha256':base['controlled_worker_sha256'],'dependencies_sha256':{str(p.relative_to(owner.ROOT)):owner.sha(p.read_bytes()) for p in (Path(__file__),Path(owner.__file__),Path(independent.__file__),Path(__file__).with_name('colorkey_lab94_scalar_candidate_20261001.py'),owner.HARNESS,BASE_REPORT)},'cases':cases,'claims_not_made':['Controlled atan2f is not native Windows UCRT proof','No full threshold/palette/geometry/HDR/AE completion','Frozen reference failures remain separate','No resident per-frame parameter readback claimed']}
    head=dict(r);del head['cases'];text=json.dumps(head,sort_keys=True,indent=2)[:-2]+',\n  "cases": [\n'+',\n'.join('    '+json.dumps(c,sort_keys=True) for c in cases)+'\n  ]\n}\n';args.report.write_text(text);assert json.loads(text)==r;print('RESULT',summary,flush=True)
if __name__=='__main__':main()
