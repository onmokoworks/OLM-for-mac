#!/usr/bin/env python3
"""V2 Gamma Colors ordered-palette tolerance boundary."""
from __future__ import annotations
import hashlib,json,struct,subprocess,tempfile
from pathlib import Path
import test_olmsmoother2_v2_nonuniform_actual_aex_20260805 as v2
import test_olmsmoother2_typed_writeback_20260717 as typed
import test_olmsmoother2_v2_gamma_palette_duplicate_actual_aex_20260805 as dup
ROOT=Path(__file__).resolve().parents[2];HARNESS=ROOT/'tools/emulation/olmsmoother2_v2_gamma_palette_tolerance_production_harness_20260805.cpp';SOURCE=ROOT/'mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp';REPORT=ROOT/'refs/conformance/olmsmoother2_v2_gamma_palette_tolerance_actual_aex_20260805.json';DOC=ROOT/'refs/conformance/olmsmoother2_v2_gamma_palette_tolerance_actual_aex_20260805.md';PALETTE=[(1.,0.,0.,1.),(0.,0.,0.,1.)];BITS=[0x3b008080,0x3b008081,0x3b008082]
def req(x,m):
 if not x:raise RuntimeError('FAIL CLOSED: '+m)
def f(u):return struct.unpack('<f',struct.pack('<I',u))[0]
def production():
 with tempfile.TemporaryDirectory(prefix='sm2gtol_') as td:
  b=Path(td)/'h';subprocess.run(['clang++','-std=c++17','-O2','-I',str(ROOT/'cli/OLMSmoother2/shim'),'-I',str(ROOT/'mac/OLMSmoother2/Mac'),str(HARNESS),'-o',str(b)],check=True);o=subprocess.run([str(b)],check=True,text=True,capture_output=True).stdout
 return dict(x.split() for x in o.splitlines())
def probe():
 l=typed.AexLoader(str(typed.AEX_PATH),verbose=False,fast=False);l.register_libm_impls(max_threads=1);owner,pb=dup.make_owner(l,PALETTE);l.write_bytes(owner+8,struct.pack('<I',1));rows=[]
 for role,u,want in [('below',BITS[0],True),('tie',BITS[1],False),('above',BITS[2],False)]:
  got=dup.call(l,owner,(f(u),0.,0.,1.));req(got['match']==want,role+' predicate');rows.append({'role':role,'candidate_r_bits':f'0x{u:08x}','candidate_r':f(u),'match':got['match'],'instructions':got['instructions']})
 return {'ordered_memory_hex':pb.hex(),'version_flag':1,'transfer':'disabled only for direct comparator isolation','rows':rows}
def main():
 pf16=[(64/32768,0,0,1),(65/32768,0,0,1),(0,0,0,1),(1,0,0,1),(0,1,0,1),(.375,.75,.25,1)];pf32=[(f(BITS[0]),0,0,1),(f(BITS[1]),0,0,1),(f(BITS[2]),0,0,1),(1,0,0,1),(0,1,0,1),(.375,.75,.25,1)];prod=production();rows=[]
 for d,pix,pad in [('PF16',pf16,6),('PF32',pf32,12)]:
  pix=[tuple(typed.f32(v) for v in q) for q in pix];raw,plane,linear,ci,wi=v2.actual(d,pix,pad,gamma_colors=True,gamma_value=2.4,gamma_palette=PALETTE);req(raw.hex()==prod[d],d+' mismatch');rows.append({'depth':d,'raw_hex':raw.hex(),'class_plane_hex':plane.hex(),'padding_per_row':pad,'padding_preserved':True,'classifier_instructions':ci,'worker_instructions':wi,'equal':True})
 p=probe();report={'verdict':'PASS_V2_GAMMA_COLORS_TOLERANCE_ORDERED_PALETTE_TO_PRODUCTION_EXACT','scope':'PF16/PF32 independent v2 Gamma Colors ordered [red,black], gamma2.4, key off, padded3x2, LUTs; direct actual comparator below/tie/above','threshold':{'f32_bits':'0x3b008081','comparison':'strict abs(delta) < threshold','direct_actual_owner':p,'pf16_note':'exact tie is not representable; codes 64/65 bracket it'},'palette_contract':{'ordered_rgba':PALETTE,'boundary_target_index':1},'aex_sha256':typed.AEX_SHA256,'decode_lut_sha256':hashlib.sha256(v2.DECODE).hexdigest(),'inverse_lut_sha256':hashlib.sha256(v2.ENCODE).hexdigest(),'fixtures':rows,'production_source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'claims_not_made':['No PF16 exact tie representation','No key interaction','No other palette/geometry','No AE host claim']};REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');DOC.write_text('# OLMSmoother2 v2 Gamma Colors tolerance boundary\n\nVerdict: `'+report['verdict']+'`\n\nThe ordered palette `[red, black]` forces the boundary target through the second entry. Direct actual-AEX comparator isolation proves one-ULP-below matches while exact equality and one-ULP-above reject under strict `<`. The natural v2 owner/classifier/worker path is production-byte exact for PF16/PF32 with captured LUTs and padding. PF16 codes 64/65 bracket the non-representable exact tie.\n\nKey interaction, other palettes/geometries, and AE host remain unclaimed.\n');print(json.dumps(report,indent=2,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
