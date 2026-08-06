#!/usr/bin/env python3
"""V2 Gamma Colors/internal-mode3 actual AEX versus production."""
from __future__ import annotations
import hashlib,json,subprocess,tempfile
from pathlib import Path
import test_olmsmoother2_v2_nonuniform_actual_aex_20260805 as v2
import test_olmsmoother2_typed_writeback_20260717 as typed
ROOT=Path(__file__).resolve().parents[2];HARNESS=ROOT/'tools/emulation/olmsmoother2_v2_gamma_colors_production_harness_20260805.cpp';SOURCE=ROOT/'mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp';REPORT=ROOT/'refs/conformance/olmsmoother2_v2_gamma_colors_actual_aex_20260805.json';DOC=ROOT/'refs/conformance/olmsmoother2_v2_gamma_colors_actual_aex_20260805.md'
def req(x,m):
 if not x:raise RuntimeError('FAIL CLOSED: '+m)
def production():
 with tempfile.TemporaryDirectory(prefix='sm2gcolors_') as td:
  b=Path(td)/'h';subprocess.run(['clang++','-std=c++17','-O2','-I',str(ROOT/'cli/OLMSmoother2/shim'),'-I',str(ROOT/'mac/OLMSmoother2/Mac'),str(HARNESS),'-o',str(b)],check=True);o=subprocess.run([str(b)],check=True,text=True,capture_output=True).stdout
 return dict(x.split() for x in o.splitlines())
def main():
 px=[(1,1,1,1),(0,0,0,1),(1,0,0,1),(.5,.5,.5,1),(0,1,1,1),(.875,.875,.875,1)];px=[tuple(typed.f32(v) for v in q) for q in px];prod=production();rows=[]
 for d,pad in [('PF16',6),('PF32',12)]:
  raw,plane,linear,ci,wi=v2.actual(d,px,pad,gamma_colors=True,gamma_value=2.4);req(raw.hex()==prod[d],d+' mismatch');rows.append({'depth':d,'raw_hex':raw.hex(),'class_plane_hex':plane.hex(),'padding_per_row':pad,'padding_preserved':True,'classifier_instructions':ci,'worker_instructions':wi,'equal':True})
 report={'verdict':'PASS_V2_GAMMA_COLORS_MODE3_NATURAL_AEX_TO_PRODUCTION_PADDED_3X2_EXACT','scope':'PF16/PF32 independent v2 Gamma Correction=Gamma Colors, one white palette color, gamma2.4, key disabled, padded3x2, captured LUTs','parameter_contract':{'ui_popup':2,'ui_name':'Gamma Colors','internal_bb10_mode_byte':3,'gamma_value_f32':typed.f32(2.4),'gamma_color_count':1,'gamma_color_rgba':[1,1,1,1],'v2_mode3_predicate':'FUN_18000a9c0 encodes candidates before RGB tolerance comparison'},'aex_sha256':typed.AEX_SHA256,'decode_lut_sha256':hashlib.sha256(v2.DECODE).hexdigest(),'inverse_lut_sha256':hashlib.sha256(v2.ENCODE).hexdigest(),'fixtures':rows,'production_source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'claims_not_made':['No multi-color gamma palette claim','No other gamma color/value/geometry','No key interaction','No AE host claim']};REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');DOC.write_text('# OLMSmoother2 v2 Gamma Colors mode3 boundary\n\nVerdict: `'+report['verdict']+'`\n\nUI popup 2 maps to internal bb10 mode 3. A single white Gamma Color exercises the v2 `FUN_18000a9c0` encoded-candidate predicate. PF16/PF32 natural classifier, typed bytes, LUT selection, and padding match production.\n\nMulti-color palettes, other gamma colors/values/geometry, key interaction, and AE host are unclaimed.\n');print(json.dumps(report,indent=2,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
