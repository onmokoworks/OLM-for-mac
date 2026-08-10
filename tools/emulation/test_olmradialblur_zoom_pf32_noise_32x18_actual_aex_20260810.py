#!/usr/bin/env python3
"""Independent 32x18 PF32 Zoom Type-1 Noise geometry witness."""
from __future__ import annotations
import hashlib,json,pickle,struct,subprocess,sys,tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];HERE=ROOT/"tools/emulation";sys.path.insert(0,str(HERE))
import test_olmradialblur_zoom_pf32_small_actual_aex_20260805 as wrapper  # noqa:E402
pf8=wrapper.fixture;zoom=pf8.zoom;W,H,RB,VISIBLE=32,18,528,512
REPORT=ROOT/"refs/conformance/olmradialblur_zoom_pf32_noise_32x18_actual_aex_20260810.json";DOC=REPORT.with_suffix(".md")
def sha(b):return hashlib.sha256(b).hexdigest()
def source_frame(seed=False):
 raw=bytearray(RB*H)
 for y in range(H):
  for x in range(W):
   argb=(-7.,-6.,-5.,-4.) if seed else (0.5 if (x+y)%7==0 else 1.,((x*31+y*7)%257)/256.,((x*11+y*29)%257)/256.,((x*47+y*13)%257)/256.)
   struct.pack_into("<4f",raw,y*RB+x*16,*argb)
  raw[y*RB+VISIBLE:(y+1)*RB]=bytes([0x80+y])*(RB-VISIBLE)
 return bytes(raw)
def build_world(loader,payload):
 data=loader.bump_alloc(len(payload),align=64);loader.write_bytes(data,payload);world=loader.host_alloc(0x80);loader.write_bytes(world,b"\0"*0x80);loader.write_bytes(world+0x18,struct.pack("<Q",data));loader.write_bytes(world+0x20,struct.pack("<I",RB));loader.write_bytes(world+0x24,struct.pack("<I",W));loader.write_bytes(world+0x28,struct.pack("<I",H));loader.write_bytes(world+0x2C,struct.pack("<H",32));return world,data
def configure(noise):
 pf8.W,pf8.H,pf8.ROWBYTES,pf8.VISIBLE=W,H,RB,VISIBLE;pf8.PIXEL_CPP="PF_PixelFloat";pf8.PIXEL_BYTES=16;pf8.BITDEPTH=32;pf8.ZOOM_RETURN=0x180008322;pf8.USE_RENDER_WORLD_FINAL=True;pf8.source_frame=source_frame;pf8.build_world=build_world;pf8.configure()
 zoom.INNER_STRENGTH=0;zoom.NOISE_VARIATION=noise;zoom.CENTER_X=16.;zoom.CENTER_Y=9.;zoom.PADDING_BASE=0x80;zoom.PIXEL_CPP="PF_PixelFloat";zoom.PIXEL_BYTES=16;zoom.USE_RENDER_WORLD_FINAL=True;zoom.RENDER_WORLD_BITDEPTH=32;zoom.ZOOM_RETURN=0x180008322;zoom.fixture.W,zoom.fixture.H,zoom.fixture.ROWBYTES,zoom.fixture.VISIBLE=W,H,RB,VISIBLE;zoom.fixture.source_frame=source_frame;zoom.fixture.build_world=build_world
def actual(n):configure(n);return zoom.actual_aex()
def production(n,e):configure(n);return zoom.mac_production(e)
def isolated(mode,n,e=None):
 with tempfile.TemporaryDirectory(prefix="radial_zoom32_") as d:
  out=Path(d)/"out.pkl";cmd=[sys.executable,str(Path(__file__)),f"--{mode}",str(n)]
  if e is not None:inp=Path(d)/"in.pkl";inp.write_bytes(pickle.dumps(e));cmd.append(str(inp))
  cmd.append(str(out));subprocess.run(cmd,check=True);return pickle.loads(out.read_bytes())
def main():
 vals=(0.,25.,100.)
 with ThreadPoolExecutor(max_workers=3) as pool:a=dict(zip(vals,pool.map(lambda n:isolated("actual",n),vals)))
 rows=[];ok=True
 for n in vals:
  m=isolated("production",n,a[n]);matches={k:m[k]==a[n][k] for k in ("pre_blur","post_blur","output")};ok&=all(matches.values());rows.append({"noise_variation":n,"matches":matches,"actual_hashes":{k:sha(a[n][k]) for k in ("pre_blur","post_blur","output")},"output_differs_noise0":n==0 or a[n]["output"]!=a[0.]["output"]})
 status="exact" if ok else "mismatch";report={"kind":"olmradialblur_zoom_pf32_noise_32x18_actual_aex_20260810","status":status,"scope":"PF32 Zoom 32x18 rowbytes528; outer Strength4; Type1 NV0/25/100; centered neutral tuple.","aex_sha256":zoom.fixture.AEX_SHA256,"cases":rows,"geometry_rule":"Center is materialized in composition coordinates and scaled by w/comp_width and h/comp_height. Active-pixel mismatch was a 9x7-only probe center literal (4,3); the remaining raw-buffer mismatch was a probe padding seed literal. Neither required a production inverse-coordinate special case.","boundary":"Independent second geometry proves the centered same-shape coordinate rule only; no arbitrary off-center geometry, Inner Strength, other noise type/seed/offset/thickness or AE-host claim."};REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n");DOC.write_text(f"# OLM RadialBlur PF32 Zoom Noise 32×18\n\nStatus: **{status}**\n\nActual AEX and production match for pre/post polar planes and padded final output at Noise 0/25/100. The apparent final mismatch had two probe-only causes: the retained 9×7 center literal `(4,3)` affected active pixels, then the retained `0xA0+y` padding seed affected only row padding. Materializing public center `(16,9)` and the fixture padding contract closes the general centered same-shape rule without a geometry-specific output mapping.\n");print(status);return 0 if ok else 1
if __name__=="__main__":
 if len(sys.argv)==4 and sys.argv[1]=="--actual":Path(sys.argv[3]).write_bytes(pickle.dumps(actual(float(sys.argv[2]))));raise SystemExit(0)
 if len(sys.argv)==5 and sys.argv[1]=="--production":Path(sys.argv[4]).write_bytes(pickle.dumps(production(float(sys.argv[2]),pickle.loads(Path(sys.argv[3]).read_bytes()))));raise SystemExit(0)
 raise SystemExit(main())
