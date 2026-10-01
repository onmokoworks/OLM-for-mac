#!/usr/bin/env python3
"""Transfer the restored Lab classifier into independent Thin/Blur geometries."""
import argparse,json,tempfile
from pathlib import Path
import probe_olmcolorkey_typed_controls_20261001 as owner
import probe_olmcolorkey_lab_state_boundary_20261001 as independent

def specifications():
    for space,component in ((3,False),(3,True),(4,True)):
        for depth in ('PF8','PF16','PF32'):
            for gi,(w,h) in enumerate(((1,1),(1,9),(9,1),(17,11))):
                for pi,palette in enumerate(('reverse','disabled_first','last25','duplicate')):
                    params=independent.controls(space,component,1+(gi+pi)%3,palette,pi%2==0,gi%2==1,0.17,premultiplied=pi%3==0)
                    edges=((0,2,1.5,1,3),(-1,1,2,2,2),(1,3,0.5,3,1),(2,2,7.3,1,3))[pi]
                    thin,thin_type,blur,direction,blur_type=edges
                    for v in params:
                        slot=v['slot']
                        if slot in (14,15,18,19,20):v['value']={14:thin,15:thin_type,18:blur,19:blur_type,20:direction}[slot]
                        elif slot in (9,10,11):v['value']={9:0.01,10:0.17,11:0.4}[slot]
                        elif slot>=24 and (slot-24)%8 in (5,6,7):v['value']={5:0.03,6:0.21,7:0.37}[(slot-24)%8]
                    yield {'fixture':{'id':f'lab_edge_{w}x{h}','width':w,'height':h},'depth':depth,'label':f'lab{space}_component{component}_{palette}_{w}x{h}','parameters':params}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--worker',type=Path,required=True);ap.add_argument('--report',type=Path,required=True);args=ap.parse_args();source=owner.SOURCE.read_text();owner.fixture=independent.fixture;cases=[]
    with tempfile.TemporaryDirectory(prefix='olmck_lab_edge_transfer_') as td:
        temp=Path(td);exe=owner.compile_public(temp/'production',source)
        for c in specifications():
            cases.append(independent.capture(args.worker,temp,c,{'production':exe}))
            if len(cases)%36==0:print('LAB_EDGE_TRANSFER',len(cases),sum(c['results']['production']['classic']['exact'] for c in cases),flush=True)
    summary={route:sum(c['results']['production'][route]['exact'] for c in cases) for route in ('classic','smart')}
    report={'schema':'olmcolorkey.lab-edge-transfer/1','case_count':len(cases),'summary':summary,'source_sha256':owner.sha(source.encode()),'aex_sha256':owner.sha(owner.AEX.read_bytes()),'worker_sha256':owner.sha(args.worker.read_bytes()),'dependencies_sha256':{str(p.relative_to(owner.ROOT)):owner.sha(p.read_bytes()) for p in (Path(__file__),Path(independent.__file__),Path(owner.__file__),owner.HARNESS)},'cases':cases,'claims_not_made':['No all-settings/geometry/threshold/HDR/ROI/downsample completion','No native Windows UCRT/AE/Mac installed proof','Lab94 scalar is not measured','Parameters are slot/type bound; per-frame parameter readback unavailable']}
    head=dict(report);del head['cases'];text=json.dumps(head,sort_keys=True,indent=2)[:-2]+',\n  "cases": [\n'+',\n'.join('    '+json.dumps(c,sort_keys=True) for c in cases)+'\n  ]\n}\n';args.report.write_text(text);assert json.loads(text)==report;print('RESULT',summary,flush=True)
if __name__=='__main__':main()
