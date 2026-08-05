#!/usr/bin/env python3
"""Independent PF8/PF16/PF32 actual-AEX corner-seed fixtures."""
from __future__ import annotations
import hashlib,json,struct,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa:E402
from test_olmtoondilate_pf16_pf32_copy_boundary_20260716 import AEX,alloc,context_and_suite,raw  # noqa:E402
ROOT=Path(__file__).resolve().parents[2]
REPORT=ROOT/"refs/conformance/olmtoondilate_corner_seed_all_depths_20260805.json"; MARKDOWN=REPORT.with_suffix(".md")
AEX_SHA="c05db8c118029ff3216d3cae8e6423e2eb41ca8f56de2fb3668db81b9b8c32b3"; W=H=5; RADIUS=4; PAD=0xA5
CFG={
  8:{"worker":0x1801A6150,"size":4,"bits":32,"pack":"<4B","a":(255,10,20,30),"b":(255,90,80,70),"c":(0,3,5,7)},
 16:{"worker":0x1801A5A90,"size":8,"bits":64,"pack":"<4H","a":(32768,1001,2002,3003),"b":(32768,4004,5005,6006),"c":(0,17,19,23)},
 32:{"worker":0x1801A6800,"size":16,"bits":128,"pack":"<4f","a":(1.0,.125,.25,.5),"b":(1.0,.75,.625,.375),"c":(0.0,.03125,.0625,.09375)},
}
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def labels():
    inf=2**32-1; d=[[inf]*W for _ in range(H)]; out=[["C"]*W for _ in range(H)]; d[0][0]=0;out[0][0]="A";d[4][4]=0;out[4][4]="B"
    def relax(x,y,cs):
        if d[y][x]==0:return
        best=inf;xy=None
        for nx,ny in cs:
            if 0<=nx<W and 0<=ny<H and d[ny][nx]<best:best=d[ny][nx];xy=(nx,ny)
        if xy and best!=inf and best+1<d[y][x]:
            d[y][x]=best+1
            if best+1<=RADIUS:out[y][x]=out[xy[1]][xy[0]]
    for y in range(H):
      for x in range(W):relax(x,y,((x-1,y),(x-1,y-1),(x,y-1),(x+1,y-1)))
    for y in range(H-1,-1,-1):
      for x in range(W-1,-1,-1):relax(x,y,((x+1,y),(x+1,y+1),(x,y+1),(x-1,y+1)))
    return out
def run(depth):
    c=CFG[depth]; rb=W*c["size"]+4; loader=AexLoader(str(AEX),verbose=False,fast=True)
    def world():
      buf=bytearray([PAD]*(rb*H))
      for y in range(H):
       for x in range(W):
        p=c["a"] if (x,y)==(0,0) else c["b"] if (x,y)==(4,4) else c["c"]
        struct.pack_into(c["pack"],buf,y*rb+x*c["size"],*p)
      data=alloc(loader,bytes(buf),align=64);h=bytearray(0x30);struct.pack_into("<QiiiH",h,0x18,data,rb,W,H,c["bits"]);return alloc(loader,bytes(h)),data
    iw,idata=world();ow,odata=world();worlds={iw:{"payload":idata,"width":W,"height":H,"rowbytes":rb,"pixel_size":c["size"]},ow:{"payload":odata,"width":W,"height":H,"rowbytes":rb,"pixel_size":c["size"]}}
    events=[];ctx=context_and_suite(loader,events,worlds);rp=alloc(loader,struct.pack("<f",4.0),align=16);call=loader.call_function(c["worker"],int_args=[ctx,0,iw,ow,rp],max_instructions=8_000_000)
    actual=bytes(raw(loader,odata,rb*H)); lab=labels(); expected=bytearray([PAD]*(rb*H))
    for y in range(H):
      for x in range(W): struct.pack_into(c["pack"],expected,y*rb+x*c["size"],*(c[lab[y][x].lower()]))
    vis=lambda b:b"".join(b[y*rb:y*rb+W*c["size"]] for y in range(H))
    gates={"worker_returned":True,"full_visible_four_word_exact":vis(actual)==vis(expected),"padding_preserved":all(actual[y*rb+W*c["size"]:(y+1)*rb]==bytes([PAD]*4) for y in range(H))}
    return {"depth":depth,"worker":hex(c["worker"]),"rowbytes":rb,"instructions":call["instructions"],"gates":gates,"label_rows":lab,"actual_visible_sha256":hashlib.sha256(vis(actual)).hexdigest()}
def main():
    if digest(AEX)!=AEX_SHA:raise SystemExit("BLOCKED_FAIL_CLOSED: AEX identity drifted")
    cases=[run(d) for d in (8,16,32)]; gates={"aex_sha256_exact":True,"three_independent_workers":len({x["worker"] for x in cases})==3,"all_depths_exact":all(all(x["gates"].values()) for x in cases)}
    status="PASS_CORNER_SEED_ALL_DEPTHS" if all(gates.values()) else "BLOCKED_FAIL_CLOSED"
    payload={"status":status,"schema":"olmtoondilate.corner-seed-all-depths/1","aex":str(AEX.relative_to(ROOT)),"aex_sha256":AEX_SHA,"fixture":{"width":W,"height":H,"radius":RADIUS,"seed_a":[0,0],"seed_b":[4,4],"padding_byte":PAD},"gates":gates,"cases":cases,"claim_boundary":"three independent actual-AEX typed workers on a corner-seed geometry under local Unicorn; no AE-host claim"}
    REPORT.write_text(json.dumps(payload,indent=2)+"\n");MARKDOWN.write_text(f"# OLMToonDilate Corner Seeds All Depths — 2026-08-05\n\n- Status: **{status}**\n- Independent PF8/PF16/PF32 worker runs on a padded 5x5 corner-seed fixture.\n- All visible four-word outputs and padding exact: `{gates['all_depths_exact']}`.\n- No AE-host claim.\n")
    print(json.dumps(payload,indent=2));return 0 if status.startswith("PASS") else 1
if __name__=="__main__":raise SystemExit(main())
