#!/usr/bin/env python3
"""PF32 NaN payload/sign and infinity full-frame proof through Smart EffectMain."""

from __future__ import annotations

import hashlib, json, struct
from pathlib import Path
import test_colorkeep_effectmain_padded_frame_20260805 as adapter
import test_colorkeep_typed_padded_frame_actual_aex_20260805 as oracle

ROOT=Path(__file__).resolve().parents[2]
REPORT=ROOT/"refs/conformance/colorkeep_pf32_nan_inf_effectmain_actual_aex_20260805.json"
def f(bits): return struct.unpack("<f",struct.pack("<I",bits))[0]
QNAN=f(0x7fc12345); NQNAN=f(0xffc54321)
COLORS=((.71,.10,.11,.12),(.72,QNAN,.21,.22),(.73,.30,.31,NQNAN),(.74,float("inf"),.41,.42),(.75,.50,float("-inf"),.52))
PIXELS=((.71,QNAN,.11,.12),(.71,NQNAN,.11,.12),(.72,.99,.21,.22),(.73,.30,.31,.99),(.74,float("inf"),.41,.42),(.75,.50,float("-inf"),.52),(.76,float("inf"),.61,.62),(.74,.99,.41,.42))

def main():
    oracle.COLORS=COLORS;oracle.DEPTHS={"PF32":(0x180001850,"<4f",PIXELS)}
    rows=[b"".join(struct.pack("<4f",*PIXELS[(y*4+x)%len(PIXELS)]) for x in range(4))+b"\xcc"*8 for y in range(3)]
    raw32=b"".join(rows);expected=oracle.actual_frame(0x180001850,"<4f",PIXELS)
    dummy={"PF8":b"\xcc"*72,"PF16":b"\xcc"*120,"PF32":raw32}
    observed=adapter.compile_and_run(dummy,pf32_only=True)
    assert observed==expected
    rb=72; match_pattern=(True,True,True,True,True,True,False,False)
    witnesses=[]
    for y in range(3):
        for x in range(4):
            i=y*4+x; source=struct.pack("<4f",*PIXELS[i%len(PIXELS)])
            out=expected[y*rb+x*16:y*rb+(x+1)*16]
            assert out[4:]==source[4:]
            expected_alpha=source[:4] if match_pattern[i%len(PIXELS)] else b"\0\0\0\0"
            assert out[:4]==expected_alpha
            if i<8:witnesses.append({"case":i,"source_argb_bits":[f"0x{v:08x}" for v in struct.unpack("<4I",source)],"output_argb_bits":[f"0x{v:08x}" for v in struct.unpack("<4I",out)],"match":match_pattern[i]})
        assert expected[y*rb+64:(y+1)*rb]==b"\xee"*8
    report={"status":"exact","depth":"PF32 only","actual_aex_sha256":oracle.AEX_SHA256,"dynamic_path":"EffectMain(SmartPreRender)->EffectMain(SmartRender)->PF32 iterate","enabled_key_cases":["positive NaN red payload 0x7fc12345","negative NaN blue payload 0xffc54321","positive infinity red","negative infinity green"],"source_cases":["positive/negative NaN payloads","positive/negative infinity","finite against infinity key","infinity no-match"],"semantics":"unordered NaN and same-sign infinity subtraction fall through COMISS/JA as within tolerance when all other components match; finite-vs-infinity and unrelated infinity reject","smart_dependencies":{"checkout_count":101,"ordered_indices":list(range(1,102))},"fixture":"4x3 PF32, rowbytes72, 8-byte input/output padding","witnesses":witnesses,"raw_output_sha256":hashlib.sha256(expected).hexdigest(),"not_proven":["PF8/PF16 generalization","After Effects host execution/export","signaling-NaN exception behavior"]}
    REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n");print(json.dumps(report,indent=2,sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
