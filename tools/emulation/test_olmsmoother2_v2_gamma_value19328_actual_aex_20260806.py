#!/usr/bin/env python3
"""Natural Gamma Colors at the retained case-09 intermediate Gamma Value."""
from __future__ import annotations
import hashlib,json,re,subprocess,tempfile
from pathlib import Path
import test_olmsmoother2_v2_nonuniform_actual_aex_20260805 as v2
import test_olmsmoother2_typed_writeback_20260717 as typed
ROOT=Path(__file__).resolve().parents[2];HARNESS=ROOT/'tools/emulation/olmsmoother2_v2_gamma_value19328_production_harness_20260806.cpp';SOURCE=ROOT/'mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp';REPORT=ROOT/'refs/conformance/olmsmoother2_v2_gamma_value19328_actual_aex_20260806.json';DOC=ROOT/'refs/conformance/olmsmoother2_v2_gamma_value19328_actual_aex_20260806.md';PALETTE=[(1.,1.,1.,1.),(1.,0.,0.,1.)];GAMMA=typed.f32(1.93280005455017)
def req(x,m):
 if not x:raise RuntimeError('FAIL CLOSED: '+m)
def production():
 with tempfile.TemporaryDirectory(prefix='sm2g19328_') as td:
  b=Path(td)/'h';subprocess.run(['clang++','-std=c++17','-O2','-I',str(ROOT/'cli/OLMSmoother2/shim'),'-I',str(ROOT/'mac/OLMSmoother2/Mac'),str(HARNESS),'-o',str(b)],check=True);o=subprocess.run([str(b)],check=True,text=True,capture_output=True).stdout
 return dict(x.split() for x in o.splitlines())
def main():
 req(1.0<GAMMA<2.4,'intermediate Gamma Value escaped public range');req(re.search(r'PF_ADD_FLOAT_SLIDERX\([^;]*?1\.0, 2\.4, 1\.0, 2\.4, 2\.4,',SOURCE.read_text(),re.S),'Gamma Value AE range/default drift');px=[(1,1,1,1),(1,0,0,1),(0,0,1,1),(0,1,0,1),(.5,.75,.25,1),(.875,.125,.625,1)];px=[tuple(typed.f32(v) for v in q) for q in px];prod=production();rows=[]
 for d,pad in [('PF16',6),('PF32',12)]:
  raw,plane,linear,ci,wi=v2.actual(d,px,pad,gamma_colors=True,gamma_value=GAMMA,gamma_palette=PALETTE);req(raw.hex()==prod[d],d+' mismatch');rows.append({'depth':d,'raw_hex':raw.hex(),'class_plane_hex':plane.hex(),'padding_per_row':pad,'padding_preserved':True,'classifier_instructions':ci,'worker_instructions':wi,'equal':True})
 req(rows[0]['class_plane_hex']==rows[1]['class_plane_hex'],'depth classifier divergence');report={'verdict':'PASS_V2_GAMMA_COLORS_GAMMA_VALUE_1_9328_INTERMEDIATE_TO_PRODUCTION_EXACT','scope':'PF16/PF32 natural v2 Gamma Colors, Gamma Value=1.93280005455017 retained case-09 intermediate value, ordered [white,red], key off, padded3x2, captured LUTs','ae_parameter_contract':{'minimum':1.0,'maximum':2.4,'default':2.4,'tested_float32':GAMMA,'source':'retained Windows AE case final_random10_olm_smoother_v2_09 parameter readback'},'palette_contract':{'ordered_rgba':PALETTE,'matched_pixels':[0,1],'nonmatching_pixels':[2,3,4,5]},'aex_sha256':typed.AEX_SHA256,'decode_lut_sha256':hashlib.sha256(v2.DECODE).hexdigest(),'inverse_lut_sha256':hashlib.sha256(v2.ENCODE).hexdigest(),'fixtures':rows,'production_source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'claims_not_made':['No other intermediate Gamma Value','No key interaction','No other palette/geometry','No AE host runtime claim']};REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');DOC.write_text('# OLMSmoother2 v2 Gamma Value 1.9328 intermediate boundary\n\nVerdict: `'+report['verdict']+'`\n\nThe retained case-09 Gamma Value `1.93280005455017` closes one meaningful intermediate point between the already proven 1.0 and 2.4 endpoints. In Gamma Colors mode with ordered `[white, red]`, PF16/PF32 actual-AEX classifier/worker output, production bytes, LUTs, and row padding are exact.\n\nOther intermediate values, key interaction, other palettes/geometries, and AE-host execution remain unclaimed.\n');print(json.dumps(report,indent=2,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
