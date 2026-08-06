#!/usr/bin/env python3
"""V2 invert-key plus Gamma Colors ordered-palette interaction."""
from __future__ import annotations
import hashlib,json,subprocess,tempfile
from pathlib import Path
import test_olmsmoother2_v2_key_threshold_actual_aex_20260805 as key
import test_olmsmoother2_v2_nonuniform_actual_aex_20260805 as v2
import test_olmsmoother2_typed_writeback_20260717 as typed
ROOT=Path(__file__).resolve().parents[2];HARNESS=ROOT/'tools/emulation/olmsmoother2_v2_invert_key_gamma_colors_production_harness_20260805.cpp';SOURCE=ROOT/'mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp';REPORT=ROOT/'refs/conformance/olmsmoother2_v2_invert_key_gamma_colors_actual_aex_20260805.json';DOC=ROOT/'refs/conformance/olmsmoother2_v2_invert_key_gamma_colors_actual_aex_20260805.md';K=typed.f32(1/255);PALETTE=[(1.,0.,0.,1.),(K,K,K,1.)]
def req(x,m):
 if not x:raise RuntimeError('FAIL CLOSED: '+m)
def production():
 with tempfile.TemporaryDirectory(prefix='sm2ikg_') as td:
  b=Path(td)/'h';subprocess.run(['clang++','-std=c++17','-O2','-I',str(ROOT/'cli/OLMSmoother2/shim'),'-I',str(ROOT/'mac/OLMSmoother2/Mac'),str(HARNESS),'-o',str(b)],check=True);o=subprocess.run([str(b)],check=True,text=True,capture_output=True).stdout
 return dict(x.split() for x in o.splitlines())
def main():
 pf16=[(128/32768,128/32768,128/32768,1),(1,0,0,1),(65/32768,128/32768,128/32768,1),(0,1,0,1),(128/32768,128/32768,128/32768,1),(.375,.75,.25,1)];pf32=[(K,K,K,1),(1,0,0,1),(.002,K,K,1),(0,1,0,1),(K,K,K,1),(.375,.75,.25,1)];prod=production();rows=[]
 for d,pix,pad in [('PF16',pf16,6),('PF32',pf32,12)]:
  pix=[tuple(typed.f32(v) for v in q) for q in pix];raw,plane,keyed,ki,ci,wi=key.actual(d,pix,pad,invert=True,gamma_palette=PALETTE,gamma_value=2.4);req(raw.hex()==prod[d],d+' mismatch');req(keyed[0][3]==1. and keyed[4][3]==1. and keyed[1][3]==0. and keyed[3][3]==0.,d+' invert roles');rows.append({'depth':d,'raw_hex':raw.hex(),'class_plane_hex':plane.hex(),'post_key_rgba_f32':[list(x) for x in keyed],'roles':{'pixels0_4':'key palette match; alpha retained; Gamma Colors index1','pixel1':'invert-key clears alpha; Gamma Colors index0 red still matches by RGB','pixel2':'near-key inside; alpha retained','pixels3_5':'invert-key clears alpha; non-palette controls'},'padding_per_row':pad,'padding_preserved':True,'palette_owner_instructions':ki,'classifier_instructions':ci,'worker_instructions':wi,'equal':True})
 report={'verdict':'PASS_V2_INVERT_KEY_PLUS_GAMMA_COLORS_TO_PRODUCTION_EXACT','scope':'PF16/PF32 v2 invert-key then Gamma Colors ordered [red,key], gamma2.4, padded3x2, captured LUTs','interaction_contract':{'operation_order':'actual invert-key palette owner retains alpha only for key matches before decode/classifier; Gamma Colors subsequently compares RGB independent of alpha','key_rgb':[K,K,K],'ordered_palette_rgba':PALETTE,'invert_key':True,'membership_witness':'red has alpha cleared by invert-key yet remains Gamma Colors index0 RGB match; key retains alpha and matches index1'},'aex_sha256':typed.AEX_SHA256,'decode_lut_sha256':hashlib.sha256(v2.DECODE).hexdigest(),'inverse_lut_sha256':hashlib.sha256(v2.ENCODE).hexdigest(),'fixtures':rows,'production_source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'claims_not_made':['No other palette/key/geometry','No AE host claim']};REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');DOC.write_text('# OLMSmoother2 v2 invert-key + Gamma Colors interaction\n\nVerdict: `'+report['verdict']+'`\n\nThe actual invert-key palette owner retains alpha only for key matches before decode/classification. Gamma Colors then compares RGB independently: red has alpha cleared but still matches ordered palette index 0, while key RGB retains alpha and matches index 1. PF16/PF32 owner/classifier/worker and production are byte-exact with LUTs and padding fixed.\n\nOther palettes/geometries and AE host remain unclaimed.\n');print(json.dumps(report,indent=2,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
