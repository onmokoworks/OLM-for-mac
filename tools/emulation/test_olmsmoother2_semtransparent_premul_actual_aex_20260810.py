#!/usr/bin/env python3
"""Semi-transparent straight/premultiplied worlds through actual AEX core and production."""
from __future__ import annotations
import hashlib,json,math,struct,subprocess,tempfile
from pathlib import Path
import test_olmsmoother2_typed_writeback_20260717 as typed
import test_olmsmoother2_v2_nonuniform_actual_aex_20260805 as v2
import test_olmsmoother2_nonuniform_geometry_actual_aex_20260805 as v1

ROOT=Path(__file__).resolve().parents[2]; W=H=5
HARNESS=ROOT/'tools/emulation/olmsmoother2_semtransparent_premul_production_harness_20260810.cpp'
SOURCE=ROOT/'mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp'
ASM=ROOT/'disasm/OLMSmoother2.aex.asm.txt'
REPORT=ROOT/'refs/conformance/olmsmoother2_semtransparent_premul_actual_aex_20260810.json'
DOC=ROOT/'refs/conformance/olmsmoother2_semtransparent_premul_actual_aex_20260810.md'
RGB=[(13,201,71),(240,17,133),(33,89,250),(199,144,7),(81,2,173),(6,77,222),(151,219,38),(244,102,63),(57,188,116),(123,45,209),(217,31,94),(42,231,155),(174,83,12),(9,164,247),(232,196,51),(69,114,184),(255,61,3),(28,214,98),(187,7,226),(104,171,39),(3,129,198),(143,238,76),(221,54,168),(91,11,242),(166,153,24)]
ALPHA={'PF8':[0,1,64,128,191,255],'PF16':[0,1,8192,16384,24576,32768],'PF32':[0.,typed.f32(1/32768),.25,.5,.75,1.]}

def req(x,m):
 if not x: raise RuntimeError('FAIL CLOSED: '+m)
def production():
 with tempfile.TemporaryDirectory(prefix='sm2_alpha_') as td:
  b=Path(td)/'h'; subprocess.run(['clang++','-std=c++17','-O2','-I',str(ROOT/'cli/OLMSmoother2/shim'),'-I',str(ROOT/'mac/OLMSmoother2/Mac'),str(HARNESS),'-o',str(b)],check=True)
  out=subprocess.run([str(b)],check=True,text=True,capture_output=True).stdout
 return {k:bytes.fromhex(v) for k,v in (line.split() for line in out.splitlines())}
