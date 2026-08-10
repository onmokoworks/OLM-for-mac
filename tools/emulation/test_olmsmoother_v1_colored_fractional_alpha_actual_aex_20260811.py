#!/usr/bin/env python3
"""Colored fractional-alpha EffectMain family for standalone Smoother v1."""
import hashlib,json,struct,tempfile
from pathlib import Path
import test_olmsmoother_v1_key_tolerance_geometry_actual_aex_20260810 as base

ROOT=Path(__file__).resolve().parents[2]
REPORT=ROOT/'refs/conformance/olmsmoother_v1_colored_fractional_alpha_actual_aex_20260811.json'
DOC=ROOT/'refs/conformance/olmsmoother_v1_colored_fractional_alpha_actual_aex_20260811.md'
TOLS=(0,6,127,255)

def fixture(depth):
    key={(0,0),(3,2),(6,4)}; alphas=(0,1,32,64,96,127,128,160,191,224,254,255)
    pixels=[]
    for y in range(base.H):
        for x in range(base.W):
            i=y*base.W+x; a=alphas[i%len(alphas)]
            # AE effect worlds normally carry premultiplied color.  Keep the
            # channels independently colored while constraining RGB <= alpha.
            p=(a,min((x*37+y*19+13)&255,a),min((x*11+y*53+201)&255,a),min((x*71+y*7+41)&255,a))
            pixels.append((255,*base.KEY) if (x,y) in key else p)
    size=4 if depth==8 else 8; rowbytes=base.W*size+8; raw=bytearray()
    for y in range(base.H):
        for p in pixels[y*base.W:(y+1)*base.W]:
            raw += bytes(p) if depth==8 else struct.pack('<4H',*(base.widen(v) for v in p))
        raw += bytes([0xb0+y])*8
    return bytes(raw),rowbytes

def main():
    temporary,lib=base.build_production(); rows=[]
    try:
        with tempfile.TemporaryDirectory(prefix='sm1-colored-alpha-') as td:
            codes={d:base.guest_code(Path(td),4 if d==8 else 8) for d in (8,16)}
        for depth in (8,16):
            payload,rowbytes=fixture(depth)
            for use_key in (0,1):
                for tolerance in TOLS:
                    actual,_=base.actual(depth,payload,rowbytes,use_key,tolerance,codes[depth])
                    production=base.production(lib,depth,payload,rowbytes,use_key,tolerance)
                    mismatch=sum(a!=b for a,b in zip(actual,production))
                    assert mismatch==0,(depth,use_key,tolerance,mismatch)
                    rows.append({'depth':depth,'use_key':use_key,'tolerance':tolerance,
                      'actual_sha256':hashlib.sha256(actual).hexdigest(),
                      'production_sha256':hashlib.sha256(production).hexdigest(),
                      'mismatched_bytes':mismatch})
    finally: temporary.cleanup()
    exact=sum(r['mismatched_bytes']==0 for r in rows)
    report={'schema_version':1,'status':'exact','verdict':'PASS_V1_COLORED_FRACTIONAL_ALPHA_16_CELLS_EXACT',
      'actual_aex_sha256':base.AEX_SHA,'scope':'actual exported PF_Cmd_RENDER vs production EffectMain; colored padded 7x5; alpha 0/1/32/64/96/127/128/160/191/224/254/255; key off/on; tolerance 0/6/127/255; PF8/PF16',
      'fixture':{'dimensions':[7,5],'padding_bytes_per_row':8,'key_rgb8':base.KEY,'key_islands':[[0,0],[3,2],[6,4]],'rgb':'independent affine R/G/B sequences clamped to alpha (premultiplied-valid)','alpha_codes':[0,1,32,64,96,127,128,160,191,224,254,255]},
      'summary':{'exact_cells':exact,'mismatching_cells':len(rows)-exact},
      'cases':rows,'claims_not_made':['arbitrary RGB/alpha inputs','PF32 native arithmetic','AE host/export color management']}
    REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    DOC.write_text('# OLMSmoother v1 colored fractional-alpha boundary\n\nVerdict: `'+report['verdict']+'`\n\nA premultiplied, non-grayscale padded 7×5 fixture crosses twelve alpha codes, effective Color Key off/on, four representative smoothing tolerances, and PF8/PF16. All sixteen exported Windows AEX versus production EffectMain cells are byte-exact after replacing the reconstructed PF16 classifier with its full actual-AEX CFG. This does not claim native PF32 behavior.\n')
    print(report['verdict'])
if __name__=='__main__':main()
