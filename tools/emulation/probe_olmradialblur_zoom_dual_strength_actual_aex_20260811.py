#!/usr/bin/env python3
"""Read-only 32x18 Zoom Outer4 + Inner2/4 actual-AEX comparison."""
import hashlib, inspect, json, pickle, subprocess, sys, tempfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import test_olmradialblur_offcenter_brightness_actual_aex_20260811 as base

CELLS=[("zoom",d,32,18,0.,0.,1.,s) for d in (8,16,32) for s in (2,4)]
REPORT=base.ROOT/"refs/conformance/olmradialblur_zoom_dual_strength_32x18_actual_aex_20260811.json"

def set_strength(target,strength):
    target.OUTER_STRENGTH=4
    target.INNER_STRENGTH=strength

def capture(cell):
    target,*_=base.configure(cell[:-1]);set_strength(target,cell[-1]);return target.actual_aex()

def patched_source(path):
    path.write_text((base.ROOT/"mac/OLMRadialBlur/OLMRadialBlur.cpp").read_text())

src=inspect.getsource(base.production)
src=src.replace("def production(cell, expected):", "def production_dual(cell, expected):")
src=src.replace("mode,depth,w,h,ox,oy,gain=cell;", "strength=cell[-1];cell=cell[:-1];mode,depth,w,h,ox,oy,gain=cell;")
src=src.replace("i.outer_strength=4;i.outer_offset_mode=1;i.inner_offset_mode=1;", "i.outer_strength=4;i.inner_strength={strength};i.outer_offset_mode=1;i.inner_offset_mode=1;")
ns=dict(base.__dict__);ns["patched_source"]=patched_source;exec(src,ns);production_dual=ns["production_dual"]

def isolated(cell):
    with tempfile.TemporaryDirectory(prefix="radial_dual_zoom_") as raw:
        p=Path(raw)/"capture.pkl"
        subprocess.run([sys.executable,__file__,"--capture",*map(str,cell),str(p)],check=True)
        return pickle.loads(p.read_bytes())

def first_diff(a,b):
    return next((i for i,(x,y) in enumerate(zip(a,b)) if x!=y),None)

def main():
    rows=[]
    for cell in CELLS:
        actual=isolated(cell);prod=production_dual(cell,actual)
        matches={p:prod[p]==actual[p] for p in ("pre_blur","post_blur","output")}
        diffs={p:{"first":first_diff(prod[p],actual[p]),"count":sum(x!=y for x,y in zip(prod[p],actual[p]))} for p in matches if not matches[p]}
        row={"depth":cell[1],"outer_strength":4,"inner_strength":cell[-1],"matches":matches,"diffs":diffs,
             "actual_sha256":{p:hashlib.sha256(actual[p]).hexdigest() for p in matches}}
        rows.append(row);print(row,flush=True)
    assert all(all(row["matches"].values()) for row in rows),rows
    REPORT.write_text(json.dumps({"kind":"olmradialblur_zoom_dual_strength_32x18_actual_aex_20260811",
        "scope":"centered 32x18 Zoom, PF8/PF16/PF32, Outer4 + Inner2/4, neutral remaining controls",
        "status":"6/6 internal planes and padded output byte exact","cases":rows},indent=2,sort_keys=True)+"\n")

if __name__=="__main__":
    if len(sys.argv)>2 and sys.argv[1]=="--capture":
        v=sys.argv[2:-1];cell=(v[0],int(v[1]),int(v[2]),int(v[3]),float(v[4]),float(v[5]),float(v[6]),int(v[7]));Path(sys.argv[-1]).write_bytes(pickle.dumps(capture(cell)));raise SystemExit
    raise SystemExit(main())
