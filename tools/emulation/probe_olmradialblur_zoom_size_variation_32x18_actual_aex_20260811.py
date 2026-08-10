#!/usr/bin/env python3
"""Read-only actual-AEX probe: Zoom Size Variation, typed 32x18."""
from __future__ import annotations
import hashlib, json, pickle, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[1]; sys.path.insert(0,str(HERE))
import test_olmradialblur_offcenter_brightness_actual_aex_20260811 as base

VALUES=(0.,1.,25.,100.)
CELLS=[(d,s) for d in (8,16,32) for s in VALUES]
REPORT=ROOT/"refs/conformance/olmradialblur_zoom_size_variation_32x18_probe_20260811.json"

def configure(depth,size):
    target,frame,rb,cx,cy=base.configure(("zoom",depth,32,18,0.,0.,1.))
    m=target.fixture.m4
    old=m.install_reader_detours
    def install(loader,params):
        params=dict(params); params["Size Variation"]=size
        return old(loader,params)
    m.install_reader_detours=install
    return target

def capture(cell):
    return configure(*cell).actual_aex()

def isolated(cell):
    with tempfile.TemporaryDirectory(prefix="radial_zoom_size_") as raw:
        out=Path(raw)/"a.pkl"
        subprocess.run([sys.executable,__file__,"--capture",str(cell[0]),str(cell[1]),str(out)],check=True)
        return pickle.loads(out.read_bytes())

def sha(x): return hashlib.sha256(x).hexdigest()

def production(depth,size,expected):
    cell=("zoom",depth,32,18,0.,0.,1.)
    original_write=Path.write_text
    def write_text(path,data,*args,**kwargs):
        if path.name=="p.cpp":
            needle="i.noise_type=1;i.seed=1;i.thickness=10;"
            if needle not in data: raise RuntimeError("info marker absent")
            data=data.replace(needle,f"i.size_variation={size};"+needle,1)
        return original_write(path,data,*args,**kwargs)
    Path.write_text=write_text
    try: return base.production(cell,expected)
    finally: Path.write_text=original_write

def main():
    with ThreadPoolExecutor(max_workers=6) as pool:
        actual=dict(zip(CELLS,pool.map(isolated,CELLS)))
    rows=[]
    for depth in (8,16,32):
        zero=actual[(depth,0.)]
        for size in (1.,25.,100.):
            got=actual[(depth,size)]
            matches={p:got[p]==zero[p] for p in ("pre_blur","post_blur","output")}
            prod=production(depth,size,got)
            production_matches={p:prod[p]==got[p] for p in ("pre_blur","post_blur","output")}
            rows.append({"depth":depth,"size_variation":size,"equals_size0":matches,
                         "production_matches_actual":production_matches,
                         "hashes":{p:sha(got[p]) for p in ("pre_blur","post_blur","output")}})
            print(depth,size,matches,production_matches,flush=True)
    assert all(all(row["equals_size0"].values()) and
               all(row["production_matches_actual"].values()) for row in rows), rows
    REPORT.write_text(json.dumps({"kind":"olmradialblur_zoom_size_variation_32x18_probe_20260811",
      "scope":"Actual AEX Zoom 32x18 centered Outer4 Inner0 neutral tuple; PF8/PF16/PF32; Size Variation 1/25/100 compared with Size0 control.",
      "status":"9/9 actual-AEX internal planes and padded output byte exact",
      "aex_sha256":configure(32,0.).fixture.AEX_SHA256,"cases":rows},indent=2,sort_keys=True)+"\n")

if __name__=="__main__":
    if len(sys.argv)==5 and sys.argv[1]=="--capture":
        Path(sys.argv[4]).write_bytes(pickle.dumps(capture((int(sys.argv[2]),float(sys.argv[3]))))); raise SystemExit
    main()
