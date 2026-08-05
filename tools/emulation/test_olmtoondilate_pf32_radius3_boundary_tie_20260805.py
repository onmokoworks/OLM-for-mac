#!/usr/bin/env python3
"""Independent actual-AEX PF32 radius-3 boundary/tie fixture."""
from __future__ import annotations
import hashlib, json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402
from test_olmtoondilate_pf16_pf32_copy_boundary_20260716 import AEX, alloc, context_and_suite, raw  # noqa: E402

ROOT=Path(__file__).resolve().parents[2]
REPORT=ROOT/"refs/conformance/olmtoondilate_pf32_radius3_boundary_tie_20260805.json"; MARKDOWN=REPORT.with_suffix(".md")
AEX_SHA256="c05db8c118029ff3216d3cae8e6423e2eb41ca8f56de2fb3668db81b9b8c32b3"
WORKER,WIDTH,HEIGHT,ROWBYTES,RADIUS=0x1801A6800,7,3,116,3
PIXEL_BYTES,PAD=16,0xA5
A=(1.0,0.125,0.25,0.5); B=(1.0,0.75,0.625,0.375); CLEAR=(0.0,0.03125,0.0625,0.09375)
def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def make_world(loader):
    buf=bytearray([PAD]*(ROWBYTES*HEIGHT))
    for y in range(HEIGHT):
        for x in range(WIDTH):
            p=A if (x,y)==(0,1) else B if (x,y)==(6,1) else CLEAR
            struct.pack_into("<4f",buf,y*ROWBYTES+x*16,*p)
    data=alloc(loader,bytes(buf),align=64); header=bytearray(0x30); struct.pack_into("<QiiiH",header,0x18,data,ROWBYTES,WIDTH,HEIGHT,128)
    return alloc(loader,bytes(header)),data
def visible(w): return b"".join(w[y*ROWBYTES:y*ROWBYTES+WIDTH*16] for y in range(HEIGHT))
def expected():
    out=bytearray(); splits=(3,4,4)
    for y in range(HEIGHT):
        for x in range(WIDTH): out.extend(struct.pack("<4f",*(A if x<splits[y] else B)))
    return bytes(out)
def main():
    if digest(AEX)!=AEX_SHA256: raise SystemExit("BLOCKED_FAIL_CLOSED: AEX identity drifted")
    loader=AexLoader(str(AEX),verbose=False,fast=True); iw,idata=make_world(loader); ow,odata=make_world(loader)
    worlds={iw:{"payload":idata,"width":WIDTH,"height":HEIGHT,"rowbytes":ROWBYTES,"pixel_size":16},ow:{"payload":odata,"width":WIDTH,"height":HEIGHT,"rowbytes":ROWBYTES,"pixel_size":16}}
    events=[]; context=context_and_suite(loader,events,worlds); radius=alloc(loader,struct.pack("<f",3.0),align=16)
    call=loader.call_function(WORKER,int_args=[context,0,iw,ow,radius],max_instructions=6_000_000)
    world=bytes(raw(loader,odata,ROWBYTES*HEIGHT)); actual=visible(world); oracle=expected()
    words=lambda i:list(struct.unpack("<4I",actual[i:i+16])); top=words(3*16); middle=words((WIDTH+3)*16)
    a_words=list(struct.unpack("<4I",struct.pack("<4f",*A))); b_words=list(struct.unpack("<4I",struct.pack("<4f",*B)))
    gates={"aex_sha256_exact":digest(AEX)==AEX_SHA256,"worker_returned":True,"full_visible_raw_four_word_exact":actual==oracle,
           "top_tie_prefers_right_seed":top==b_words,"middle_tie_prefers_left_seed":middle==a_words,
           "padding_preserved":all(world[y*ROWBYTES+WIDTH*16:(y+1)*ROWBYTES]==bytes([PAD]*4) for y in range(HEIGHT))}
    status="PASS_PF32_RADIUS3_BOUNDARY_TIE" if all(gates.values()) else "BLOCKED_FAIL_CLOSED"
    payload={"status":status,"schema":"olmtoondilate.pf32-radius3-boundary-tie/1","aex":str(AEX.relative_to(ROOT)),"aex_sha256":AEX_SHA256,"worker":hex(WORKER),
             "fixture":{"width":WIDTH,"height":HEIGHT,"rowbytes":ROWBYTES,"radius":RADIUS,"left_seed":[0,1],"right_seed":[6,1],"left_raw_words":a_words,"right_raw_words":b_words,"padding_byte":PAD},
             "execution":{"instructions":call["instructions"],"return_rax":hex(call["rax"])},"gates":gates,
             "actual_visible_sha256":hashlib.sha256(actual).hexdigest(),"expected_visible_sha256":hashlib.sha256(oracle).hexdigest(),
             "claim_boundary":"independent bounded actual-AEX PF32 raw-word radius-3 boundary/tie fixture; no PF8/PF16 or AE-host inference"}
    REPORT.write_text(json.dumps(payload,indent=2)+"\n"); MARKDOWN.write_text(f"# OLMToonDilate PF32 Radius-3 Boundary Tie — 2026-08-05\n\n- Status: **{status}**\n- Independent PF32 actual-AEX worker execution; no PF8/PF16 fixture is consumed.\n- Full visible raw FLOAT32 four-word exact: `{gates['full_visible_raw_four_word_exact']}`.\n- Top tie selects right and middle tie selects left.\n- Bounded worker evidence only; no AE-host claim.\n")
    print(json.dumps(payload,indent=2)); return 0 if status.startswith("PASS") else 1
if __name__=="__main__": raise SystemExit(main())
