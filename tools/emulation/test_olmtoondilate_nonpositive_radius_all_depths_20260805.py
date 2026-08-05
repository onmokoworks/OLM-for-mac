#!/usr/bin/env python3
"""Actual-AEX typed fixtures for zero and negative Search Radius."""
from __future__ import annotations
import hashlib,json,struct,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa:E402
from test_olmtoondilate_pf16_pf32_copy_boundary_20260716 import AEX,alloc,context_and_suite,raw  # noqa:E402
ROOT=Path(__file__).resolve().parents[2];REPORT=ROOT/"refs/conformance/olmtoondilate_nonpositive_radius_all_depths_20260805.json";MARKDOWN=REPORT.with_suffix(".md")
AEX_SHA="c05db8c118029ff3216d3cae8e6423e2eb41ca8f56de2fb3668db81b9b8c32b3";W,H,PAD=3,2,0xA5
CFG={8:(0x1801A6150,4,32,"<4B",[(255,10,20,30),(0,201,101,51),(128,81,41,21),(0,3,5,7),(255,90,80,70),(1,11,13,17)]),16:(0x1801A5A90,8,64,"<4H",[(32768,1001,2002,3003),(0,50001,40002,30003),(16384,8001,7002,6003),(0,17,19,23),(32768,4004,5005,6006),(1,101,103,107)]),32:(0x1801A6800,16,128,"<4f",[(1.0,.125,.25,.5),(0.0,.875,.625,.375),(.5,.8,.4,.2),(0.0,.03125,.0625,.09375),(1.0,.75,.625,.375),(.001,.11,.13,.17)])}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(depth,radius):
 worker,size,bits,fmt,pixels=CFG[depth];rb=W*size+4;loader=AexLoader(str(AEX),verbose=False,fast=True)
 def world():
  buf=bytearray([PAD]*(rb*H))
  for i,p in enumerate(pixels):struct.pack_into(fmt,buf,(i//W)*rb+(i%W)*size,*p)
  data=alloc(loader,bytes(buf),align=64);head=bytearray(0x30);struct.pack_into("<QiiiH",head,0x18,data,rb,W,H,bits);return alloc(loader,bytes(head)),data,bytes(buf)
 iw,idata,original=world();ow,odata,_=world();worlds={iw:{"payload":idata,"width":W,"height":H,"rowbytes":rb,"pixel_size":size},ow:{"payload":odata,"width":W,"height":H,"rowbytes":rb,"pixel_size":size}}
 events=[];ctx=context_and_suite(loader,events,worlds);rp=alloc(loader,struct.pack("<f",radius),align=16);call=loader.call_function(worker,int_args=[ctx,0,iw,ow,rp],max_instructions=2_000_000);actual=bytes(raw(loader,odata,rb*H));vis=lambda b:b"".join(b[y*rb:y*rb+W*size] for y in range(H))
 gates={"worker_returned":True,"visible_typed_bytes_copy_exact":vis(actual)==vis(original),"padding_preserved":all(actual[y*rb+W*size:(y+1)*rb]==bytes([PAD]*4) for y in range(H)),"nontrivial_source":len(set(vis(original)))>4}
 return {"depth":depth,"radius":radius,"worker":hex(worker),"rowbytes":rb,"instructions":call["instructions"],"gates":gates,"visible_sha256":hashlib.sha256(vis(actual)).hexdigest()}
def main():
 if sha(AEX)!=AEX_SHA:raise SystemExit("BLOCKED_FAIL_CLOSED: AEX identity drifted")
 cases=[run(d,r) for d in (8,16,32) for r in (0.0,-1.0)];g={"aex_sha256_exact":True,"six_independent_runs":len(cases)==6,"all_nonpositive_copy_exact":all(all(c["gates"].values()) for c in cases)};status="PASS_NONPOSITIVE_RADIUS_ALL_DEPTHS" if all(g.values()) else "BLOCKED_FAIL_CLOSED"
 p={"status":status,"schema":"olmtoondilate.nonpositive-radius-all-depths/1","aex":str(AEX.relative_to(ROOT)),"aex_sha256":AEX_SHA,"fixture":{"width":W,"height":H,"radii":[0.0,-1.0],"mixed_alpha_and_zero_alpha_nonzero_rgb":True,"padding_byte":PAD},"gates":g,"cases":cases,"claim_boundary":"bounded actual-AEX typed-worker zero/negative-radius copy behavior; SmartRender host extent clipping remains unproved"}
 REPORT.write_text(json.dumps(p,indent=2)+"\n");MARKDOWN.write_text(f"# OLMToonDilate Nonpositive Radius — 2026-08-05\n\n- Status: **{status}**\n- PF8/PF16/PF32 workers run independently at radius 0 and -1.\n- Mixed-alpha visible typed bytes and row padding remain exact copies: `{g['all_nonpositive_copy_exact']}`.\n- Extent clipping and AE-host behavior remain unproved.\n");print(json.dumps(p,indent=2));return 0 if status.startswith("PASS") else 1
if __name__=="__main__":raise SystemExit(main())
