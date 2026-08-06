#!/usr/bin/env python3
"""Natural v2 nonuniform Smoothness=0 public lower endpoint."""
from __future__ import annotations
import hashlib,json,re,subprocess,tempfile
from pathlib import Path
import test_olmsmoother2_v2_nonuniform_actual_aex_20260805 as v2
import test_olmsmoother2_typed_writeback_20260717 as typed
ROOT=Path(__file__).resolve().parents[2];HARNESS=ROOT/'tools/emulation/olmsmoother2_v2_smoothness0_production_harness_20260805.cpp';SOURCE=ROOT/'mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp';REPORT=ROOT/'refs/conformance/olmsmoother2_v2_smoothness0_actual_aex_20260805.json';DOC=ROOT/'refs/conformance/olmsmoother2_v2_smoothness0_actual_aex_20260805.md'
def req(x,m):
 if not x:raise RuntimeError('FAIL CLOSED: '+m)
def production():
 with tempfile.TemporaryDirectory(prefix='sm2s0_') as td:
  b=Path(td)/'h';subprocess.run(['clang++','-std=c++17','-O2','-I',str(ROOT/'cli/OLMSmoother2/shim'),'-I',str(ROOT/'mac/OLMSmoother2/Mac'),str(HARNESS),'-o',str(b)],check=True);o=subprocess.run([str(b)],check=True,text=True,capture_output=True).stdout
 return dict(x.split() for x in o.splitlines())
def main():
 req(re.search(r'PF_ADD_SLIDER\(GetStringPtr\(StrID_Smoothness_Param_Name\),\s*0, 100, 0, 100, 100,',SOURCE.read_text()),'Smoothness public range drift');px=[(0,0,0,1),(0,1,1,1),(1,0,1,1),(1,1,0,1),(.25,.25,.25,1),(.75,.75,.75,1)];px=[tuple(typed.f32(v) for v in q) for q in px];prod=production();rows=[]
 for d,pad in [('PF16',6),('PF32',12)]:
  raw,plane,linear,ci,wi=v2.actual(d,px,pad,smoothness=0,smooth_range=1,require_class_nonzero=False);req(raw.hex()==prod[d],d+' mismatch');rows.append({'depth':d,'raw_hex':raw.hex(),'class_plane_hex':plane.hex(),'class_nonzero_bytes':sum(x!=0 for x in plane),'padding_per_row':pad,'padding_preserved':True,'classifier_instructions':ci,'worker_instructions':wi,'equal':True})
 req(rows[0]['class_plane_hex']==rows[1]['class_plane_hex'],'depth classifier divergence');report={'verdict':'PASS_V2_SMOOTHNESS_ZERO_LOWER_ENDPOINT_TO_PRODUCTION_EXACT','scope':'PF16/PF32 natural v2 nonuniform 3x2, Smoothness=0 lower endpoint, Smooth Range=1, key/gamma off, captured LUTs, padded rows','ae_parameter_contract':{'minimum':0,'maximum':100,'default':100,'tested':0},'aex_sha256':typed.AEX_SHA256,'decode_lut_sha256':hashlib.sha256(v2.DECODE).hexdigest(),'inverse_lut_sha256':hashlib.sha256(v2.ENCODE).hexdigest(),'fixtures':rows,'production_source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'claims_not_made':['No other Smoothness/Range combination','No key or Gamma UI interaction','No AE host runtime claim']};REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');DOC.write_text('# OLMSmoother2 v2 Smoothness 0 endpoint\n\nVerdict: `'+report['verdict']+'`\n\nThe public Smoothness lower endpoint `0` is exercised on a nonuniform 3x2 frame with Smooth Range 1. PF16/PF32 actual classifier/worker and production bytes agree exactly; classifier plane, captured LUTs, and row padding are fixed.\n\nOther Smoothness/Range combinations, key/gamma interaction, and AE-host execution are unclaimed.\n');print(json.dumps(report,indent=2,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
