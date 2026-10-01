#!/usr/bin/env python3
"""Independent typed geometry witnesses for the initial-matte recovery."""
import argparse,json,tempfile
from pathlib import Path
import probe_olmcolorkey_typed_controls_20261001 as owner
import colorkey_signed_zero_candidate_20261001 as recovery

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--worker',type=Path,required=True);ap.add_argument('--report',type=Path,required=True);args=ap.parse_args()
    original=owner.SOURCE.read_text();body=recovery.candidate_source(original);cases=[]
    with tempfile.TemporaryDirectory(prefix='olmck_signed_zero_transfer_') as td:
        temp=Path(td);exe=owner.compile_public(temp/'mac',body)
        for w,h in ((1,1),(1,9),(9,1),(17,15)):
            for c in owner.specifications('hdr',w,h):
                source,_=owner.fixture(c['fixture'],c['depth']);native,frame,payload,close=owner.native_render(args.worker,temp,c);c.update(input_sha256=owner.sha(source),actual_sha256=owner.sha(native),raw_pixel_bytes=len(native),parameter_payload=payload,config_sha256=owner.sha(owner.config_text(c['parameters']).encode()),frame_done=frame,unsupported_suite_calls=close['unsupported_suite_calls'],session_clean=close['session_clean'],results={})
                for route,name in ((0,'classic'),(1,'smart')):
                    err,raw=owner.mac_render(exe,temp,c,route)
                    c['results'][name]={'error':err,'sha256':owner.sha(raw) if not err else None,'exact':not err and raw==native,'different_bytes':sum(a!=b for a,b in zip(raw,native)) if not err else None,'first_differences':[{'offset':i,'aex':a,'mac':b} for i,(a,b) in enumerate(zip(native,raw)) if a!=b][:12] if not err else []}
                cases.append(c)
            print('SIGNED_ZERO_TRANSFER',w,h,sum(c['results']['classic']['exact'] for c in cases),'/',len(cases),flush=True)
    r={'schema':'olmcolorkey.signed-zero-transfer/1','case_count':len(cases),'summary':{name:sum(c['results'][name]['exact'] for c in cases) for name in ('classic','smart')},'source_sha256':owner.sha(original.encode()),'candidate_source_sha256':owner.sha(body.encode()),'probe_sha256':owner.sha(Path(__file__).read_bytes()),'typed_probe_sha256':owner.sha(Path(owner.__file__).read_bytes()),'harness_sha256':owner.sha(owner.HARNESS.read_bytes()),'candidate_tool_sha256':owner.sha(Path(recovery.__file__).read_bytes()),'worker_sha256':owner.sha(args.worker.read_bytes()),'aex_sha256':owner.sha(owner.AEX.read_bytes()),'cases':cases,'claims_not_made':['No native Windows AE/UCRT/Mac AE/installed completion','No all color-space/threshold/geometry/settings/ROI completion','Signed zero is preserved in the initial matte, not corrected after writing']}
    head=dict(r);del head['cases'];text=json.dumps(head,sort_keys=True,indent=2)[:-2]+',\n  "cases": [\n'+',\n'.join('    '+json.dumps(c,sort_keys=True) for c in cases)+'\n  ]\n}\n';args.report.write_text(text);assert json.loads(text)==r;print(r['summary'],flush=True)
if __name__=='__main__':main()
