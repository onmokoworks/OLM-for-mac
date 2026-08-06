#!/usr/bin/env python3
"""V2 Gamma Colors two-entry ordered palette actual AEX versus production."""
from __future__ import annotations
import hashlib,json,subprocess,tempfile
from pathlib import Path
import test_olmsmoother2_v2_nonuniform_actual_aex_20260805 as v2
import test_olmsmoother2_typed_writeback_20260717 as typed
ROOT=Path(__file__).resolve().parents[2];HARNESS=ROOT/'tools/emulation/olmsmoother2_v2_gamma_palette2_production_harness_20260805.cpp';SOURCE=ROOT/'mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp';REPORT=ROOT/'refs/conformance/olmsmoother2_v2_gamma_palette2_actual_aex_20260805.json';DOC=ROOT/'refs/conformance/olmsmoother2_v2_gamma_palette2_actual_aex_20260805.md'
def req(x,m):
 if not x:raise RuntimeError('FAIL CLOSED: '+m)
def production():
 with tempfile.TemporaryDirectory(prefix='sm2gpal2_') as td:
  b=Path(td)/'h';subprocess.run(['clang++','-std=c++17','-O2','-I',str(ROOT/'cli/OLMSmoother2/shim'),'-I',str(ROOT/'mac/OLMSmoother2/Mac'),str(HARNESS),'-o',str(b)],check=True);o=subprocess.run([str(b)],check=True,text=True,capture_output=True).stdout
 return dict(x.split() for x in o.splitlines())
def owner_probe():
 l=typed.AexLoader(str(typed.AEX_PATH),verbose=False,fast=False);l.register_libm_impls(max_threads=1);pal=l.bump_alloc(32,align=16);l.write_bytes(pal,__import__('struct').pack('<8f',1,1,1,1,1,0,0,1));vec=l.bump_alloc(24,align=16);l.write_bytes(vec,b'\0'*24);l.write_bytes(vec+8,__import__('struct').pack('<Q',2));l.write_bytes(vec+16,__import__('struct').pack('<Q',pal));ctx=l.bump_alloc(0x20,align=16);tab=l.bump_alloc(len(v2.ENCODE),align=16);l.write_bytes(tab,v2.ENCODE);l.write_bytes(ctx,b'\0'*0x20);l.write_bytes(ctx+0x10,__import__('struct').pack('<Q',10000));l.write_bytes(ctx+0x18,__import__('struct').pack('<Q',tab));owner=l.bump_alloc(0x20,align=16);l.write_bytes(owner,b'\0'*0x20);l.write_bytes(owner,__import__('struct').pack('<Q',vec));l.write_bytes(owner+8,__import__('struct').pack('<i',0));l.write_bytes(owner+0x10,__import__('struct').pack('<Q',ctx));rows=[]
 for role,color in [('first_match_white',(1.,1.,1.,1.)),('last_match_red',(1.,0.,0.,1.)),('no_match_blue',(0.,0.,1.,1.))]:
  cand=l.bump_alloc(16,align=16);l.write_bytes(cand,__import__('struct').pack('<4f',*color));r=l.call_function(0x18000A9C0,int_args=[owner,cand],max_instructions=1000000);rows.append({'role':role,'returned_match':bool(r['rax']&0xff),'instructions':r['instructions']})
 req([x['returned_match'] for x in rows]==[True,True,False],'mode3 owner first/last/no-match');return {'count':2,'ordered_rgba_memory_hex':l.read_bytes(pal,32).hex(),'rows':rows}
def main():
 px=[(1,1,1,1),(0,0,1,1),(1,0,0,1),(0,1,0,1),(.5,.5,.5,1),(.75,.25,.375,1)];px=[tuple(typed.f32(v) for v in q) for q in px];palette=[(1.,1.,1.,1.),(1.,0.,0.,1.)];prod=production();rows=[]
 for d,pad in [('PF16',6),('PF32',12)]:
  raw,plane,linear,ci,wi=v2.actual(d,px,pad,gamma_colors=True,gamma_value=2.4,gamma_palette=palette);req(raw.hex()==prod[d],d+' mismatch');rows.append({'depth':d,'raw_hex':raw.hex(),'class_plane_hex':plane.hex(),'padding_per_row':pad,'padding_preserved':True,'classifier_instructions':ci,'worker_instructions':wi,'equal':True})
 probe=owner_probe();report={'verdict':'PASS_V2_GAMMA_COLORS_ORDERED_PALETTE2_NATURAL_AEX_TO_PRODUCTION_EXACT','scope':'PF16/PF32 independent v2 Gamma Colors, ordered two-color palette [white,red], gamma2.4, key off, padded3x2, LUTs','palette_contract':{'count':2,'ordered_rgba':palette,'fixture_roles':{'pixel_0':'first-entry white match','pixel_2':'last-entry red match','pixels_1_3_4_5':'no-match candidates'},'owner_iteration':'FUN_18000a9c0 advances 0x10 bytes until match or end','direct_actual_aex_probe':probe},'aex_sha256':typed.AEX_SHA256,'decode_lut_sha256':hashlib.sha256(v2.DECODE).hexdigest(),'inverse_lut_sha256':hashlib.sha256(v2.ENCODE).hexdigest(),'fixtures':rows,'production_source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'claims_not_made':['No palette count above 2','No duplicate/tolerance-tie gamma colors','No key interaction','No AE host claim']};REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');DOC.write_text('# OLMSmoother2 v2 Gamma Colors ordered palette2\n\nVerdict: `'+report['verdict']+'`\n\nThe ordered palette is `[white, red]`. A direct actual-AEX `FUN_18000a9c0` probe proves first-entry match, last-entry match, and no-match returns. Natural classifier, typed bytes, LUTs, padding, and production agree for PF16/PF32.\n\nCounts above two, duplicate/tie colors, key interaction, and AE host remain unclaimed.\n');print(json.dumps(report,indent=2,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
