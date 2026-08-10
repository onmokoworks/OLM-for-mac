#!/usr/bin/env python3
"""PF8 v2 Gamma All: natural checked-in AEX chain versus production."""
from __future__ import annotations
import hashlib,json,subprocess,tempfile
from pathlib import Path
import test_olmsmoother2_typed_writeback_20260717 as typed
import test_olmsmoother2_v2_nonuniform_actual_aex_20260805 as v2

ROOT=Path(__file__).resolve().parents[2]
HARNESS=ROOT/'tools/emulation/olmsmoother2_pf8_gamma_all_production_harness_20260810.cpp'
SOURCE=ROOT/'mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp'
REPORT=ROOT/'refs/conformance/olmsmoother2_pf8_gamma_all_actual_aex_20260810.json'
DOC=ROOT/'refs/conformance/olmsmoother2_pf8_gamma_all_actual_aex_20260810.md'
def require(ok,msg):
    if not ok: raise RuntimeError('FAIL CLOSED: '+msg)
def production():
    with tempfile.TemporaryDirectory(prefix='sm2_pf8_gamma_all_') as td:
        binary=Path(td)/'harness'
        subprocess.run(['clang++','-std=c++17','-O2','-I',str(ROOT/'cli/OLMSmoother2/shim'),'-I',str(ROOT/'mac/OLMSmoother2/Mac'),str(HARNESS),'-o',str(binary)],check=True)
        raw=subprocess.run([str(binary)],check=True,text=True,capture_output=True).stdout.strip()
    return bytes.fromhex(raw)
def main():
    codes=[(64,128,191),(191,64,128),(128,191,64),(32,223,96),(223,96,32),(96,32,223)]
    encoded=[tuple(typed.f32(value/255) for value in (*rgb,255)) for rgb in codes]
    actual,plane,linear,ci,wi=v2.actual('PF8',encoded,5,gamma_all=True,gamma_value=2.4)
    candidate=production()
    require(actual==candidate,f'PF8 Gamma All raw mismatch: actual={actual.hex()} production={candidate.hex()}')
    require(any(plane),'natural classifier plane stayed zero')
    rowbytes=3*4+5
    for y in range(2): require(actual[y*rowbytes+12:(y+1)*rowbytes]==b'\xa5'*5,f'padding row {y} changed')
    report={'verdict':'PASS_PF8_V2_GAMMA_ALL_NATURAL_AEX_TO_PRODUCTION_EXACT','scope':'PF8 v2, key off, Gamma Correction=All Colors, gamma2.4, smoothness100/range1/extra0, padded nonuniform 3x2','parameter_contract':{'ui_popup':3,'ui_name':'All Colors','internal_bb10_mode_byte':1,'gamma_value_f32':typed.f32(2.4),'encoded_pf8_rgb_codes':[list(x) for x in codes]},'aex_sha256':typed.AEX_SHA256,'decode_lut_sha256':hashlib.sha256(v2.DECODE).hexdigest(),'inverse_lut_sha256':hashlib.sha256(v2.ENCODE).hexdigest(),'production_source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'fixture':{'geometry':[3,2],'padding_per_row':5,'padding_preserved':True,'class_plane_hex':plane.hex(),'class_nonzero_bytes':sum(x!=0 for x in plane),'decoded_input_rgba_f32':[list(x) for x in linear],'raw_hex':actual.hex(),'classifier_instructions':ci,'typed_worker_instructions':wi,'equal':True},'claims_not_made':['No other PF8 gamma value/geometry/smoothing combination','No key interaction','No PF16/PF32 claim from this fixture','No AE-host execution claim']}
    REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    DOC.write_text('# OLMSmoother2 PF8 Gamma All Colors boundary\n\nVerdict: `'+report['verdict']+'`\n\nFor the declared padded 3x2 fixture, the checked-in AEX naturally generates a nonzero class plane, executes its PF8 worker with the captured decode/inverse LUT contract, and matches production `RenderBits<PF_Pixel8>` byte-for-byte. Five padding bytes per row remain unchanged.\n\nThis does not claim other gamma values, geometry, smoothing combinations, key interaction, or AE-host execution.\n')
    print(report['verdict']); return 0
if __name__=='__main__': raise SystemExit(main())
