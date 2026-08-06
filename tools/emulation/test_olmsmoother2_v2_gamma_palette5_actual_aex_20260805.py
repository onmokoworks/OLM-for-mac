#!/usr/bin/env python3
"""V2 Gamma Colors ordered five-entry palette actual AEX versus production."""
from __future__ import annotations
import hashlib,json,struct,subprocess,tempfile
from pathlib import Path
import test_olmsmoother2_v2_nonuniform_actual_aex_20260805 as v2
import test_olmsmoother2_typed_writeback_20260717 as typed
import test_olmsmoother2_v2_gamma_palette_duplicate_actual_aex_20260805 as dup
ROOT=Path(__file__).resolve().parents[2];HARNESS=ROOT/'tools/emulation/olmsmoother2_v2_gamma_palette5_production_harness_20260805.cpp';SOURCE=ROOT/'mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp';REPORT=ROOT/'refs/conformance/olmsmoother2_v2_gamma_palette5_actual_aex_20260805.json';DOC=ROOT/'refs/conformance/olmsmoother2_v2_gamma_palette5_actual_aex_20260805.md';PALETTE=[(1.,1.,1.,1.),(1.,0.,0.,1.),(0.,0.,1.,1.),(0.,1.,0.,1.),(1.,1.,0.,1.)]
def req(x,m):
 if not x:raise RuntimeError('FAIL CLOSED: '+m)
def production():
 with tempfile.TemporaryDirectory(prefix='sm2gp5_') as td:
  b=Path(td)/'h';subprocess.run(['clang++','-std=c++17','-O2','-I',str(ROOT/'cli/OLMSmoother2/shim'),'-I',str(ROOT/'mac/OLMSmoother2/Mac'),str(HARNESS),'-o',str(b)],check=True);o=subprocess.run([str(b)],check=True,text=True,capture_output=True).stdout
 return dict(x.split() for x in o.splitlines())
def probe():
 l=typed.AexLoader(str(typed.AEX_PATH),verbose=False,fast=False);l.register_libm_impls(max_threads=1);owner,pb=dup.make_owner(l,PALETTE);cases=[('first_white',(1,1,1,1),True),('middle1_red',(1,0,0,1),True),('middle2_blue',(0,0,1,1),True),('middle3_green',(0,1,0,1),True),('last_yellow',(1,1,0,1),True),('no_match_gray',(.375,.75,.25,1),False)];rows=[]
 for role,color,want in cases:
  got=dup.call(l,owner,color);req(got['match']==want,role);rows.append({'role':role,'match':got['match'],'instructions':got['instructions']})
 return {'count':5,'ordered_memory_hex':pb.hex(),'rows':rows}
def main():
 px=[(1,1,1,1),(1,0,0,1),(0,0,1,1),(0,1,0,1),(1,1,0,1),(.375,.75,.25,1)];px=[tuple(typed.f32(v) for v in q) for q in px];prod=production();rows=[]
 for d,pad in [('PF16',6),('PF32',12)]:
  raw,plane,linear,ci,wi=v2.actual(d,px,pad,gamma_colors=True,gamma_value=2.4,gamma_palette=PALETTE);req(raw.hex()==prod[d],d+' mismatch');rows.append({'depth':d,'raw_hex':raw.hex(),'class_plane_hex':plane.hex(),'padding_per_row':pad,'padding_preserved':True,'classifier_instructions':ci,'worker_instructions':wi,'equal':True})
 p=probe();report={'verdict':'PASS_V2_GAMMA_COLORS_ORDERED_PALETTE5_TO_PRODUCTION_EXACT','scope':'PF16/PF32 independent v2 Gamma Colors ordered [white,red,blue,green,yellow] count5, gamma2.4, key off, padded3x2, LUTs','palette_contract':{'ordered_rgba':PALETTE,'direct_actual_owner':p,'frame_roles':{'pixel0':'first white','pixel1':'middle1 red','pixel2':'middle2 blue','pixel3':'middle3 green','pixel4':'last yellow','pixel5':'no-match gray'}},'aex_sha256':typed.AEX_SHA256,'decode_lut_sha256':hashlib.sha256(v2.DECODE).hexdigest(),'inverse_lut_sha256':hashlib.sha256(v2.ENCODE).hexdigest(),'fixtures':rows,'production_source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'claims_not_made':['No count above 5','No key interaction','No other palette/geometry','No AE host claim']};REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');DOC.write_text('# OLMSmoother2 v2 Gamma Colors ordered palette5\n\nVerdict: `'+report['verdict']+'`\n\nOrdered `[white, red, blue, green, yellow]` covers direct actual-AEX first, all three middle positions, last, and no-match returns. PF16/PF32 natural owner/classifier/worker paths, production bytes, LUTs, and padding are exact.\n\nCounts above five, key interaction, other palettes/geometries, and AE host remain unclaimed.\n');print(json.dumps(report,indent=2,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
