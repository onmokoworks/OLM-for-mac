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
 cases=[(0.,0.),(0.,25.),(0.,100.),(50.,0.),(100.,0.),(50.,25.),(50.,100.),(100.,25.),(100.,100.)]
 with ThreadPoolExecutor(max_workers=5) as pool:captured=dict(zip(cases,pool.map(lambda p:isolated("actual",*p)[1],cases)))
 supported=[(0.,25.),(0.,100.),(50.,0.),(100.,0.),(50.,25.),(50.,100.),(100.,25.),(100.,100.)]
 with ThreadPoolExecutor(max_workers=6) as pool:produced=dict(zip(supported,pool.map(lambda p:isolated("production",p[0],p[1],captured[p]),supported)))
 noise_rows=[];exact=True
 for nv in (25.,100.):
  rc,prod=produced[(0.,nv)];matches={k:prod[k]==captured[(0.,nv)][k] for k in ("pre_blur","post_blur","output")} if prod else {}
  ok=rc==0 and all(matches.values());exact&=ok;noise_rows.append({"noise_variation":nv,"matches":matches,"output_differs_noise0":captured[(0.,nv)]["output"]!=captured[(0.,0.)]["output"],"hashes":{k:sha(captured[(0.,nv)][k]) for k in ("pre_blur","post_blur","output")},"exact":ok})
 inner=[]
 for strength in (50.,100.):
  rc,prod=produced[(strength,0.)];matches={k:prod[k]==captured[(strength,0.)][k] for k in ("pre_blur","post_blur","output")} if prod else {};inner_exact=rc==0 and all(matches.values());exact&=inner_exact;inner.append({"inner_strength":strength,"actual_output_differs_inner0":captured[(strength,0.)]["output"]!=captured[(0.,0.)]["output"],"actual_hashes":{k:sha(captured[(strength,0.)][k]) for k in ("pre_blur","post_blur","output")},"production_matches_actual":matches,"exact":inner_exact})
 combo=[]
 for strength in (50.,100.):
  for noise in (25.,100.):
   rc,prod=produced[(strength,noise)];matches={k:prod[k]==captured[(strength,noise)][k] for k in ("pre_blur","post_blur","output")} if prod else {};cell_exact=rc==0 and all(matches.values());exact&=cell_exact;combo.append({"inner_strength":strength,"noise_variation":noise,"production_matches_actual":matches,"actual_output_differs_inner_only":captured[(strength,noise)]["output"]!=captured[(strength,0.)]["output"],"actual_output_differs_noise_only":captured[(strength,noise)]["output"]!=captured[(0.,noise)]["output"],"exact":cell_exact})
 unsupported_rc,_=isolated("production",50.,50.,captured[(50.,25.)]);inner_noise_fail_closed=unsupported_rc!=0;exact&=inner_noise_fail_closed
 status="noise_and_inner_exact" if exact else "mismatch"
 report={"kind":"olmradialblur_zoom_pf32_noise_inner_actual_aex_20260810","status":status,"scope":"PF32 Zoom 9x7 padded; outer Strength4; Noise Type1 NV25/100, Inner Strength50/100, and their four-cell cross-product.","aex_sha256":zoom.fixture.AEX_SHA256,"noise_family":noise_rows,"inner_family":inner,"inner_noise_family":combo,"inner_noise_fail_closed":{"inner50_noise50":inner_noise_fail_closed},"inner_rule":"Noise materializes the source span before propagation. Outer propagation writes increasing radius; Inner propagation writes decreasing radius but stops before radius cell zero. Both directions use the same noisy span for limit and table index, accumulate RGB/alpha and max-alpha in source order, then normalize once.","boundary":"Inner×Noise exact only for the four 9x7 cells, Outer4 and neutral offsets/fades. NV50, other strength/offset/fade, other geometry/depth and AE-host behavior remain fail-closed."}
 REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n");DOC.write_text(f"# OLM RadialBlur PF32 Zoom Noise and Inner boundary — 2026-08-11\n\nStatus: **{status}**\n\nType-1 Noise 25/100, Inner Strength 50/100, and all four cross-product cells match actual AEX from pre/post polar planes through padded production output. Noise first materializes the source span; both radial directions then consume the same span and accumulate in source order before one normalization pass. Radius cell zero remains the unblurred center sample. NV50 remains fail-closed.\n");print(json.dumps({"status":status},sort_keys=True));return 0 if status=="noise_and_inner_exact" else 1
if __name__=="__main__":
 if len(sys.argv)==5 and sys.argv[1]=="--actual":Path(sys.argv[4]).write_bytes(pickle.dumps(actual(float(sys.argv[2]),float(sys.argv[3]))));raise SystemExit(0)
 if len(sys.argv)==6 and sys.argv[1]=="--production":
  try:r=production(float(sys.argv[2]),float(sys.argv[3]),pickle.loads(Path(sys.argv[4]).read_bytes()))
  except subprocess.CalledProcessError as e:raise SystemExit(e.returncode)
  Path(sys.argv[5]).write_bytes(pickle.dumps(r));raise SystemExit(0)
 raise SystemExit(main())
