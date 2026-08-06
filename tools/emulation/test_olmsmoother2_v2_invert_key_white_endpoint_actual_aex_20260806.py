#!/usr/bin/env python3
"""Natural v2 invert-key white public endpoint, actual AEX to production."""
from __future__ import annotations
import hashlib, json, subprocess, tempfile
from pathlib import Path
import test_olmsmoother2_v2_key_threshold_actual_aex_20260805 as key
import test_olmsmoother2_v2_nonuniform_actual_aex_20260805 as v2
import test_olmsmoother2_typed_writeback_20260717 as typed

ROOT=Path(__file__).resolve().parents[2]
HARNESS=ROOT/'tools/emulation/olmsmoother2_v2_invert_key_white_endpoint_production_harness_20260806.cpp'
SOURCE=ROOT/'mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp'
REPORT=ROOT/'refs/conformance/olmsmoother2_v2_invert_key_white_endpoint_actual_aex_20260806.json'
DOC=ROOT/'refs/conformance/olmsmoother2_v2_invert_key_white_endpoint_actual_aex_20260806.md'
WHITE=(1.,1.,1.)

def require(value, message):
    if not value: raise RuntimeError('FAIL CLOSED: '+message)

def production():
    with tempfile.TemporaryDirectory(prefix='sm2_inv_white_') as directory:
        binary=Path(directory)/'harness'
        subprocess.run(['clang++','-std=c++17','-O2','-I',str(ROOT/'cli/OLMSmoother2/shim'),'-I',str(ROOT/'mac/OLMSmoother2/Mac'),str(HARNESS),'-o',str(binary)],check=True)
        output=subprocess.run([str(binary)],check=True,text=True,capture_output=True).stdout
    return dict(line.split() for line in output.splitlines())

def main():
    fixtures={
        'PF16': ([(1,1,1,1),(32767/32768,1,1,1),(32704/32768,1,1,1),(32703/32768,1,1,1),(0,0,0,1),(.75,.75,.75,1)],6),
        'PF32': ([(1,1,1,1),(.999,1,1,1),(.9981,1,1,1),(.997,1,1,1),(0,0,0,1),(.75,.75,.75,1)],12),
    }
    expected=production(); rows=[]
    for depth,(pixels,padding) in fixtures.items():
        pixels=[tuple(typed.f32(value) for value in pixel) for pixel in pixels]
        raw,plane,keyed,key_instructions,classifier_instructions,worker_instructions=key.actual(depth,pixels,padding,invert=True,key_rgb=WHITE)
        alpha=[pixel[3] for pixel in keyed]
        require(alpha==[1.,1.,1.,0.,0.,0.],depth+' invert-white ownership')
        require(raw.hex()==expected[depth],depth+' production mismatch')
        rows.append({'depth':depth,'raw_hex':raw.hex(),'class_plane_hex':plane.hex(),'post_key_alpha':alpha,'roles':['exact white match','inside near-white','inside threshold side','outside threshold side','far black','far gray'],'padding_per_row':padding,'padding_preserved':True,'palette_owner_instructions':key_instructions,'classifier_instructions':classifier_instructions,'worker_instructions':worker_instructions,'equal':True})
    report={'verdict':'PASS_V2_INVERT_WHITE_KEY_ENDPOINT_TO_PRODUCTION_EXACT','scope':'PF16/PF32 natural v2 invert Key Color white public RGB endpoint, exact/inside/outside/far cases, gamma off, Range1, padded3x2, LUTs','key_contract':{'rgb':WHITE,'public_color_endpoint':'255,255,255','invert_semantics':'retain alpha only for strict per-channel tolerance matches'},'aex_sha256':typed.AEX_SHA256,'decode_lut_sha256':hashlib.sha256(v2.DECODE).hexdigest(),'inverse_lut_sha256':hashlib.sha256(v2.ENCODE).hexdigest(),'fixtures':rows,'production_source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'claims_not_made':['No Gamma UI interaction','No multi-color key palette','No exact PF16 tolerance tie','No AE host runtime claim']}
    REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    DOC.write_text('# OLMSmoother2 v2 invert-white Key Color endpoint\n\nVerdict: `'+report['verdict']+'`\n\nThe public white Key Color endpoint now covers the invert owner for exact, inside, outside, and far pixels before the natural classifier/worker. PF16/PF32 actual-AEX paths and production are byte-exact with LUTs and padding fixed.\n\nGamma interaction, multi-color key palettes, an exact PF16 tolerance tie, and AE-host execution remain unclaimed.\n')
    print(json.dumps(report,indent=2,sort_keys=True)); return 0

if __name__=='__main__': raise SystemExit(main())
