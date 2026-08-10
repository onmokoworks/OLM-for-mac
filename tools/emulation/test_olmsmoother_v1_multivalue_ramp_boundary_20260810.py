#!/usr/bin/env python3
"""Lock the PF16 FMA fix and the remaining PF8 multivalue-ramp boundary."""
import hashlib, json, struct, tempfile
from pathlib import Path

import test_olmsmoother_v1_key_tolerance_geometry_actual_aex_20260810 as base

ROOT=Path(__file__).resolve().parents[2]
REPORT=ROOT/'refs/conformance/olmsmoother_v1_multivalue_ramp_boundary_20260810.json'
DOC=ROOT/'refs/conformance/olmsmoother_v1_multivalue_ramp_boundary_20260810.md'

def fixture(depth):
    keys={(0,0),(6,0),(3,2),(0,4),(6,4)}; pixels=[]
    for y in range(base.H):
        for x in range(base.W):
            v=(x*17+y*23)&255
            pixels.append((255,*base.KEY) if (x,y) in keys else (255,v,v,v))
    size=4 if depth==8 else 8; rowbytes=base.W*size+8; raw=bytearray()
    for y in range(base.H):
        for p in pixels[y*base.W:(y+1)*base.W]:
            raw += bytes(p) if depth==8 else struct.pack('<4H',*(base.widen(v) for v in p))
        raw += bytes([0xd0+y])*8
    return bytes(raw),rowbytes

def main():
    assert hashlib.sha256(base.AEX.read_bytes()).hexdigest()==base.AEX_SHA
    temporary,lib=base.build_production(); rows=[]
    try:
        with tempfile.TemporaryDirectory(prefix='sm1-ramp-guest-') as td:
            codes={d:base.guest_code(Path(td),4 if d==8 else 8) for d in (8,16)}
        for depth in (8,16):
            payload,rowbytes=fixture(depth)
            for use_key in (0,1):
                for tolerance in base.TOLERANCES:
                    win,_=base.actual(depth,payload,rowbytes,use_key,tolerance,codes[depth])
                    mac=base.production(lib,depth,payload,rowbytes,use_key,tolerance)
                    diffs=[i for i,(a,b) in enumerate(zip(win,mac)) if a!=b]
                    rows.append({'depth':depth,'use_key':use_key,'tolerance':tolerance,
                                 'mismatched_bytes':len(diffs),'first_mismatch':diffs[0] if diffs else None,
                                 'actual_sha256':hashlib.sha256(win).hexdigest(),
                                 'production_sha256':hashlib.sha256(mac).hexdigest()})
    finally: temporary.cleanup()
    assert all(r['mismatched_bytes']==0 for r in rows)
    report={'schema_version':1,'status':'exact','verdict':'PASS_PF8_PF16_MULTIVALUE_RAMP_ALL_20_CELLS_EXACT',
      'actual_aex_sha256':base.AEX_SHA,
      'scope':'padded nonuniform 7x5 multivalue grayscale ramp with five exact-key islands; Use Key off/on x tolerance 0/1/6/127/255 x PF8/PF16',
      'pf16_closed_boundary':'all 10 exported PF_Cmd_RENDER versus production EffectMain cells are byte exact after preserving Windows MULSS/MULSS/ADDSS binary32 rounding in AlphaBlend16',
      'pf8_closed_boundary':'all 10 cells are exact after matching scalar-SSE operation boundaries and the AEX signed-luma truncation-toward-zero import behavior in ColorCompare8',
      'pf8_diagnosis':{'pre_fix_residual':'tolerance 6, key off/on, three pixels, nine RGB bytes',
        'first_pixel_xy':[4,1],
        'actual_executor_order_before_fix':[
          {'direction':7,'start':[4,1],'end':[4,1],'source_color_xy':[4,0],'other_color_xy':[4,1],'weight':0.875,'use_source':1,'leading_span':-1},
          {'direction':5,'start':[4,1],'end':[4,1],'source_color_xy':[3,1],'other_color_xy':[4,1],'weight':0.875,'use_source':1,'leading_span':-1},
          {'direction':5,'start':[4,1],'end':[4,1],'source_color_xy':[4,1],'other_color_xy':[5,1],'weight':0.125,'use_source':1,'leading_span':0},
          {'direction':7,'start':[4,1],'end':[4,1],'source_color_xy':[4,1],'other_color_xy':[4,2],'weight':0.125,'use_source':1,'leading_span':0}],
        'production_before_fix':'the fourth callback was absent because ColorCompare8 rounded signed luma away from zero and changed the SubHandler caller decision',
        'worker_replay':'the complete four-call sequence was independently exact, excluding worker math, source/destination pointer normalization, and iterate order as causes'},
      'fixture':{'width':7,'height':5,'padding_bytes_per_row':8,'key_rgb8':base.KEY,'background':'grayscale (x*17+y*23)&255'},
      'cases':rows,'claims_not_made':['arbitrary multivalue inputs','PF32','AE host/export color management']}
    REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    DOC.write_text('# OLMSmoother v1 multivalue ramp boundary\n\nVerdict: `'+report['verdict']+'`\n\nPF8 and PF16 are byte-exact in all twenty key/tolerance cells. PF16 retains the Windows scalar-SSE rounding points in `AlphaBlend16`. PF8 now follows the AEX scalar-SSE operation boundaries and its signed-luma truncation-toward-zero imports in `ColorCompare8`; this restores the missing caller executor callbacks without pixel-specific handling.\n')
    print(report['verdict'])
if __name__=='__main__': main()
