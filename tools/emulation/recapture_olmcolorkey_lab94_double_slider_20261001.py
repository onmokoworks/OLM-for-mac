#!/usr/bin/env python3
"""Fresh production recapture of measured Lab94 DOUBLE-materialization differences."""
import argparse,copy,json,tempfile
from pathlib import Path
import probe_olmcolorkey_typed_controls_20261001 as owner
import probe_olmcolorkey_lab_state_boundary_20261001 as independent
BASE=owner.ROOT/'reports/colorkey_lab94_double_slider_20261001.json'
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--worker',type=Path,required=True);ap.add_argument('--report',type=Path,required=True);args=ap.parse_args();base=json.loads(BASE.read_text());assert owner.sha(args.worker.read_bytes())==base['controlled_worker_sha256'];source=owner.SOURCE.read_text();owner.fixture=independent.fixture;cases=[]
    with tempfile.TemporaryDirectory(prefix='olmck_lab94_double_recapture_') as td:
        temp=Path(td);exe=owner.compile_public(temp/'production',source)
        for old in base['cases']:
            if old['results']['production']['classic']['exact']:continue
            c={k:copy.deepcopy(old[k]) for k in ('fixture','depth','label','parameters','double_threshold_hex','materialized_threshold_bits')};native,frame,payload,close=owner.native_render(args.worker,temp,c);raw,_=owner.fixture(c['fixture'],c['depth']);assert owner.sha(raw)==old['input_sha256'] and owner.sha(native)==old['actual_sha256'] and payload==old['parameter_payload']
            c.update(input_sha256=owner.sha(raw),actual_sha256=owner.sha(native),raw_pixel_bytes=len(native),parameter_payload=payload,frame_done=frame,session_clean=close['session_clean'],unsupported_suite_calls=close['unsupported_suite_calls'],results=independent.compare(exe,temp,c,native));cases.append(c)
    report={'schema':'olmcolorkey.lab94-double-slider-production-recapture/1','case_count':len(cases),'summary':{route:sum(c['results'][route]['exact'] for c in cases) for route in ('classic','smart')},'source_sha256':owner.sha(source.encode()),'controlled_worker_sha256':base['controlled_worker_sha256'],'aex_sha256':base['aex_sha256'],'input_settings_and_native_hashes_preserved':True,'dependencies_sha256':{str(p.relative_to(owner.ROOT)):owner.sha(p.read_bytes()) for p in (Path(__file__),Path(owner.__file__),Path(independent.__file__),owner.HARNESS,BASE)},'cases':cases,'claims_not_made':['Controlled atan2f does not prove native Windows UCRT/AE','No all input/threshold/geometry completion','No resident per-frame parameter readback']}
    head=dict(report);del head['cases'];text=json.dumps(head,sort_keys=True,indent=2)[:-2]+',\n  "cases": [\n'+',\n'.join('    '+json.dumps(c,sort_keys=True) for c in cases)+'\n  ]\n}\n';args.report.write_text(text);assert json.loads(text)==report;print('LAB94_DOUBLE_RECAPTURE',report['case_count'],report['summary'],flush=True)
if __name__=='__main__':main()
