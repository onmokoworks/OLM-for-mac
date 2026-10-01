#!/usr/bin/env python3
"""Keep failed reference execution separate from measurable color-space differences."""
import argparse,json,struct,subprocess,tempfile
from pathlib import Path
import probe_olmcolorkey_typed_controls_20261001 as owner

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--worker',type=Path,required=True);ap.add_argument('--report',type=Path,required=True);args=ap.parse_args();source=owner.SOURCE.read_text();cases=[]
    with tempfile.TemporaryDirectory(prefix='olmck_spaces_diagnostics_') as td:
        temp=Path(td);exe=owner.compile_public(temp/'mac',source)
        for c in owner.specifications('spaces',9,7):
            raw,_=owner.fixture(c['fixture'],c['depth']);c['input_sha256']=owner.sha(raw)
            try:
                native,frame,payload,close=owner.native_render(args.worker,temp,c)
            except subprocess.CalledProcessError as error:
                diagnostic=error.stderr.decode();diagnostic=diagnostic.replace(str(args.worker),'<worker>').replace(str(owner.AEX),'<AEX>').replace(str(temp),'<temporary>')
                messages=[];pos=0
                while pos<len(error.stdout):
                    n=struct.unpack_from('<I',error.stdout,pos)[0];pos+=4;m=json.loads(error.stdout[pos:pos+n]);pos+=n
                    if m['type']=='frame_done':messages.append(m)
                c.update(reference_status='failed',reference_exit_code=error.returncode,reference_stderr=diagnostic,frame_messages=messages,results={})
            else:
                c.update(reference_status='measured',actual_sha256=owner.sha(native),raw_pixel_bytes=len(native),parameter_payload=payload,frame_done=frame,session_clean=close['session_clean'],unsupported_suite_calls=close['unsupported_suite_calls'],results={})
                for route,name in ((0,'classic'),(1,'smart')):
                    err,mac=owner.mac_render(exe,temp,c,route)
                    c['results'][name]={'error':err,'sha256':owner.sha(mac) if not err else None,'exact':not err and mac==native,'different_bytes':sum(a!=b for a,b in zip(native,mac)) if not err else None,'first_differences':[{'offset':i,'aex':a,'mac':b} for i,(a,b) in enumerate(zip(native,mac)) if a!=b][:12] if not err else []}
            cases.append(c)
            if len(cases)%72==0:print('COLOR_SPACE_DIAGNOSTICS',len(cases),flush=True)
    measured=[c for c in cases if c['reference_status']=='measured'];r={'schema':'olmcolorkey.spaces-diagnostics/1','case_count':len(cases),'measured_count':len(measured),'reference_failure_count':len(cases)-len(measured),'summary':{name:sum(c['results'][name]['exact'] for c in measured) for name in ('classic','smart')},'source_sha256':owner.sha(source.encode()),'probe_sha256':owner.sha(Path(__file__).read_bytes()),'typed_probe_sha256':owner.sha(Path(owner.__file__).read_bytes()),'harness_sha256':owner.sha(owner.HARNESS.read_bytes()),'worker_sha256':owner.sha(args.worker.read_bytes()),'aex_sha256':owner.sha(owner.AEX.read_bytes()),'cases':cases,'claims_not_made':['Reference import failures are not Mac output mismatches','No tolerance or output compensation','No native Windows UCRT/AE/installed completion']}
    head=dict(r);del head['cases'];text=json.dumps(head,sort_keys=True,indent=2)[:-2]+',\n  "cases": [\n'+',\n'.join('    '+json.dumps(c,sort_keys=True) for c in cases)+'\n  ]\n}\n';args.report.write_text(text);assert json.loads(text)==r;print(r['measured_count'],r['reference_failure_count'],r['summary'],flush=True)
if __name__=='__main__':main()
