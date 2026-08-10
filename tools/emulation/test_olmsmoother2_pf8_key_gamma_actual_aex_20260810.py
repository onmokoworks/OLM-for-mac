#!/usr/bin/env python3
"""PF8 v2 key/invert-key plus Gamma Colors: checked-in AEX versus production."""
from __future__ import annotations
import hashlib,json,subprocess,tempfile
from pathlib import Path
import test_olmsmoother2_typed_writeback_20260717 as typed
import test_olmsmoother2_v2_key_threshold_actual_aex_20260805 as key
import test_olmsmoother2_v2_nonuniform_actual_aex_20260805 as v2

ROOT=Path(__file__).resolve().parents[2]
HARNESS=ROOT/'tools/emulation/olmsmoother2_pf8_key_gamma_production_harness_20260810.cpp'
SOURCE=ROOT/'mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp'
REPORT=ROOT/'refs/conformance/olmsmoother2_pf8_key_gamma_actual_aex_20260810.json'
DOC=ROOT/'refs/conformance/olmsmoother2_pf8_key_gamma_actual_aex_20260810.md'
K=typed.f32(1/255); PALETTE=[(1.,0.,0.,1.),(K,K,K,1.)]
def require(ok,msg):
    if not ok: raise RuntimeError('FAIL CLOSED: '+msg)
def production():
    with tempfile.TemporaryDirectory(prefix='sm2_pf8_key_gamma_') as td:
        binary=Path(td)/'harness'
        subprocess.run(['clang++','-std=c++17','-O2','-I',str(ROOT/'cli/OLMSmoother2/shim'),'-I',str(ROOT/'mac/OLMSmoother2/Mac'),str(HARNESS),'-o',str(binary)],check=True)
        stdout=subprocess.run([str(binary)],check=True,text=True,capture_output=True).stdout
    return {label:bytes.fromhex(raw) for label,raw in (line.split() for line in stdout.splitlines())}
def main():
    pixels=[(K,K,K,1.),(1.,0.,0.,1.),(0.,K,K,1.),(0.,1.,0.,1.),(K,K,K,1.),tuple(typed.f32(x/255) for x in (96,191,64,255))]
    pixels=[tuple(typed.f32(value) for value in pixel) for pixel in pixels]
    prod=production(); fixtures=[]
    for label,invert in [('noninvert',False),('invert',True)]:
        raw,plane,keyed,ki,ci,wi=key.actual('PF8',pixels,5,invert=invert,gamma_palette=PALETTE,gamma_value=2.4)
        require(raw==prod[label],label+' PF8 raw mismatch')
        # PF8 code 0 versus key code 1 lands outside the AEX's strict threshold;
        # the exact key pixels (0/4) are the matching witnesses.
        expected=[0.,1.,1.,1.,0.,1.] if not invert else [1.,0.,0.,0.,1.,0.]
        require([pixel[3] for pixel in keyed]==expected,label+' post-key alpha roles')
        require(any(plane),label+' class plane zero')
        rowbytes=3*4+5
        for y in range(2): require(raw[y*rowbytes+12:(y+1)*rowbytes]==b'\xa5'*5,label+' padding')
        fixtures.append({'mode':label,'invert_key':invert,'post_key_alpha':expected,'class_plane_hex':plane.hex(),'class_nonzero_bytes':sum(x!=0 for x in plane),'raw_hex':raw.hex(),'padding_per_row':5,'padding_preserved':True,'key_owner_instructions':ki,'classifier_instructions':ci,'typed_worker_instructions':wi,'equal':True})
    report={'verdict':'PASS_PF8_V2_KEY_AND_INVERT_PLUS_GAMMA_COLORS_TO_PRODUCTION_EXACT','scope':'PF8 v2 non-invert and invert key followed by Gamma Colors ordered [red,key], gamma2.4, padded3x2, captured LUTs','interaction_contract':{'key_rgb':[K,K,K],'ordered_palette_rgba':PALETTE,'operation_order':'actual key owner mutates alpha before decode/classifier; Gamma Colors membership remains RGB-only','pf8_code0_vs_key_code1':'outside strict key-match threshold in both non-invert and invert paths'},'aex_sha256':typed.AEX_SHA256,'decode_lut_sha256':hashlib.sha256(v2.DECODE).hexdigest(),'inverse_lut_sha256':hashlib.sha256(v2.ENCODE).hexdigest(),'production_source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'fixtures':fixtures,'claims_not_made':['No other PF8 key color/palette/geometry','No PF16/PF32 claim from this fixture','No AE-host execution claim']}
    REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    DOC.write_text('# OLMSmoother2 PF8 key + Gamma Colors boundary\n\nVerdict: `'+report['verdict']+'`\n\nThe checked-in AEX and production are byte-exact for both non-invert and invert key ownership followed by ordered `[red, key]` Gamma Colors processing. Both paths naturally generate nonzero class planes, use the captured LUT pair, execute the PF8 typed worker, and preserve five padding bytes per row.\n\nThis evidence is limited to the declared 3x2 fixtures and does not claim other key colors, palettes, geometry, or AE-host execution.\n')
    print(report['verdict']); return 0
if __name__=='__main__': raise SystemExit(main())
