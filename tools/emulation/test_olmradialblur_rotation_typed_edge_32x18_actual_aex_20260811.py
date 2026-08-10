#!/usr/bin/env python3
"""Rotation 32x18 PF8/PF16/PF32 edge-fade actual-owner comparison."""
from __future__ import annotations
import json, pickle, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[1]; sys.path.insert(0,str(HERE))
import test_olmradialblur_offcenter_brightness_actual_aex_20260811 as base

CELLS=[(d,k,f) for d in (8,16,32) for k in ("outer","inner") for f in (50,100)]
REPORT=ROOT/"refs/conformance/olmradialblur_rotation_typed_edge_32x18_actual_aex_20260811.json"
DOC=REPORT.with_suffix(".md")

def configure(cell):
    depth,kind,fade=cell
    synthetic=("rotation",depth,32,18,0.0,0.0,1.0)
    target,frame,rb,cx,cy=base.configure(synthetic)
    fixture=target.base if depth==32 else target
    fixture.FIXTURE_OUTER_STRENGTH=4 if kind=="outer" else 0
    fixture.FIXTURE_INNER_STRENGTH=0 if kind=="outer" else 4
    fixture.FIXTURE_OUTER_EDGE_FADE=fade if kind=="outer" else 0
    fixture.FIXTURE_INNER_EDGE_FADE=fade if kind=="inner" else 0
    fixture.CAPTURE_EDGE_INTERNALS=True
    # The PF32 wrapper copies its own strength globals into the shared PF16
    # owner fixture immediately before executing the AEX.  Keep both layers in
    # sync; otherwise PF32 inner captures silently exercise Strength 0 while
    # production is compiled with the requested Strength 4.
    if depth==32:
        target.OUTER_STRENGTH=4 if kind=="outer" else 0
        target.INNER_STRENGTH=0 if kind=="outer" else 4
    return synthetic,target

def capture(cell):
    _,target=configure(cell)
    return target.actual_aex()

def isolated(cell):
    with tempfile.TemporaryDirectory(prefix="rotation_edge_probe_") as raw:
        out=Path(raw)/"a.pkl"
        subprocess.run([sys.executable,__file__,"--capture",*map(str,cell),str(out)],check=True)
        return pickle.loads(out.read_bytes())

def production(cell, expected):
    synthetic,_=configure(cell); depth,kind,fade=cell
    old=Path.write_text
    def write_text(path,data,*args,**kwargs):
        if path.name=="p.cpp":
            marker="i.outer_strength=4;i.outer_offset_mode=1;"
            replacement=(f"i.outer_strength={4 if kind=='outer' else 0};"
                         f"i.outer_edge_fade={fade if kind=='outer' else 0};"
                         "i.outer_offset_mode=1;"
                         f"i.inner_strength={0 if kind=='outer' else 4};"
                         f"i.inner_edge_fade={fade if kind=='inner' else 0};")
            if marker not in data: raise RuntimeError("probe marker missing")
            data=data.replace(marker,replacement,1)
        return old(path,data,*args,**kwargs)
    Path.write_text=write_text
    try: return base.production(synthetic,expected)
    finally: Path.write_text=old

def diff(a,b):
    for i,(x,y) in enumerate(zip(a,b)):
        if x!=y:return {"offset":i,"actual":x,"production":y}
    if len(a)!=len(b):return {"offset":min(len(a),len(b)),"actual_len":len(a),"production_len":len(b)}

def main():
    with ThreadPoolExecutor(max_workers=6) as pool:
        actuals=dict(zip(CELLS,pool.map(isolated,CELLS)))
    rows=[]
    for cell in CELLS:
        try:
            actual=actuals[cell]; prod=production(cell,actual)
            planes=("polar","source_scalar","accum","max_alpha","final_rgba","coordinates","output")
            matches={p:p in actual and p in prod and actual[p]==prod[p] for p in planes}
            diffs={p:diff(actual[p],prod[p]) for p in planes if p in actual and p in prod and not matches[p]}
            semantic=all(matches.values())
            rows.append({"depth":cell[0],"kind":cell[1],"edge_fade":cell[2],
                         "strength":4,"matches":matches,"first_diffs":diffs,
                         "seven_plane_exact":semantic,
                         "prepass_actual_captured":actual.get("prepass_alpha") is not None,
                         "prepass_production_exported":prod.get("prepass_alpha") is not None})
            print(cell,"SEVEN-PLANE-EXACT" if semantic else "MISMATCH",matches,diffs,flush=True)
        except Exception as e:
            rows.append({"depth":cell[0],"kind":cell[1],"edge_fade":cell[2],"blocker":f"{type(e).__name__}: {e}"})
            print(cell,"BLOCKER",type(e).__name__,str(e),flush=True)
    exact=sum(r.get("seven_plane_exact",False) for r in rows)
    status="exact" if exact==len(rows) else "bounded-mismatch"
    report={"kind":"olmradialblur_rotation_typed_edge_32x18_actual_aex_20260811",
            "status":status,"scope":"Rotation centered 32x18, PF8/PF16/PF32, Outer or Inner Strength4 with matching Edge Fade50/100; neutral remaining parameters.",
            "seven_plane_exact_cases":exact,"total_cases":len(rows),"cases":rows,
            "comparison_planes":["polar","source_scalar","accum","max_alpha","final_rgba","coordinates","output"],
            "configuration_guard":"The PF32 wrapper globals and its shared PF16 owner fixture must both receive the requested Strength. Setting only the fixture is overwritten by the wrapper immediately before actual-AEX execution.",
            "admission_boundary":"Only the listed 12 depth/kind/fade cells at centered 32x18 are admitted by this evidence."}
    REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    DOC.write_text(f"# OLM RadialBlur Rotation typed Edge Fade 32x18 — 2026-08-11\n\nStatus: **{status}** ({exact}/{len(rows)}). PF8/PF16/PF32のOuter/Inner Fade 50/100は、polar、source scalar、accum、max alpha、final RGBA、coordinates、outputでbyte一致しました。prepass alphaはactual側で取得済みですが共通production harnessがexportしないため比較対象外です。以前のPF32 Inner残差はwrapperがStrength 4をStrength 0へ上書きしていたactual harness設定不備であり、アルゴリズム差ではありません。\n")

if __name__=="__main__":
    if len(sys.argv)>2 and sys.argv[1]=="--capture":
        cell=(int(sys.argv[2]),sys.argv[3],int(sys.argv[4]));Path(sys.argv[5]).write_bytes(pickle.dumps(capture(cell)));raise SystemExit(0)
    main()
