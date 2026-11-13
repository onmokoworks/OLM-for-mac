"""Supplemental plateau, alpha and opaque-edge cases through the labelled diagnostic bridge."""
import argparse,json,sys,os
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'tools/oracle'))
import olm_oracle as o
import numpy as np
from PIL import Image

def run(reference,candidate,original,out):
    out.mkdir(parents=True,exist_ok=False)
    identities={'reference':o.identity(reference),'candidate':o.identity(candidate),'harness':o.identity(o.DEFAULT_HARNESS),'original_loaded_by_bridge':o.identity(original)}
    os.environ['OLM_REFERENCE_ORIGINAL']=str(original);os.environ['OLM_REFERENCE_REDUNDANT_CHECKIN']='1'
    rows=[]
    colors=[[1,1,0,0],[1,0,1,0],[1,0,0,1],[1,0,0,0],[1,1,1,1]]
    for k in range(12):
        w,h=17,11;arr=np.zeros((h,w,4),dtype=np.uint8)
        for y in range(h):
            for x in range(w):
                c=colors[(x//4+y//5)%5];arr[y,x]=[int(c[1]*255),int(c[2]*255),int(c[3]*255),255]
                if k%4==1 and x%4==3:arr[y,x,:3]=[128,128,32]
                if k%4==2:arr[y,x,3]=[0,1,127,128,254,255][(x+y)%6]
                if k%4==3:arr[y,x,:3]=[int(x*255/(w-1)),17 if x<w//2 else 239,(x*71+y*37)%256]
        palette=[] if k<4 else colors if k<8 else [colors[0],colors[0],colors[3],colors[4]]
        assignments=[{'slot':1,'value':len(palette)},{'slot':2,'value':int(k<8)}]+[{'slot':j+7,'color':[int(v*255) for v in c]} for j,c in enumerate(palette)]
        case={'index':k,'size':[w,h],'input_seed':k,'assignments':assignments,'downsample':['1','1/2','1/4'][k%3]}
        for route in ['smart8','smart16','smart32']:
            directory,manifest=o.prepare_case(out,case,route,identities)
            Image.fromarray(arr).save(directory/'input.png');manifest['assets']['input.png']=o.sha256(directory/'input.png');o.write_json(directory/'case.json',manifest)
            rows.append(o.evaluate_case(directory,manifest,60))
        print(k,[r['status'] for r in rows[-3:]],flush=True)
    summary={'diagnostic_bridge_only':True,**identities,'results':rows,'routes':o.summarize(rows,{r:None for r in ['smart8','smart16','smart32']})}
    o.write_json(out/'summary.json',summary);return int(any(r['status']!='exact' for r in rows))
if __name__=='__main__':
    p=argparse.ArgumentParser();[p.add_argument('--'+k,type=Path,required=True) for k in ['reference','candidate','original','out']];x=p.parse_args();raise SystemExit(run(*[getattr(x,k).resolve() for k in ['reference','candidate','original','out']]))
