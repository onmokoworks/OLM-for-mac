#!/usr/bin/env python3
"""V2 invert-key palette owner through natural classifier and typed output."""
from __future__ import annotations
import hashlib,json,struct,subprocess,tempfile
from pathlib import Path
import test_olmsmoother2_v2_key_threshold_actual_aex_20260805 as base
import test_olmsmoother2_typed_writeback_20260717 as typed
ROOT=Path(__file__).resolve().parents[2];HARNESS=ROOT/'tools/emulation/olmsmoother2_v2_invert_key_production_harness_20260805.cpp';SOURCE=ROOT/'mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp';REPORT=ROOT/'refs/conformance/olmsmoother2_v2_invert_key_actual_aex_20260805.json';DOC=ROOT/'refs/conformance/olmsmoother2_v2_invert_key_actual_aex_20260805.md'
def req(x,m):
 if not x:raise RuntimeError('FAIL CLOSED: '+m)
def f(u):return struct.unpack('<f',struct.pack('<I',u))[0]
def production():
 with tempfile.TemporaryDirectory(prefix='sm2invert_') as td:
  b=Path(td)/'h';subprocess.run(['clang++','-std=c++17','-O2','-I',str(ROOT/'cli/OLMSmoother2/shim'),'-I',str(ROOT/'mac/OLMSmoother2/Mac'),str(HARNESS),'-o',str(b)],check=True);o=subprocess.run([str(b)],check=True,text=True,capture_output=True).stdout
 return dict(x.split() for x in o.splitlines())
def main():
 k=typed.f32(1/255);pf16=[(64/32768,128/32768,128/32768,1),(128/32768,128/32768,128/32768,1),(65/32768,128/32768,128/32768,1),(.75,.75,.75,1),(0,1,1,1),(1,0,0,1)];pf32=[(f(0x3b008080),k,k,1),(k,k,k,1),(f(0x3b008082),k,k,1),(f(0x3b008081),k,k,1),(.75,.75,.75,1),(0,1,1,1)];prod=production();rows=[]
 for d,pix,pad in [('PF16',pf16,6),('PF32',pf32,12)]:
  pix=[tuple(typed.f32(v) for v in q) for q in pix];raw,plane,keyed,ki,ci,wi=base.actual(d,pix,pad,invert=True);req(raw.hex()==prod[d],d+' mismatch');rows.append({'depth':d,'raw_hex':raw.hex(),'class_plane_hex':plane.hex(),'post_key_alpha':[x[3] for x in keyed],'threshold_relation':['outside','exact-key','inside','far','far','far'] if d=='PF16' else ['outside','exact-key','inside','tie','far','far'],'padding_per_row':pad,'padding_preserved':True,'palette_owner_instructions':ki,'classifier_instructions':ci,'worker_instructions':wi,'equal':True})
 req(rows[0]['post_key_alpha'][:3]==[0.,1.,1.],'PF16 invert ownership');req(rows[1]['post_key_alpha'][:4]==[0.,1.,1.,0.],'PF32 invert/tie ownership');report={'verdict':'PASS_V2_INVERT_KEY_PALETTE_NATURAL_AEX_TO_PRODUCTION_PADDED_3X2_EXACT','scope':'PF16/PF32 independent v2 invert key, key RGB=1/255, threshold sides; PF32 exact tie; gamma UI none, LUTs, padded 3x2','aex_sha256':typed.AEX_SHA256,'palette_owner':'0x180002930','threshold_bits':'0x3b008081','pf16_exact_tie_representable':False,'fixtures':rows,'production_source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'claims_not_made':['No multi-color palette claim','No Gamma UI mode claim','No other key color/geometry','No AE host claim']};REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');DOC.write_text('# OLMSmoother2 v2 Invert Key boundary\n\nVerdict: `'+report['verdict']+'`\n\nActual AEX `FUN_180002930` keeps alpha only for palette matches. PF32 inside remains alpha 1 while exact tie/outside become alpha 0; PF16 adjacent codes bracket the unrepresentable tie. Natural classifier, typed worker, production bytes, LUTs, and padding agree.\n\nMulti-color palettes, Gamma UI modes, other geometry, and AE host are unclaimed.\n');print(json.dumps(report,indent=2,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
