#!/usr/bin/env python3
"""Measure exported Lab94 scalar with explicitly controlled atan2f imports."""
import argparse,copy,json,tempfile
from pathlib import Path
import probe_olmcolorkey_typed_controls_20261001 as owner
import probe_olmcolorkey_lab_state_boundary_20261001 as independent
from colorkey_lab94_scalar_candidate_20261001 import candidate_source
FROZEN_WORKER_SHA256='0eb2f7705598f7b5f53563b9d920274ba094c835ff3dbaaf5f6fb214ec0cfd61'
BUILD_REPORT=owner.ROOT/'reports/colorkey_lab94_controlled_worker_build_20261001.json'
SPACES_REPORT=owner.ROOT/'reports/colorkey_spaces_diagnostics_20261001.json'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--worker',type=Path,required=True);ap.add_argument('--report',type=Path,required=True);args=ap.parse_args()
    build=json.loads(BUILD_REPORT.read_text());assert owner.sha(args.worker.read_bytes())==build['controlled_worker_sha256'];assert build['frozen_worker_sha256']==FROZEN_WORKER_SHA256
    patch=owner.ROOT/'tools/emulation/aexcompat_colorkey_lab94_controlled_atan2f_20261001.patch';assert owner.sha(patch.read_bytes())==build['patch_sha256']
    previous=json.loads(SPACES_REPORT.read_text());source=owner.SOURCE.read_text();candidate=candidate_source(source);original=owner.fixture;cases=[];searches=[];calibration=[]
    def choose_fixture(f,depth):return original(f,depth) if 'profile' in f else independent.fixture(f,depth)
    owner.fixture=choose_fixture
    with tempfile.TemporaryDirectory(prefix='olmck_lab94_controlled_') as td:
        temp=Path(td);executables={'production':owner.compile_public(temp/'production',source),'candidate':owner.compile_public(temp/'candidate',candidate)}
        # Calibrate every previously measured space row before interpreting new scalar rows.
        for old in previous['cases']:
            c={k:copy.deepcopy(old[k]) for k in ('fixture','depth','label','parameters')}
            native,frame,payload,close=owner.native_render(args.worker,temp,c);raw,rb=choose_fixture(c['fixture'],c['depth']);ps={'PF8':4,'PF16':8,'PF32':16}[c['depth']]
            c.update(input_sha256=owner.sha(raw),actual_sha256=owner.sha(native),raw_pixel_bytes=len(native),parameter_payload=payload,frame_done=frame,session_clean=close['session_clean'],unsupported_suite_calls=close['unsupported_suite_calls'],reference_kind='controlled-host-f32-atan2f',results={name:independent.compare(exe,temp,c,native) for name,exe in executables.items()})
            if old['reference_status']=='measured':
                row={'label':c['label'],'depth':c['depth'],'input_sha256':c['input_sha256'],'historical_actual_sha256':old['actual_sha256'],'controlled_actual_sha256':c['actual_sha256'],'input_preserved':c['input_sha256']==old['input_sha256'],'exact':c['actual_sha256']==old['actual_sha256']};calibration.append(row);c['historical_calibration']=row['exact']
            else:c['historical_reference_failure']='Frozen worker lacks atan2f; not native Windows refusal'
            cases.append(c)
            if len(cases)%72==0:print('CONTROLLED_SPACE',len(cases),sum(v['exact'] for v in calibration),flush=True)
        assert all(v['exact'] and v['input_preserved'] for v in calibration), 'Controlled reference calibration differs; do not promote'
        for c in independent.state_cases():
            values={v['slot']:v.get('value') for v in c['parameters']}
            if values[5]!=3 or values[8]!=0:continue
            c['label']=c['label'].replace('lab3_','lab94_scalar_');next(v for v in c['parameters'] if v['slot']==5)['value']=4
            native,frame,payload,close=owner.native_render(args.worker,temp,c);raw,_=choose_fixture(c['fixture'],c['depth']);c.update(input_sha256=owner.sha(raw),actual_sha256=owner.sha(native),raw_pixel_bytes=len(native),parameter_payload=payload,frame_done=frame,session_clean=close['session_clean'],unsupported_suite_calls=close['unsupported_suite_calls'],reference_kind='controlled-host-f32-atan2f',results={name:independent.compare(exe,temp,c,native) for name,exe in executables.items()});cases.append(c)
        for precision in (1,2,3):
            for depth in ('PF8','PF16','PF32'):
                c={'fixture':{'id':'independent_lab94_boundary','width':1,'height':1,'opaque':True,'rgb':[44,75,119]},'depth':depth,'label':f'lab94_scalar_precision{precision}','parameters':independent.controls(4,False,precision,'single',True,False,0,replace=False)}
                low,high=independent.bits(0),independent.bits(1);trace=[]
                while high-low>1:
                    mid=(low+high)//2;trial=independent.set_threshold(c,independent.number(mid));native,_,_,_=owner.native_render(args.worker,temp,trial);hit=any(native[:{'PF8':1,'PF16':2,'PF32':4}[depth]]);trace.append({'threshold_bits':mid,'matched':hit,'actual_sha256':owner.sha(native)})
                    if hit:high=mid
                    else:low=mid
                searches.append({'label':c['label'],'depth':depth,'last_unmatched_bits':low,'first_matched_bits':high,'trace':trace})
                for tb in range(low-2,high+3):
                    trial=independent.set_threshold(c,independent.number(tb));trial['threshold_bits']=tb;native,frame,payload,close=owner.native_render(args.worker,temp,trial);raw,_=choose_fixture(trial['fixture'],depth);trial.update(input_sha256=owner.sha(raw),actual_sha256=owner.sha(native),raw_pixel_bytes=len(native),parameter_payload=payload,frame_done=frame,session_clean=close['session_clean'],unsupported_suite_calls=close['unsupported_suite_calls'],reference_kind='controlled-host-f32-atan2f',results={name:independent.compare(exe,temp,trial,native) for name,exe in executables.items()});cases.append(trial)
                print('CONTROLLED_LAB94_BOUNDARY',precision,depth,independent.number(low),independent.number(high),flush=True)
    owner.fixture=original
    summary={name:{route:sum(c['results'][name][route]['exact'] for c in cases) for route in ('classic','smart')} for name in executables}
    r={'schema':'olmcolorkey.lab94-controlled-owner/1','case_count':len(cases),'summary':summary,'calibration_count':len(calibration),'calibration_exact_count':sum(c['exact'] for c in calibration),'historical_reference_failures_measured':36,'source_sha256':owner.sha(source.encode()),'candidate_source_sha256':owner.sha(candidate.encode()),'controlled_worker_sha256':build['controlled_worker_sha256'],'frozen_worker_sha256':FROZEN_WORKER_SHA256,'aex_sha256':owner.sha(owner.AEX.read_bytes()),'dependencies_sha256':{str(p.relative_to(owner.ROOT)):owner.sha(p.read_bytes()) for p in (Path(__file__),Path(owner.__file__),Path(independent.__file__),Path(__file__).with_name('colorkey_lab94_scalar_candidate_20261001.py'),owner.HARNESS,patch,BUILD_REPORT,SPACES_REPORT)},'searches':searches,'cases':cases,'claims_not_made':['Controlled host FLOAT32 atan2 is not native Windows UCRT proof','Frozen worker remains unchanged and its 36 failures remain genuine','Calibration is bounded to the measured rows','No full-color/threshold/geometry/HDR/state/ROI/downsample or installed AE completion','Resident payload is slot/type bound; per-frame parameter readback unavailable']}
    head=dict(r);del head['cases'];text=json.dumps(head,sort_keys=True,indent=2)[:-2]+',\n  "cases": [\n'+',\n'.join('    '+json.dumps(c,sort_keys=True) for c in cases)+'\n  ]\n}\n';args.report.write_text(text);assert json.loads(text)==r;print('RESULT',summary,flush=True)
if __name__=='__main__':main()
