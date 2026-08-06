#!/usr/bin/env python3
"""V2 Gamma All Colors natural AEX path versus production."""
from __future__ import annotations
import hashlib,json,subprocess,tempfile
from pathlib import Path
import test_olmsmoother2_v2_nonuniform_actual_aex_20260805 as v2
import test_olmsmoother2_typed_writeback_20260717 as typed
ROOT=Path(__file__).resolve().parents[2];HARNESS=ROOT/'tools/emulation/olmsmoother2_v2_gamma_all_production_harness_20260805.cpp';SOURCE=ROOT/'mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp';REPORT=ROOT/'refs/conformance/olmsmoother2_v2_gamma_all_actual_aex_20260805.json';DOC=ROOT/'refs/conformance/olmsmoother2_v2_gamma_all_actual_aex_20260805.md'
def req(x,m):
 if not x:raise RuntimeError('FAIL CLOSED: '+m)
def production():
 with tempfile.TemporaryDirectory(prefix='sm2gamma_') as td:
  b=Path(td)/'h';subprocess.run(['clang++','-std=c++17','-O2','-I',str(ROOT/'cli/OLMSmoother2/shim'),'-I',str(ROOT/'mac/OLMSmoother2/Mac'),str(HARNESS),'-o',str(b)],check=True);o=subprocess.run([str(b)],check=True,text=True,capture_output=True).stdout
 return dict(x.split() for x in o.splitlines())
def main():
 px=[(.25,.5,.75,1),(.75,.25,.5,1),(.5,.75,.25,1),(.125,.875,.375,1),(.875,.375,.125,1),(.375,.125,.875,1)];px=[tuple(typed.f32(v) for v in q) for q in px];prod=production();rows=[]
 for d,pad in [('PF16',6),('PF32',12)]:
  raw,plane,linear,ci,wi=v2.actual(d,px,pad,gamma_all=True,gamma_value=2.4);req(raw.hex()==prod[d],d+' mismatch');rows.append({'depth':d,'raw_hex':raw.hex(),'class_plane_hex':plane.hex(),'padding_per_row':pad,'padding_preserved':True,'classifier_instructions':ci,'worker_instructions':wi,'equal':True})
 report={'verdict':'PASS_V2_GAMMA_ALL_NATURAL_AEX_TO_PRODUCTION_PADDED_3X2_EXACT','scope':'PF16/PF32 independent v2 Gamma Correction=All Colors, gamma2.4, key disabled, nonuniform padded3x2, captured LUTs, no host','parameter_contract':{'ui_popup':3,'ui_name':'All Colors','internal_bb10_mode_byte':1,'gamma_value_f32':typed.f32(2.4),'frame_decode_lut_selected_by':'version != v1, independent of Gamma UI','typed_inverse_lut_selected_by':'internal version flag 0 and transfer context length/pointer'},'aex_sha256':typed.AEX_SHA256,'decode_lut_sha256':hashlib.sha256(v2.DECODE).hexdigest(),'inverse_lut_sha256':hashlib.sha256(v2.ENCODE).hexdigest(),'fixtures':rows,'production_source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'claims_not_made':['No Gamma Colors mode claim','No other gamma value/geometry','No key interaction','No AE host claim']};REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');DOC.write_text('# OLMSmoother2 v2 Gamma All Colors boundary\n\nVerdict: `'+report['verdict']+'`\n\nUI popup 3 maps to actual bb10 mode byte 1. Frame decode remains selected by v2 independently of the Gamma UI, and typed output uses the captured inverse LUT context. PF16/PF32 raw output and padding match production.\n\nGamma Colors, other gamma values/geometry, key interaction, and AE host are unclaimed.\n');print(json.dumps(report,indent=2,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
