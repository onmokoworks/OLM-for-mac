"""Fixture-v2 primary/secondary padding, origin and extent probes (no downsample)."""
import argparse
import copy
import json
from pathlib import Path
import sys
from PIL import Image

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'tools/oracle'))
import olm_oracle as o

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',required=True,type=Path);p.add_argument('--out',required=True,type=Path)
    a=p.parse_args();a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=False)
    original=Path(json.loads((HERE/'scaffold.json').read_text())['original']['path'])
    params=json.loads((HERE/'inventory.json').read_text())['parameters']
    results=[]
    for depth in [8,16,32]:
        for variant in ['padding','texture-origin','texture-extent','primary-origin','primary-extent']:
            case=a.out/f'{variant}-{depth}';case.mkdir()
            Image.fromarray(o.input_pixels(11,7,20261115)).save(case/'input.png')
            Image.fromarray(o.input_pixels(9,5,20261116)).save(case/'texture.png')
            pars=copy.deepcopy(params)
            for par in pars:
                if par['slot']==1:par['layer_path']='texture.png'
            fmt={8:'argb8',16:'argb16',32:'argb32f'}[depth];bpp=depth//2
            def layout(w,h):return dict(pixel_format=fmt,width=w,height=h,rowbytes=(w+2)*bpp,row_padding=2*bpp,padding_byte=165,origin={'x':0,'y':0},extent=dict(left=0,top=0,right=w,bottom=h))
            primary=layout(11,7);secondary=layout(9,5);secondary['slot']=1
            if variant=='texture-origin':secondary['origin']={'x':-2,'y':1}
            if variant=='texture-extent':secondary['extent']=dict(left=1,top=1,right=8,bottom=4)
            if variant=='primary-origin':primary['origin']={'x':2,'y':-1}
            if variant=='primary-extent':primary['extent']=dict(left=1,top=1,right=10,bottom=6)
            fixture=dict(schema='aexcompat.render_fixture',schema_version=2,primary_layer='input.png',parameters=pars,pixel_format=fmt,render_path='smart',premultiplication='straight',timing=dict(current_time=0,time_step=1,total_time=1,time_scale=1),final_artifact='raw',worlds=dict(primary=primary,secondary=[secondary]),checkpoints=[dict(id='input',stage='smart-input'),dict(id='texture',stage='smart-layer-slot1'),dict(id='output',stage='smart-output')])
            o.write_json(case/'fixture.json',fixture)
            processes={}
            for side,module in [('reference',original),('candidate',a.candidate.resolve())]:
                processes[side]=o.run_process([o.DEFAULT_HARNESS,'--headless','--render-fixture',module,case/'fixture.json',case/side],60)
                o.write_json(case/f'{side}.process.json',processes[side])
            success=all(p['returncode']==0 and not p['timeout'] for p in processes.values())
            matches={}
            if success:
                for checkpoint in ['input','texture','output']:
                    paths=[case/side/'checkpoints'/checkpoint/'output.bin' for side in ['reference','candidate']]
                    matches[checkpoint]=paths[0].read_bytes()==paths[1].read_bytes()
            row=dict(depth=depth,variant=variant,rendered=success,matches=matches)
            results.append(row);print(row,flush=True)
    o.write_json(a.out/'summary.json',results)
    return 0 if all(r['rendered'] and all(r['matches'].values()) for r in results) else 1
if __name__=='__main__':raise SystemExit(main())
