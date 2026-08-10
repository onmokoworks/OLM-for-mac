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
    pf16=[r for r in rows if r['depth']==16]; pf8=[r for r in rows if r['depth']==8]
    assert all(r['mismatched_bytes']==0 for r in pf16)
    residual=[r for r in pf8 if r['mismatched_bytes']]
    assert [(r['use_key'],r['tolerance'],r['mismatched_bytes']) for r in residual]==[(0,6,9),(1,6,9)]
    report={'schema_version':1,'status':'bounded','verdict':'PASS_PF16_MULTIVALUE_RAMP_FMA_EXACT_PF8_RESIDUAL_RECORDED',
      'actual_aex_sha256':base.AEX_SHA,
      'scope':'padded nonuniform 7x5 multivalue grayscale ramp with five exact-key islands; Use Key off/on x tolerance 0/1/6/127/255 x PF8/PF16',
      'pf16_closed_boundary':'all 10 exported PF_Cmd_RENDER versus production EffectMain cells are byte exact after preserving Windows MULSS/MULSS/ADDSS binary32 rounding in AlphaBlend16',
      'pf8_open_boundary':'tolerance 6 differs by nine RGB bytes in each key state; all other eight PF8 cells are exact; no PF8 production change is claimed by this report',
      'fixture':{'width':7,'height':5,'padding_bytes_per_row':8,'key_rgb8':base.KEY,'background':'grayscale (x*17+y*23)&255'},
      'cases':rows,'claims_not_made':['PF8 tolerance-6 ramp exactness','arbitrary multivalue inputs','PF32','AE host/export color management']}
    REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    DOC.write_text('# OLMSmoother v1 multivalue ramp boundary\n\nVerdict: `'+report['verdict']+'`\n\nPF16 is byte-exact in all ten key/tolerance cells after retaining the Windows scalar-SSE rounding points in `AlphaBlend16`. PF8 remains explicitly open at tolerance 6: both key states differ by nine RGB bytes; the other eight PF8 cells are exact. No PF8 workaround is admitted.\n')
    print(report['verdict'])
if __name__=='__main__': main()
