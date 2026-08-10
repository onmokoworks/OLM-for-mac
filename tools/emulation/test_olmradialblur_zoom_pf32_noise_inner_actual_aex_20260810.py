#!/usr/bin/env python3
"""PF32 Zoom: close Type-1 Noise and retain Inner Strength as an evidence boundary."""
from __future__ import annotations
import hashlib,json,pickle,subprocess,sys,tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];HERE=ROOT/"tools/emulation";sys.path.insert(0,str(HERE))
import test_olmradialblur_zoom_pf32_small_actual_aex_20260805 as wrapper  # noqa:E402
pf8=wrapper.fixture;zoom=pf8.zoom
REPORT=ROOT/"refs/conformance/olmradialblur_zoom_pf32_noise_inner_actual_aex_20260810.json";DOC=REPORT.with_suffix(".md")
def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def configure(inner:float,noise:float):
 pf8.W,pf8.H,pf8.ROWBYTES,pf8.VISIBLE=9,7,160,144;pf8.PIXEL_CPP="PF_PixelFloat";pf8.PIXEL_BYTES=16;pf8.BITDEPTH=32;pf8.ZOOM_RETURN=0x180008322;pf8.USE_RENDER_WORLD_FINAL=True;pf8.source_frame=wrapper.source_frame;pf8.configure()
 zoom.INNER_STRENGTH=inner;zoom.NOISE_VARIATION=noise;zoom.PIXEL_CPP="PF_PixelFloat";zoom.PIXEL_BYTES=16;zoom.USE_RENDER_WORLD_FINAL=True;zoom.RENDER_WORLD_BITDEPTH=32;zoom.ZOOM_RETURN=0x180008322
 zoom.fixture.W,zoom.fixture.H,zoom.fixture.ROWBYTES,zoom.fixture.VISIBLE=9,7,160,144;zoom.fixture.source_frame=wrapper.source_frame;zoom.fixture.build_world=pf8.build_world
def actual(inner:float,noise:float):configure(inner,noise);return zoom.actual_aex()
def production(inner:float,noise:float,expected):configure(inner,noise);return zoom.mac_production(expected)
def isolated(mode:str,inner:float,noise:float,expected=None):
 with tempfile.TemporaryDirectory(prefix="radial_zoom_branch_") as d:
  out=Path(d)/"out.pkl";cmd=[sys.executable,str(Path(__file__)),f"--{mode}",str(inner),str(noise)]
  if expected is not None:inp=Path(d)/"in.pkl";inp.write_bytes(pickle.dumps(expected));cmd.append(str(inp))
  cmd.append(str(out));p=subprocess.run(cmd);return (p.returncode,pickle.loads(out.read_bytes()) if out.exists() else None)
def main():
 cases=[(0.,0.),(0.,25.),(0.,100.),(50.,0.),(100.,0.)]
 with ThreadPoolExecutor(max_workers=5) as pool:captured=dict(zip(cases,pool.map(lambda p:isolated("actual",*p)[1],cases)))
 noise_rows=[];exact=True
 for nv in (25.,100.):
  rc,prod=isolated("production",0.,nv,captured[(0.,nv)]);matches={k:prod[k]==captured[(0.,nv)][k] for k in ("pre_blur","post_blur","output")} if prod else {}
  ok=rc==0 and all(matches.values());exact&=ok;noise_rows.append({"noise_variation":nv,"matches":matches,"output_differs_noise0":captured[(0.,nv)]["output"]!=captured[(0.,0.)]["output"],"hashes":{k:sha(captured[(0.,nv)][k]) for k in ("pre_blur","post_blur","output")},"exact":ok})
 inner=[]
 for strength in (50.,100.):
  rc,_=isolated("production",strength,0.,captured[(strength,0.)]);inner.append({"inner_strength":strength,"actual_output_differs_inner0":captured[(strength,0.)]["output"]!=captured[(0.,0.)]["output"],"actual_hashes":{k:sha(captured[(strength,0.)][k]) for k in ("pre_blur","post_blur","output")},"production_fail_closed":rc!=0})
 status="noise_exact_inner_captured_fail_closed" if exact and all(x["production_fail_closed"] for x in inner) else "mismatch"
 report={"kind":"olmradialblur_zoom_pf32_noise_inner_actual_aex_20260810","status":status,"scope":"PF32 Zoom 9x7 padded; outer Strength4; Noise Type1 NV25/100 and separate Inner Strength50/100 captures.","aex_sha256":zoom.fixture.AEX_SHA256,"noise_family":noise_rows,"inner_boundary":inner,"boundary":"Noise exact only for 9x7 PF32 neutral outer tuple. Inner Strength is captured but remains fail-closed pending a production two-sided producer. No 32x18/general geometry claim."}
 REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n");DOC.write_text(f"# OLM RadialBlur PF32 Zoom Noise and Inner boundary — 2026-08-10\n\nStatus: **{status}**\n\nType-1 Noise 25/100 is compared from actual-AEX pre/post polar planes through padded production output. Inner Strength 50/100 actual-AEX planes are pinned separately and remain fail-closed; they require a two-sided producer rather than an outer-only admission.\n");print(json.dumps({"status":status},sort_keys=True));return 0 if status.startswith("noise_exact") else 1
if __name__=="__main__":
 if len(sys.argv)==5 and sys.argv[1]=="--actual":Path(sys.argv[4]).write_bytes(pickle.dumps(actual(float(sys.argv[2]),float(sys.argv[3]))));raise SystemExit(0)
 if len(sys.argv)==6 and sys.argv[1]=="--production":
  try:r=production(float(sys.argv[2]),float(sys.argv[3]),pickle.loads(Path(sys.argv[4]).read_bytes()))
  except subprocess.CalledProcessError as e:raise SystemExit(e.returncode)
  Path(sys.argv[5]).write_bytes(pickle.dumps(r));raise SystemExit(0)
 raise SystemExit(main())