def native(depth,n,premul):
 a=ALPHA[depth][n%6]; rgb=RGB[n]
 if depth=='PF8':
  c=[(v*a+127)//255 if premul else v for v in rgb]; return (a,*c)
 if depth=='PF16':
  q=[round(v*32768/255) for v in rgb]; c=[(v*a+16384)//32768 if premul else v for v in q]; return (a,*c)
 c=[typed.f32(typed.f32(v/255)*a) if premul else typed.f32(v/255) for v in rgb]; return (typed.f32(a),*c)
def encoded(depth,premul):
 out=[]
 for n in range(W*H):
  a,r,g,b=native(depth,n,premul)
  den=255 if depth=='PF8' else (32768 if depth=='PF16' else 1)
  out.append(tuple(typed.f32(v/den) for v in (r,g,b,a)))
 return out
def desc(l,b,s):
 p=l.bump_alloc(24,align=16); l.write_bytes(p,struct.pack('<QiiQ',b,W,H,s)); return p
def noninvert_key(pixels):
 l=typed.AexLoader(str(typed.AEX_PATH),verbose=False,fast=False); l.register_libm_impls(max_threads=1); stride=16*W+16; base=l.bump_alloc(stride*H,align=16)
 for y in range(H): l.write_bytes(base+y*stride,b''.join(struct.pack('<4f',*pixels[y*W+x]) for x in range(W))+b'\x3c'*16)
 d=desc(l,base,stride); ptr=[l.bump_alloc(4,align=4) for _ in range(4)]
 for p,n in zip(ptr,[W,0,H,0]): l.write_bytes(p,struct.pack('<i',n))
 color=l.bump_alloc(16,align=16); l.write_bytes(color,struct.pack('<4f',1.,typed.f32(13/255),typed.f32(201/255),typed.f32(71/255)))
 v1.SmallStatic(l,H); result=l.call_function(0x180002A70,int_args=[*ptr,d,color],max_instructions=5000000)
 out=[struct.unpack('<4f',l.read_bytes(base+y*stride+x*16,16)) for y in range(H) for x in range(W)]
 return out,result['instructions']
def actual_v1(depth,pixels,pad):
 l=typed.AexLoader(str(typed.AEX_PATH),verbose=False,fast=False); l.register_libm_impls(max_threads=1)
 ss=16*W+16; sb=l.bump_alloc(ss*H,align=16)
 for y in range(H): l.write_bytes(sb+y*ss,b''.join(struct.pack('<4f',*pixels[y*W+x]) for x in range(W))+b'\x3c'*16)
 cs=4*W+4; cb=l.bump_alloc(cs*H,align=16); l.write_bytes(cb,b'\xa5'*(cs*H)); sd,cd=desc(l,sb,ss),desc(l,cb,cs)
 rect=l.bump_alloc(16,align=16); l.write_bytes(rect,struct.pack('<4i',0,0,W,H)); cfg=l.bump_alloc(0x80,align=16); l.write_bytes(cfg,b'\0'*0x80)
 l.write_bytes(cfg,struct.pack('<i',1)); l.write_bytes(cfg+0x1c,struct.pack('<i',37)); l.write_bytes(cfg+0x20,struct.pack('<ii',73,41))
 v1.SmallStatic(l,H); cr=l.call_function(v1.FUN_ADA0,int_args=[sd,cd,rect,cfg],max_instructions=5000000)
 plane=b''.join(l.read_bytes(cb+y*cs,W*4) for y in range(H)); req(all(x in (0,255) for x in plane),'invalid class plane')
 psz={'PF8':4,'PF16':8,'PF32':16}[depth]; os=W*psz+pad; ob=l.bump_alloc(os*H,align=16); l.write_bytes(ob,b'\xa5'*(os*H)); od=desc(l,ob,os)
 ctx=l.bump_alloc(0x20,align=16); l.write_bytes(ctx,b'\0'*0x20); v1.Dynamic(l,typed.WORKERS[depth]); ptr=[l.bump_alloc(4,align=4) for _ in range(4)]
 for p,n in zip(ptr,[W,0,H,0]): l.write_bytes(p,struct.pack('<i',n))
 rr=l.call_function(typed.WORKERS[depth],int_args=[*ptr,sd,cd,od,cfg,ctx],max_instructions=20000000); raw=l.read_bytes(ob,os*H)
 for y in range(H): req(raw[y*os+W*psz:(y+1)*os]==b'\xa5'*pad,depth+' padding')
 return raw,plane,cr['instructions'],rr['instructions']
def setter_contract():
 text=ASM.read_text(); body=text[text.index('; === FUN_180004e10'):text.index('; === FUN_',text.index('; === FUN_180004e10')+10)]
 stores=[line.strip() for line in body.splitlines() if '[RCX + 0x20]' in line or '[RDI + 0x20]' in line or '[RCX + 0x21]' in line or '[RDI + 0x21]' in line]
 req(stores==['180004e5b  MOV word ptr [RCX + 0x20],SI'],f'unexpected setter premul stores {stores}')
 return {'function':'FUN_180004e10','initializer_store':stores[0],'later_writes_to_setter_0x20_or_0x21':0,'result':'both bytes remain zero for every public parameter combination','asm_sha256':hashlib.sha256(ASM.read_bytes()).hexdigest()}
def main():
 prod=production(); rows=[]
 for depth,pad in [('PF8',5),('PF16',7),('PF32',13)]:
  for version in (1,2):
   outputs={}
   for representation in ('straight','premul'):
    pix=encoded(depth,representation=='premul')
    if version==1: raw,plane,ci,wi=actual_v1(depth,pix,pad)
    else: raw,plane,_linear,ci,wi=v2.actual(depth,pix,pad,smoothness=73,smooth_range=37,extra_smooth=41,require_class_nonzero=True,width=W,height=H)
    key=f'{depth}_v{version}_{representation}_base'; req(raw==prod[key],key+' mismatch'); outputs[representation]=raw
    rows.append({'family':'base_keyoff_gamma_none','depth':depth,'version':version,'input_representation':representation,'alpha_native_values':ALPHA[depth],'class_nonzero_bytes':sum(x!=0 for x in plane),'class_plane_sha256':hashlib.sha256(plane).hexdigest(),'raw_sha256':hashlib.sha256(raw).hexdigest(),'raw_hex':raw.hex(),'padding_per_row':pad,'padding_preserved':True,'classifier_instructions':ci,'worker_instructions':wi,'equal':True})
   req(outputs['straight']!=outputs['premul'],depth+f' v{version} representations unexpectedly equivalent')
  for representation in ('straight','premul'):
   pix=encoded(depth,representation=='premul')
   for family,use_key in [('gammaall',False),('key_gammaall',True)]:
    key_instructions=0
    if use_key: pix2,key_instructions=noninvert_key(pix)
    else: pix2=pix
    raw,plane,_linear,ci,wi=v2.actual(depth,pix2,pad,gamma_all=True,gamma_value=2.4,smoothness=73,smooth_range=37,extra_smooth=41,require_class_nonzero=True,width=W,height=H)
    key=f'{depth}_v2_{representation}_{family}'; req(raw==prod[key],key+' mismatch')
    rows.append({'family':family,'depth':depth,'version':2,'input_representation':representation,'alpha_native_values':ALPHA[depth],'post_key_fractional_alpha_count':sum(0<x[3]<1 for x in pix2),'class_nonzero_bytes':sum(x!=0 for x in plane),'class_plane_sha256':hashlib.sha256(plane).hexdigest(),'raw_sha256':hashlib.sha256(raw).hexdigest(),'raw_hex':raw.hex(),'padding_per_row':pad,'padding_preserved':True,'key_owner_instructions':key_instructions,'classifier_instructions':ci,'worker_instructions':wi,'equal':True})
 report={'schema_version':1,'verdict':'PASS_SEMITRANSPARENT_PREMUL_KEY_GAMMA_V1_V2_ALL_DEPTHS_ACTUAL_AEX_TO_PRODUCTION_EXACT','scope':'PF8/PF16/PF32 padded nonuniform 5x5; alpha 0/near-zero/.25/.5/.75/1; straight and native-rounded premultiplied worlds; Version1/2 key-off Gamma None plus Version2 Gamma All key-off/non-invert; Smoothness73/Range37/Extra41','aex_sha256':typed.AEX_SHA256,'production_source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'parameter_contract':{'version':[1,2],'families':['key off + Gamma None','key off + Gamma All','non-invert key + Gamma All'],'key_rgb':[13/255,201/255,71/255],'gamma_value':2.4,'smoothness':73,'smooth_range':37,'extra_smooth':41},'setter_premultiply_contract':setter_contract(),'input_contract':{'straight':'RGB codes preserved independently of alpha','premul':'PF8/PF16 use native integer-domain rounded multiplication; PF32 uses binary32 multiplication','representations_produce_distinct_output':True},'fixtures':rows,'claims_not_made':['No claim that AE supplies straight rather than premultiplied input worlds','No invert-key or Gamma Colors interaction in this fixture','No installed AE-host invocation claim']}
 REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
 DOC.write_text('# OLMSmoother2 semi-transparent premultiplication boundary\n\nVerdict: `'+report['verdict']+'`\n\nA padded nonuniform 5x5 fixture crosses Version 1/2, PF8/PF16/PF32, and straight versus native-rounded premultiplied inputs at alpha 0, near-zero, 0.25, 0.5, 0.75, and 1. The base family uses key-off/Gamma None; representative Version 2 intersections add Gamma All with key off and with a non-invert colored key. Actual AEX classifier/core/writer bytes or float32 bits equal production in all 24 cells. The key intersection retains fractional-alpha pixels rather than collapsing the test to alpha 0/1.\n\nThe checked-in AEX setter initializes its two premultiplication-control bytes at setter `+0x20/+0x21` to zero and has no later write in `FUN_180004e10`; this supports production `keep_premul=false`. The fixture does not claim which world representation AE supplies.\n')
 print(report['verdict'])
 return 0
if __name__=='__main__': raise SystemExit(main())
