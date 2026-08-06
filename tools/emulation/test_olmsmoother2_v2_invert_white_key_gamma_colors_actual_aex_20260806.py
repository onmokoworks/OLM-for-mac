#!/usr/bin/env python3
"""V2 invert-white key plus Gamma Colors owner/classifier/typed interaction."""
from __future__ import annotations
import hashlib,json,subprocess,tempfile
from pathlib import Path
import test_olmsmoother2_v2_key_threshold_actual_aex_20260805 as key
import test_olmsmoother2_v2_nonuniform_actual_aex_20260805 as v2
import test_olmsmoother2_typed_writeback_20260717 as typed

ROOT=Path(__file__).resolve().parents[2]
HARNESS=ROOT/'tools/emulation/olmsmoother2_v2_invert_white_key_gamma_colors_production_harness_20260806.cpp'
SOURCE=ROOT/'mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp'
REPORT=ROOT/'refs/conformance/olmsmoother2_v2_invert_white_key_gamma_colors_actual_aex_20260806.json'
DOC=ROOT/'refs/conformance/olmsmoother2_v2_invert_white_key_gamma_colors_actual_aex_20260806.md'
WHITE=(1.,1.,1.); PALETTE=[(1.,0.,0.,1.),(1.,1.,1.,1.)]

def require(value,message):
    if not value: raise RuntimeError('FAIL CLOSED: '+message)

def production():
    with tempfile.TemporaryDirectory(prefix='sm2_iwkg_') as directory:
        binary=Path(directory)/'harness'
        subprocess.run(['clang++','-std=c++17','-O2','-I',str(ROOT/'cli/OLMSmoother2/shim'),'-I',str(ROOT/'mac/OLMSmoother2/Mac'),str(HARNESS),'-o',str(binary)],check=True)
        output=subprocess.run([str(binary)],check=True,text=True,capture_output=True).stdout
    return dict(line.split() for line in output.splitlines())

def main():
    fixtures={
        'PF16': ([(1,1,1,1),(1,0,0,1),(32704/32768,1,1,1),(0,1,0,1),(1,1,1,1),(.75,.75,.75,1)],6),
        'PF32': ([(1,1,1,1),(1,0,0,1),(.9981,1,1,1),(0,1,0,1),(1,1,1,1),(.75,.75,.75,1)],12),
    }
    expected=production(); rows=[]
    for depth,(pixels,padding) in fixtures.items():
        pixels=[tuple(typed.f32(value) for value in pixel) for pixel in pixels]
        raw,plane,keyed,key_instructions,classifier_instructions,worker_instructions=key.actual(depth,pixels,padding,invert=True,gamma_palette=PALETTE,gamma_value=2.4,key_rgb=WHITE)
        alpha=[pixel[3] for pixel in keyed]
        require(alpha==[1.,0.,1.,0.,1.,0.],depth+' invert-white alpha ownership')
        require(raw.hex()==expected[depth],depth+' production mismatch')
        rows.append({'depth':depth,'raw_hex':raw.hex(),'class_plane_hex':plane.hex(),'post_key_rgba_f32':[list(pixel) for pixel in keyed],'post_key_alpha':alpha,'roles':{'pixels0_4':'exact white key matches retain alpha and Gamma Colors index1','pixel1':'invert-key clears alpha but red remains Gamma Colors index0 RGB match','pixel2':'inside near-white retains alpha','pixels3_5':'non-key controls clear alpha; not in Gamma palette'},'padding_per_row':padding,'padding_preserved':True,'palette_owner_instructions':key_instructions,'classifier_instructions':classifier_instructions,'worker_instructions':worker_instructions,'equal':True})
    report={'verdict':'PASS_V2_INVERT_WHITE_KEY_PLUS_GAMMA_COLORS_TO_PRODUCTION_EXACT','scope':'PF16/PF32 v2 invert white key then Gamma Colors ordered [red,white], gamma2.4, padded3x2, captured LUTs','interaction_contract':{'operation_order':'actual invert-key owner retains alpha for white-key tolerance matches before decode/classifier; Gamma Colors then compares RGB independently of alpha','key_rgb':WHITE,'ordered_palette_rgba':PALETTE,'membership_witness':'red loses alpha but remains Gamma Colors index0; exact white retains alpha and matches index1'},'aex_sha256':typed.AEX_SHA256,'decode_lut_sha256':hashlib.sha256(v2.DECODE).hexdigest(),'inverse_lut_sha256':hashlib.sha256(v2.ENCODE).hexdigest(),'fixtures':rows,'production_source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'claims_not_made':['No other key or palette endpoints','No intermediate Gamma Value','No other geometry','No AE host claim']}
    REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    DOC.write_text('# OLMSmoother2 v2 invert-white key + Gamma Colors interaction\n\nVerdict: `'+report['verdict']+'`\n\nThe actual invert-key owner retains alpha for white-key tolerance matches before decode/classification. Gamma Colors then compares RGB independently: red loses alpha but remains palette index 0, while exact white retains alpha and matches index 1. PF16/PF32 owner, classifier, typed worker, production bytes, LUTs, and padding are exact.\n\nOther key/palette endpoints, intermediate Gamma values, other geometry, and AE-host execution remain unclaimed.\n')
    print(json.dumps(report,indent=2,sort_keys=True)); return 0

if __name__=='__main__': raise SystemExit(main())
