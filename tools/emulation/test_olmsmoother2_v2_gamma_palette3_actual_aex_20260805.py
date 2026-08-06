#!/usr/bin/env python3
"""V2 Gamma Colors ordered three-entry palette actual AEX versus production."""
from __future__ import annotations
import hashlib,json,struct,subprocess,tempfile
from pathlib import Path
import test_olmsmoother2_v2_nonuniform_actual_aex_20260805 as v2
import test_olmsmoother2_typed_writeback_20260717 as typed
ROOT=Path(__file__).resolve().parents[2];HARNESS=ROOT/'tools/emulation/olmsmoother2_v2_gamma_palette3_production_harness_20260805.cpp';SOURCE=ROOT/'mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp';REPORT=ROOT/'refs/conformance/olmsmoother2_v2_gamma_palette3_actual_aex_20260805.json';DOC=ROOT/'refs/conformance/olmsmoother2_v2_gamma_palette3_actual_aex_20260805.md'
PALETTE=[(1.,1.,1.,1.),(1.,0.,0.,1.),(0.,0.,1.,1.)]
def req(x,m):
 if not x:raise RuntimeError('FAIL CLOSED: '+m)
def production():
 with tempfile.TemporaryDirectory(prefix='sm2gpal3_') as td:
  b=Path(td)/'h';subprocess.run(['clang++','-std=c++17','-O2','-I',str(ROOT/'cli/OLMSmoother2/shim'),'-I',str(ROOT/'mac/OLMSmoother2/Mac'),str(HARNESS),'-o',str(b)],check=True);o=subprocess.run([str(b)],check=True,text=True,capture_output=True).stdout
 return dict(x.split() for x in o.splitlines())
def owner_probe():
 l=typed.AexLoader(str(typed.AEX_PATH),verbose=False,fast=False);l.register_libm_impls(max_threads=1);pb=b''.join(struct.pack('<4f',*p) for p in PALETTE);pal=l.bump_alloc(len(pb),align=16);l.write_bytes(pal,pb);vec=l.bump_alloc(24,align=16);l.write_bytes(vec,b'\0'*24);l.write_bytes(vec+8,struct.pack('<Q',3));l.write_bytes(vec+16,struct.pack('<Q',pal));tab=l.bump_alloc(len(v2.ENCODE),align=16);l.write_bytes(tab,v2.ENCODE);ctx=l.bump_alloc(0x20,align=16);l.write_bytes(ctx,b'\0'*0x20);l.write_bytes(ctx+0x10,struct.pack('<Q',10000));l.write_bytes(ctx+0x18,struct.pack('<Q',tab));owner=l.bump_alloc(0x20,align=16);l.write_bytes(owner,b'\0'*0x20);l.write_bytes(owner,struct.pack('<Q',vec));l.write_bytes(owner+0x10,struct.pack('<Q',ctx));rows=[]
 for role,color in [('first_white',(1,1,1,1)),('middle_red',(1,0,0,1)),('last_blue',(0,0,1,1)),('no_match_green',(0,1,0,1))]:
  c=l.bump_alloc(16,align=16);l.write_bytes(c,struct.pack('<4f',*color));r=l.call_function(0x18000A9C0,int_args=[owner,c],max_instructions=1000000);rows.append({'role':role,'match':bool(r['rax']&255),'instructions':r['instructions']})
 req([r['match'] for r in rows]==[1,1,1,0],'owner roles');return {'count':3,'ordered_memory_hex':pb.hex(),'rows':rows}
def main():
 px=[(0,1,0,1),(1,1,1,1),(1,0,0,1),(0,0,1,1),(.5,.25,.75,1),(1,1,0,1)];px=[tuple(typed.f32(v) for v in q) for q in px];prod=production();rows=[]
 for d,pad in [('PF16',6),('PF32',12)]:
  raw,plane,linear,ci,wi=v2.actual(d,px,pad,gamma_colors=True,gamma_value=2.4,gamma_palette=PALETTE);req(raw.hex()==prod[d],d+' mismatch');rows.append({'depth':d,'raw_hex':raw.hex(),'class_plane_hex':plane.hex(),'padding_per_row':pad,'padding_preserved':True,'classifier_instructions':ci,'worker_instructions':wi,'equal':True})
 probe=owner_probe();report={'verdict':'PASS_V2_GAMMA_COLORS_ORDERED_PALETTE3_NATURAL_AEX_TO_PRODUCTION_EXACT','scope':'PF16/PF32 independent v2 Gamma Colors ordered [white,red,blue] count3, gamma2.4, key off, padded3x2, LUTs','palette_contract':{'ordered_rgba':PALETTE,'direct_actual_owner':probe,'frame_roles':{'pixel1':'first white','pixel2':'middle red','pixel3':'last blue','pixels0_4_5':'no-match'}},'aex_sha256':typed.AEX_SHA256,'decode_lut_sha256':hashlib.sha256(v2.DECODE).hexdigest(),'inverse_lut_sha256':hashlib.sha256(v2.ENCODE).hexdigest(),'fixtures':rows,'production_source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'claims_not_made':['No count above 3','No duplicate/tolerance-tie palette','No key interaction','No AE host claim']};REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');DOC.write_text('# OLMSmoother2 v2 Gamma Colors ordered palette3\n\nVerdict: `'+report['verdict']+'`\n\nThe independent ordered palette `[white, red, blue]` covers direct actual-AEX first, middle, last, and no-match returns. PF16/PF32 natural frame paths, LUTs, padding, and production bytes are exact.\n\nCounts above three, duplicate/tie palette entries, key interaction, and AE host are unclaimed.\n');print(json.dumps(report,indent=2,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
