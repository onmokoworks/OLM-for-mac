#!/usr/bin/env python3
"""Natural v2 non-invert white Key Color public endpoint."""
from __future__ import annotations
import hashlib,json,subprocess,tempfile
from pathlib import Path
import test_olmsmoother2_v2_key_threshold_actual_aex_20260805 as key
import test_olmsmoother2_v2_nonuniform_actual_aex_20260805 as v2
import test_olmsmoother2_typed_writeback_20260717 as typed
ROOT=Path(__file__).resolve().parents[2];HARNESS=ROOT/'tools/emulation/olmsmoother2_v2_key_white_endpoint_production_harness_20260805.cpp';SOURCE=ROOT/'mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp';REPORT=ROOT/'refs/conformance/olmsmoother2_v2_key_white_endpoint_actual_aex_20260805.json';DOC=ROOT/'refs/conformance/olmsmoother2_v2_key_white_endpoint_actual_aex_20260805.md';WHITE=(1.,1.,1.)
def req(x,m):
 if not x:raise RuntimeError('FAIL CLOSED: '+m)
def production():
 with tempfile.TemporaryDirectory(prefix='sm2kw_') as td:
  b=Path(td)/'h';subprocess.run(['clang++','-std=c++17','-O2','-I',str(ROOT/'cli/OLMSmoother2/shim'),'-I',str(ROOT/'mac/OLMSmoother2/Mac'),str(HARNESS),'-o',str(b)],check=True);o=subprocess.run([str(b)],check=True,text=True,capture_output=True).stdout
 return dict(x.split() for x in o.splitlines())
def main():
 pf16=[(1,1,1,1),(32767/32768,1,1,1),(32704/32768,1,1,1),(32703/32768,1,1,1),(0,0,0,1),(.75,.75,.75,1)];pf32=[(1,1,1,1),(.999,1,1,1),(.9981,1,1,1),(.997,1,1,1),(0,0,0,1),(.75,.75,.75,1)];prod=production();rows=[]
 for d,pix,pad in [('PF16',pf16,6),('PF32',pf32,12)]:
  pix=[tuple(typed.f32(v) for v in q) for q in pix];raw,plane,keyed,ki,ci,wi=key.actual(d,pix,pad,key_rgb=WHITE);req(raw.hex()==prod[d],d+' mismatch');alpha=[x[3] for x in keyed];req(alpha[:2]==[0.,0.] and alpha[3:]==[1.,1.,1.],d+' key endpoint roles');rows.append({'depth':d,'raw_hex':raw.hex(),'class_plane_hex':plane.hex(),'post_key_alpha':alpha,'roles':['exact white match','inside near-white','inside threshold side','outside threshold side','far black','far gray'],'padding_per_row':pad,'padding_preserved':True,'key_owner_instructions':ki,'classifier_instructions':ci,'worker_instructions':wi,'equal':True})
 report={'verdict':'PASS_V2_NONINVERT_WHITE_KEY_ENDPOINT_TO_PRODUCTION_EXACT','scope':'PF16/PF32 natural v2 non-invert Key Color white public RGB endpoint, exact/inside/outside/far cases, gamma off, Range1, padded3x2, LUTs','key_contract':{'rgb':WHITE,'public_color_endpoint':'255,255,255','comparison':'strict per-channel abs(delta)<0x3b008081'},'aex_sha256':typed.AEX_SHA256,'decode_lut_sha256':hashlib.sha256(v2.DECODE).hexdigest(),'inverse_lut_sha256':hashlib.sha256(v2.ENCODE).hexdigest(),'fixtures':rows,'production_source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'claims_not_made':['No invert-white-key claim','No gamma interaction','No exact PF16 tolerance tie','No AE host runtime claim']};REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');DOC.write_text('# OLMSmoother2 v2 white Key Color endpoint\n\nVerdict: `'+report['verdict']+'`\n\nThe public white Key Color endpoint exercises exact, inside, outside, and far non-invert key cases before the natural classifier/worker. PF16/PF32 actual paths and production are byte-exact with LUTs and padding fixed.\n\nInvert-white interaction, PF16 exact tolerance tie, and AE-host execution are unclaimed.\n');print(json.dumps(report,indent=2,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
