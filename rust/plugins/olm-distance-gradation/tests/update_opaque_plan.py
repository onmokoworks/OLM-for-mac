"""Explicit fully opaque edge and new 512/1000 slider boundary corpus."""
import itertools
import json
from pathlib import Path
crate=Path(__file__).resolve().parents[1]
cases=[]
def add(inout,padding,downsample,render,threshold=7):
    values={1:0,2:inout,3:threshold,4:threshold,5:render,6:0,9:2,10:1.,11:1,12:0,13:padding}
    cases.append(dict(index=len(cases),size=[11,7],input_seed=2026111300+len(cases),
        downsample=downsample,assignments=[dict(slot=k,value=v) for k,v in values.items()],
        unassigned=[],untouched_defaults=[],input_pattern='fully opaque RGBA; deterministic colored interior',
        purpose='opaque-edge padding and threshold boundary'))
for i,p,d,r in itertools.product([1,2,3],[0,1],['1','1/2','1/4'],[1,2]): add(i,p,d,r)
for i,t in itertools.product([1,2,3],[512,1000]): add(i,1,'1/4',1,t)
path=crate/'validation/upstream/opaque-plan.json'
path.write_text(json.dumps(cases,indent=2))
print(len(cases),'cases:',path)
