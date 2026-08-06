#!/usr/bin/env python3
"""V2 Gamma Colors duplicate ordered palette and first-match semantics."""
from __future__ import annotations
import hashlib,json,struct,subprocess,tempfile
from pathlib import Path
import test_olmsmoother2_v2_nonuniform_actual_aex_20260805 as v2
import test_olmsmoother2_typed_writeback_20260717 as typed
ROOT=Path(__file__).resolve().parents[2];HARNESS=ROOT/'tools/emulation/olmsmoother2_v2_gamma_palette_duplicate_production_harness_20260805.cpp';SOURCE=ROOT/'mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp';REPORT=ROOT/'refs/conformance/olmsmoother2_v2_gamma_palette_duplicate_actual_aex_20260805.json';DOC=ROOT/'refs/conformance/olmsmoother2_v2_gamma_palette_duplicate_actual_aex_20260805.md';PALETTE=[(1.,1.,1.,1.),(1.,0.,0.,1.),(1.,1.,1.,1.)]
def req(x,m):
 if not x:raise RuntimeError('FAIL CLOSED: '+m)
def production():
 with tempfile.TemporaryDirectory(prefix='sm2gdup_') as td:
  b=Path(td)/'h';subprocess.run(['clang++','-std=c++17','-O2','-I',str(ROOT/'cli/OLMSmoother2/shim'),'-I',str(ROOT/'mac/OLMSmoother2/Mac'),str(HARNESS),'-o',str(b)],check=True);o=subprocess.run([str(b)],check=True,text=True,capture_output=True).stdout
 return dict(x.split() for x in o.splitlines())
def make_owner(l,palette):
 pb=b''.join(struct.pack('<4f',*p) for p in palette);pal=l.bump_alloc(len(pb),align=16);l.write_bytes(pal,pb);vec=l.bump_alloc(24,align=16);l.write_bytes(vec,b'\0'*24);l.write_bytes(vec+8,struct.pack('<Q',len(palette)));l.write_bytes(vec+16,struct.pack('<Q',pal));tab=l.bump_alloc(len(v2.ENCODE),align=16);l.write_bytes(tab,v2.ENCODE);ctx=l.bump_alloc(32,align=16);l.write_bytes(ctx,b'\0'*32);l.write_bytes(ctx+16,struct.pack('<Q',10000));l.write_bytes(ctx+24,struct.pack('<Q',tab));owner=l.bump_alloc(32,align=16);l.write_bytes(owner,b'\0'*32);l.write_bytes(owner,struct.pack('<Q',vec));l.write_bytes(owner+16,struct.pack('<Q',ctx));return owner,pb
def call(l,owner,color):
 c=l.bump_alloc(16,align=16);l.write_bytes(c,struct.pack('<4f',*color));r=l.call_function(0x18000A9C0,int_args=[owner,c],max_instructions=1000000);return {'match':bool(r['rax']&255),'instructions':r['instructions']}
def owner_probe():
 l=typed.AexLoader(str(typed.AEX_PATH),verbose=False,fast=False);l.register_libm_impls(max_threads=1);owner,pb=make_owner(l,PALETTE);white=call(l,owner,(1,1,1,1));red=call(l,owner,(1,0,0,1));blue=call(l,owner,(0,0,1,1));owner_single,_=make_owner(l,[(1.,1.,1.,1.)]);white_single=call(l,owner_single,(1,1,1,1));req(white['match'] and red['match'] and not blue['match'],'duplicate roles');req(white['instructions']==white_single['instructions'],'duplicate white did not return at first entry');return {'count':3,'ordered_memory_hex':pb.hex(),'first_duplicate_white':white,'middle_red':red,'no_match_blue':blue,'single_white_control':white_single,'first_match_instruction_equal_to_single_entry':True}
def main():
 px=[(0,0,1,1),(1,1,1,1),(1,0,0,1),(0,1,0,1),(.5,.75,.25,1),(.875,.125,.625,1)];px=[tuple(typed.f32(v) for v in q) for q in px];prod=production();rows=[]
 for d,pad in [('PF16',6),('PF32',12)]:
  raw,plane,linear,ci,wi=v2.actual(d,px,pad,gamma_colors=True,gamma_value=2.4,gamma_palette=PALETTE);req(raw.hex()==prod[d],d+' mismatch');rows.append({'depth':d,'raw_hex':raw.hex(),'class_plane_hex':plane.hex(),'padding_per_row':pad,'padding_preserved':True,'classifier_instructions':ci,'worker_instructions':wi,'equal':True})
 probe=owner_probe();report={'verdict':'PASS_V2_GAMMA_COLORS_DUPLICATE_ORDER_FIRST_MATCH_TO_PRODUCTION_EXACT','scope':'PF16/PF32 independent v2 Gamma Colors duplicate ordered [white,red,white], gamma2.4, key off, padded3x2, LUTs','palette_contract':{'ordered_rgba':PALETTE,'duplicate_indices':[0,2],'direct_actual_owner':probe,'first_match_semantics':'white instruction count equals single-white control despite duplicate at last index'},'aex_sha256':typed.AEX_SHA256,'decode_lut_sha256':hashlib.sha256(v2.DECODE).hexdigest(),'inverse_lut_sha256':hashlib.sha256(v2.ENCODE).hexdigest(),'fixtures':rows,'production_source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'claims_not_made':['No tolerance-tie palette claim','No other duplicate position/count','No key interaction','No AE host claim']};REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');DOC.write_text('# OLMSmoother2 v2 Gamma Colors duplicate palette\n\nVerdict: `'+report['verdict']+'`\n\nThe independent ordered palette `[white, red, white]` proves first-match semantics: actual-AEX white-match instruction count equals a single-white control, despite the duplicate last entry. PF16/PF32 natural frame paths, LUTs, padding, and production bytes are exact.\n\nTolerance ties, other duplicate layouts, key interaction, and AE host are unclaimed.\n');print(json.dumps(report,indent=2,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
