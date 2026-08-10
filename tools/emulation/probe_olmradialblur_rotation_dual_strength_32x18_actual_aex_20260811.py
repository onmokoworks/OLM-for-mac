#!/usr/bin/env python3
"""Read-only probe: Rotation Outer4 + Inner2/4 at centered 32x18."""
from __future__ import annotations
import json, pickle, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[1]; sys.path.insert(0,str(HERE))
import test_olmradialblur_offcenter_brightness_actual_aex_20260811 as base

CELLS=[(d,s) for d in (8,16,32) for s in (2,4)]
REPORT=ROOT/"refs/conformance/olmradialblur_rotation_dual_strength_32x18_probe_20260811.json"

def configure(cell):
    depth,inner=cell
    synthetic=("rotation",depth,32,18,0.0,0.0,1.0)
    target,*_=base.configure(synthetic)
    fixture=target.base if depth==32 else target
    fixture.FIXTURE_OUTER_STRENGTH=4
    fixture.FIXTURE_INNER_STRENGTH=inner
    fixture.FIXTURE_OUTER_EDGE_FADE=0
    fixture.FIXTURE_INNER_EDGE_FADE=0
    fixture.CAPTURE_EDGE_INTERNALS=True
    if depth==32:
        target.OUTER_STRENGTH=4
        target.INNER_STRENGTH=inner
    return synthetic,target

def capture(cell): return configure(cell)[1].actual_aex()

def isolated(cell):
    with tempfile.TemporaryDirectory(prefix="rotation_dual_") as raw:
        out=Path(raw)/"a.pkl"
        subprocess.run([sys.executable,__file__,"--capture",*map(str,cell),str(out)],check=True)
        return pickle.loads(out.read_bytes())

def production(cell,expected):
    synthetic,_=configure(cell); _,inner=cell
    old=Path.write_text
    def write_text(path,data,*args,**kwargs):
        if path.name=="p.cpp":
            marker="i.outer_strength=4;i.outer_offset_mode=1;"
            replacement=("i.outer_strength=4;i.outer_offset_mode=1;"
                         f"i.inner_strength={inner};i.inner_offset_mode=1;")
            if marker not in data: raise RuntimeError("probe marker missing")
            data=data.replace(marker,replacement,1)
        return old(path,data,*args,**kwargs)
    Path.write_text=write_text
    try:return base.production(synthetic,expected)
    finally:Path.write_text=old

def firstdiff(a,b):
    for i,(x,y) in enumerate(zip(a,b)):
        if x!=y:return {"offset":i,"actual":x,"production":y}
    return None if len(a)==len(b) else {"offset":min(len(a),len(b)),"actual_len":len(a),"production_len":len(b)}

def main():
    with ThreadPoolExecutor(max_workers=6) as pool: actuals=dict(zip(CELLS,pool.map(isolated,CELLS)))
    rows=[]
    for cell in CELLS:
        a=actuals[cell]; p=production(cell,a)
        names=("polar","source_scalar","prepass_alpha","accum","max_alpha","final_rgba","coordinates","output")
        matches={n:(n in a and n in p and a[n]==p[n]) for n in names}
        rows.append({"depth":cell[0],"outer_strength":4,"inner_strength":cell[1],
                     "matches":matches,"first_diffs":{n:firstdiff(a[n],p[n]) for n in names if n in a and n in p and a[n]!=p[n]},
                     "actual_sizes":{n:len(a[n]) for n in names if n in a},
                     "production_sizes":{n:len(p[n]) for n in names if n in p}})
        print(cell,matches,rows[-1]["first_diffs"],flush=True)
    assert all(all(row["matches"].values()) for row in rows),rows
    REPORT.write_text(json.dumps({"kind":"olmradialblur_rotation_dual_strength_32x18_actual_aex_20260811","scope":"centered 32x18 Rotation, Outer4 + Inner2/4, neutral remaining controls","status":"6/6 internal planes and padded output byte exact","cases":rows},indent=2,sort_keys=True)+"\n")

if __name__=="__main__":
    if len(sys.argv)>2 and sys.argv[1]=="--capture":
        cell=(int(sys.argv[2]),int(sys.argv[3]));Path(sys.argv[4]).write_bytes(pickle.dumps(capture(cell)));raise SystemExit
    main()
