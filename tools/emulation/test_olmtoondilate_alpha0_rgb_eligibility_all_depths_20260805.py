#!/usr/bin/env python3
"""Actual-AEX all-depth alpha-zero/nonzero-RGB seed-eligibility fixture."""
from __future__ import annotations
import hashlib,json,struct,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa:E402
from test_olmtoondilate_pf16_pf32_copy_boundary_20260716 import AEX,alloc,context_and_suite,raw  # noqa:E402
ROOT=Path(__file__).resolve().parents[2];REPORT=ROOT/"refs/conformance/olmtoondilate_alpha0_rgb_eligibility_all_depths_20260805.json";MARKDOWN=REPORT.with_suffix(".md")
AEX_SHA="c05db8c118029ff3216d3cae8e6423e2eb41ca8f56de2fb3668db81b9b8c32b3";W,H,RADIUS,PAD=5,3,4,0xA5
CFG={8:(0x1801A6150,4,32,"<4B",(0,201,101,51),(255,10,20,30),(0,0,0,0)),16:(0x1801A5A90,8,64,"<4H",(0,50001,40002,30003),(32768,1001,2002,3003),(0,0,0,0)),32:(0x1801A6800,16,128,"<4f",(0.0,.875,.625,.375),(1.0,.125,.25,.5),(0.0,0.0,0.0,0.0))}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(depth):
 worker,size,bits,fmt,alpha0,opaque,clear=CFG[depth];rb=W*size+4;loader=AexLoader(str(AEX),verbose=False,fast=True)
 def world():
  buf=bytearray([PAD]*(rb*H))
  for y in range(H):
   for x in range(W):
    p=alpha0 if (x,y)==(0,1) else opaque if (x,y)==(4,1) else clear
    struct.pack_into(fmt,buf,y*rb+x*size,*p)
  data=alloc(loader,bytes(buf),align=64);head=bytearray(0x30);struct.pack_into("<QiiiH",head,0x18,data,rb,W,H,bits);return alloc(loader,bytes(head)),data
 iw,idata=world();ow,odata=world();worlds={iw:{"payload":idata,"width":W,"height":H,"rowbytes":rb,"pixel_size":size},ow:{"payload":odata,"width":W,"height":H,"rowbytes":rb,"pixel_size":size}}
 events=[];ctx=context_and_suite(loader,events,worlds);rp=alloc(loader,struct.pack("<f",4.0),align=16);call=loader.call_function(worker,int_args=[ctx,0,iw,ow,rp],max_instructions=6_000_000);actual=bytes(raw(loader,odata,rb*H));expected=bytearray([PAD]*(rb*H))
 for y in range(H):
  for x in range(W):struct.pack_into(fmt,expected,y*rb+x*size,*opaque)
 vis=lambda b:b"".join(b[y*rb:y*rb+W*size] for y in range(H));g={"worker_returned":True,"alpha0_rgb_rejected_as_seed":vis(actual)==vis(expected),"full_visible_four_word_exact":vis(actual)==vis(expected),"padding_preserved":all(actual[y*rb+W*size:(y+1)*rb]==bytes([PAD]*4) for y in range(H))}
 return {"depth":depth,"worker":hex(worker),"rowbytes":rb,"instructions":call["instructions"],"alpha0_words":list(struct.unpack("<4I",struct.pack("<4f",*alpha0))) if depth==32 else list(alpha0),"opaque_words":list(struct.unpack("<4I",struct.pack("<4f",*opaque))) if depth==32 else list(opaque),"gates":g,"actual_visible_sha256":hashlib.sha256(vis(actual)).hexdigest()}
def main():
 if sha(AEX)!=AEX_SHA:raise SystemExit("BLOCKED_FAIL_CLOSED: AEX identity drifted")
 cases=[run(d) for d in (8,16,32)];g={"aex_sha256_exact":True,"three_independent_workers":len({c["worker"] for c in cases})==3,"all_depths_alpha0_nonseed_exact":all(all(c["gates"].values()) for c in cases)};status="PASS_ALPHA0_RGB_ELIGIBILITY_ALL_DEPTHS" if all(g.values()) else "BLOCKED_FAIL_CLOSED"
 p={"status":status,"schema":"olmtoondilate.alpha0-rgb-eligibility-all-depths/1","aex":str(AEX.relative_to(ROOT)),"aex_sha256":AEX_SHA,"fixture":{"width":W,"height":H,"radius":RADIUS,"alpha0_rgb_candidate":[0,1],"opaque_seed":[4,1],"padding_byte":PAD},"gates":g,"cases":cases,"claim_boundary":"independent actual-AEX typed-worker proof that alpha-zero nonzero-RGB pixels are not seeds; no AE-host claim"}
 REPORT.write_text(json.dumps(p,indent=2)+"\n");MARKDOWN.write_text(f"# OLMToonDilate Alpha-0 RGB Eligibility — 2026-08-05\n\n- Status: **{status}**\n- PF8/PF16/PF32 workers run independently.\n- The alpha-zero, nonzero-RGB candidate loses to the opaque seed at every output pixel.\n- Full typed-word and padding exact: `{g['all_depths_alpha0_nonseed_exact']}`.\n- No AE-host claim.\n");print(json.dumps(p,indent=2));return 0 if status.startswith("PASS") else 1
if __name__=="__main__":raise SystemExit(main())
