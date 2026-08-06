#!/usr/bin/env python3
"""PF32 signaling-NaN raw-output and emulator FP-status investigation."""

from __future__ import annotations

import hashlib,json,struct
from pathlib import Path
from unicorn.x86_const import UC_X86_REG_MXCSR
import test_colorkeep_effectmain_padded_frame_20260805 as adapter
import test_colorkeep_typed_padded_frame_actual_aex_20260805 as oracle
from aex_loader import AexLoader

ROOT=Path(__file__).resolve().parents[2];REPORT=ROOT/"refs/conformance/colorkeep_pf32_snan_effectmain_actual_aex_20260805.json";AEX=ROOT/"aex/OLMColorKeep/Plugins/64/2025/ColorKeep.aex"
def f(bits):return struct.unpack("<f",struct.pack("<I",bits))[0]
PSNAN,NSNAN=f(0x7f812345),f(0xff854321)
COLORS=((.71,.10,.11,.12),(.72,PSNAN,.21,.22),(.73,.30,.31,NSNAN))
PIXELS=((.71,PSNAN,.11,.12),(.71,NSNAN,.11,.12),(.72,.99,.21,.22),(.73,.30,.31,.99),(.76,.9,.8,.7))

def direct(source,color):
 l=AexLoader(str(AEX),verbose=False,fast=True);r=l.host_alloc(0x38);s=l.host_alloc(16);d=l.host_alloc(16)
 l.write_bytes(r+0x24,struct.pack("<i",1));l.write_bytes(r+0x28,struct.pack("<4f",*color));l.write_bytes(s,struct.pack("<4f",*source));l.write_bytes(d,b"\xa5"*16)
 before=l.uc.reg_read(UC_X86_REG_MXCSR);l.call_function(0x180001850,int_args=[r,0,0,s,d],max_instructions=10000);after=l.uc.reg_read(UC_X86_REG_MXCSR)
 return {"source_bits":[f"0x{x:08x}" for x in struct.unpack("<4I",struct.pack("<4f",*source))],"key_bits":[f"0x{x:08x}" for x in struct.unpack("<4I",struct.pack("<4f",*color))],"output_bits":[f"0x{x:08x}" for x in struct.unpack("<4I",l.read_bytes(d,16))],"mxcsr_before":f"0x{before:08x}","mxcsr_after":f"0x{after:08x}"}

def main():
 witnesses={"source_positive_snan":direct(PIXELS[0],COLORS[0]),"source_negative_snan":direct(PIXELS[1],COLORS[0]),"key_positive_snan":direct(PIXELS[2],COLORS[1]),"key_negative_snan":direct(PIXELS[3],COLORS[2])}
 oracle.COLORS=COLORS;oracle.DEPTHS={"PF32":(0x180001850,"<4f",PIXELS)}
 raw=b"".join(b"".join(struct.pack("<4f",*PIXELS[(y*4+x)%len(PIXELS)]) for x in range(4))+b"\xcc"*8 for y in range(3));expected=oracle.actual_frame(0x180001850,"<4f",PIXELS)
 observed=adapter.compile_and_run({"PF8":b"\xcc"*72,"PF16":b"\xcc"*120,"PF32":raw},pf32_only=True);assert observed==expected
 for name in ("source_positive_snan","source_negative_snan"):
  assert witnesses[name]["output_bits"][1]==witnesses[name]["source_bits"][1]
 report={"status":"exact_raw_output","actual_aex_sha256":oracle.AEX_SHA256,"depth":"PF32 only","snan_bits":{"positive":"0x7f812345","negative":"0xff854321"},"direct_actual_worker_witnesses":witnesses,"raw_behavior":"source sNaN payload/sign is copied unchanged to RGB output when the unordered comparison matches; key-side sNaN permits an unordered channel match without appearing in output","quieting":"SUBSS may quiet its temporary result, but the AEX output copies the original source word, so no quiet-bit change is observable in output","exception_status":{"unicorn_observation":"MXCSR remained 0 before/after all calls","interpretation":"the local Unicorn backend does not model the SSE invalid-operation status for sNaN; this is not evidence that native x86 raises no exception","production_equivalence":"raw pixels exact; cross-architecture FP exception flags unproven and intentionally not claimed"},"dynamic_path":"SmartPreRender->SmartRender->PF32 iterate","smart_dependencies":{"checkout_count":101,"ordered_indices":list(range(1,102))},"fixture":"4x3 PF32, rowbytes72, padding8","raw_output_sha256":hashlib.sha256(expected).hexdigest(),"not_proven":["native Windows MXCSR invalid flag","macOS ARM FPSR equivalence","signaling trap mode","PF8/PF16 or AE host/export"]}
 REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n");print(json.dumps(report,indent=2,sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
