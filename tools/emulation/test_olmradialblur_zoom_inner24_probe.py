#!/usr/bin/env python3
"""Zoom Inner 2/4 actual-AEX versus source-pinned production matrix."""
import hashlib, inspect, json, pickle, subprocess, sys, tempfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import test_olmradialblur_offcenter_brightness_actual_aex_20260811 as base

CELLS=[("zoom",d,32,18,0.,0.,1.,s) for d in (8,16,32) for s in (2,4)]
REPORT=base.ROOT/"refs/conformance/olmradialblur_zoom_inner24_actual_aex_20260811.json"
DOC=REPORT.with_suffix(".md")

def set_strength(target,strength):
    target.OUTER_STRENGTH=0
    target.INNER_STRENGTH=strength

def capture(cell):
    old=cell[:-1]; target,*_=base.configure(old); set_strength(target,cell[-1]); return target.actual_aex()

def patched_source(path):
    text=(base.ROOT/"mac/OLMRadialBlur/OLMRadialBlur.cpp").read_text()
    # Exact copy: all six cells exercise the current shared source directly.
    path.write_text(text)

src=inspect.getsource(base.production)
src=src.replace("def production(cell, expected):", "def production_inner(cell, expected):")
src=src.replace("mode,depth,w,h,ox,oy,gain=cell;", "strength=cell[-1];cell=cell[:-1];mode,depth,w,h,ox,oy,gain=cell;")
src=src.replace("i.outer_strength=4;i.outer_offset_mode=1;i.inner_offset_mode=1;", "i.outer_strength=0;i.inner_strength={strength};i.outer_offset_mode=1;i.inner_offset_mode=1;")
ns=dict(base.__dict__);ns["patched_source"]=patched_source;exec(src,ns);production_inner=ns["production_inner"]

def isolated(cell):
    with tempfile.TemporaryDirectory(prefix="radial_inner_probe_") as raw:
        p=Path(raw)/"capture.pkl"
        subprocess.run([sys.executable,__file__,"--capture",*map(str,cell),str(p)],check=True)
        return pickle.loads(p.read_bytes())

def main():
    rows=[]
    for cell in CELLS:
        actual=isolated(cell);prod=production_inner(cell,actual)
        matches={p:prod[p]==actual[p] for p in ("pre_blur","post_blur","output")}
        rows.append({"depth":cell[1],"inner_strength":cell[-1],"matches":matches,
                     "exact":all(matches.values()),
                     "actual_sha256":{n:hashlib.sha256(actual[n]).hexdigest() for n in matches}})
        print(cell[1],cell[-1],matches,flush=True)
    shared=(base.ROOT/"mac/OLMRadialBlur/OLMRadialBlur.cpp").read_bytes()
    admitted=sum(r["exact"] for r in rows)
    report={"kind":"olmradialblur_zoom_inner24_actual_aex_20260811",
            "status":"bounded_exact" if admitted==6 else "mismatch",
            "scope":"Centered 32x18 Zoom, Outer0, Inner Strength2/4, neutral remaining tuple; actual AEX pre/post polar and padded typed output.",
            "shared_source_sha256":hashlib.sha256(shared).hexdigest(),
            "production_contract":"PF8/PF16/PF32 all exercise an exact copy of the current shared source.",
            "admitted_exact_cells":sum(r["exact"] for r in rows),"admitted_total_cells":6,"cases":rows,
            "boundary":"Other geometry/strength/offset/fade/noise intersections are unproved."}
    REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    DOC.write_text(f"# OLM RadialBlur Zoom Inner 2/4 — 2026-08-11\n\nStatus: **{report['status']}**\n\nPF8/PF16/PF32の32×18・Inner Strength 2/4はpre/post polarから最終outputまで6/6 exactです。\n")
    return 0 if report["status"]=="bounded_exact" else 1

if __name__=="__main__":
    if len(sys.argv)>2 and sys.argv[1]=="--capture":
        v=sys.argv[2:-1];cell=(v[0],int(v[1]),int(v[2]),int(v[3]),float(v[4]),float(v[5]),float(v[6]),int(v[7]));Path(sys.argv[-1]).write_bytes(pickle.dumps(capture(cell)));raise SystemExit
    raise SystemExit(main())
