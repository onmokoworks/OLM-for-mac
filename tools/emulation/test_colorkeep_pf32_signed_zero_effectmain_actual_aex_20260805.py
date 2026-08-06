#!/usr/bin/env python3
"""PF32 signed-zero source/key comparison and raw-copy proof."""

from __future__ import annotations
import hashlib,json,struct
from pathlib import Path
import test_colorkeep_effectmain_padded_frame_20260805 as adapter
import test_colorkeep_typed_padded_frame_actual_aex_20260805 as oracle

ROOT=Path(__file__).resolve().parents[2];REPORT=ROOT/"refs/conformance/colorkeep_pf32_signed_zero_effectmain_actual_aex_20260805.json"
PZ=0.0;NZ=struct.unpack("<f",struct.pack("<I",0x80000000))[0]
COLORS=((.71,PZ,.11,.12),(.72,NZ,.21,.22),(.73,.30,NZ,.32),(.74,.40,PZ,.42))
PIXELS=((.71,NZ,.11,.12),(.72,PZ,.21,.22),(.73,.30,PZ,.32),(.74,.40,NZ,.42),(.75,NZ,.51,.52))

def bits(v):return [f"0x{x:08x}" for x in struct.unpack("<4I",struct.pack("<4f",*v))]
def main():
 oracle.COLORS=COLORS;oracle.DEPTHS={"PF32":(0x180001850,"<4f",PIXELS)}
 raw=b"".join(b"".join(struct.pack("<4f",*PIXELS[(y*4+x)%len(PIXELS)]) for x in range(4))+b"\xcc"*8 for y in range(3));expected=oracle.actual_frame(0x180001850,"<4f",PIXELS)
 observed=adapter.compile_and_run({"PF8":b"\xcc"*72,"PF16":b"\xcc"*120,"PF32":raw},pf32_only=True);assert observed==expected
 rb=72;match=(True,True,True,True,False);w=[]
 for i in range(12):
  y,x=divmod(i,4);src=struct.pack("<4f",*PIXELS[i%5]);out=expected[y*rb+x*16:y*rb+(x+1)*16]
  assert out[4:]==src[4:];assert out[:4]==(src[:4] if match[i%5] else b"\0"*4)
  if i<5:w.append({"case":i,"source_bits":bits(PIXELS[i]),"output_bits":[f"0x{x:08x}" for x in struct.unpack("<4I",out)],"match":match[i]})
 for y in range(3):assert expected[y*rb+64:(y+1)*rb]==b"\xee"*8
 report={"status":"exact","depth":"PF32 only","actual_aex_sha256":oracle.AEX_SHA256,"cases":["+0 key / -0 source","-0 key / +0 source","-0 key green / +0 source green","+0 key green / -0 source green","signed-zero no-match"],"comparison_semantics":"+0 and -0 compare equal","raw_copy_semantics":"matching output preserves the source RGB zero sign bit; it does not canonicalize to the key sign","dynamic_path":"SmartPreRender->SmartRender->PF32 iterate","smart_dependencies":{"checkout_count":101,"ordered_indices":list(range(1,102))},"fixture":"4x3 PF32, rowbytes72, padding8","witnesses":w,"raw_output_sha256":hashlib.sha256(expected).hexdigest(),"not_proven":["PF8/PF16 generalization","After Effects host execution/export"]}
 REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n");print(json.dumps(report,indent=2,sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
