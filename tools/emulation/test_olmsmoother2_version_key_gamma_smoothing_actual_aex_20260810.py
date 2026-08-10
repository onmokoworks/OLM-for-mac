#!/usr/bin/env python3
"""Version v1/v2 crossed with key polarity, Gamma Colors and smoothing endpoints."""
from __future__ import annotations
import hashlib,json,struct,subprocess,tempfile
from pathlib import Path
import test_olmsmoother2_typed_writeback_20260717 as typed
import test_olmsmoother2_v2_nonuniform_actual_aex_20260805 as v2
import test_olmsmoother2_nonuniform_geometry_actual_aex_20260805 as v1
ROOT=Path(__file__).resolve().parents[2];W=H=5;K=typed.f32(1/255);PALETTE=[(1.,0.,0.,1.),(K,K,K,1.)]
HARNESS=ROOT/'tools/emulation/olmsmoother2_version_key_gamma_smoothing_production_harness_20260810.cpp';SOURCE=ROOT/'mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp';REPORT=ROOT/'refs/conformance/olmsmoother2_version_key_gamma_smoothing_actual_aex_20260810.json';DOC=ROOT/'refs/conformance/olmsmoother2_version_key_gamma_smoothing_actual_aex_20260810.md'
RGB=[(1,1,1),(255,0,0),(65,1,1),(0,255,0),(206,55,161),(86,55,26),(43,73,217),(231,16,235),(116,106,230),(1,9,43),(91,38,34),(99,183,84),(230,125,149),(208,155,60),(168,21,161),(233,157,226),(8,57,119),(159,56,196),(232,156,109),(50,140,246),(229,135,20),(36,6,46),(176,107,229),(168,83,193),(235,7,162)]
def req(x,m):
 if not x:raise RuntimeError('FAIL CLOSED: '+m)
def production():
 with tempfile.TemporaryDirectory(prefix='sm2_vkg_') as td:
  b=Path(td)/'h';subprocess.run(['clang++','-std=c++17','-O2','-I',str(ROOT/'cli/OLMSmoother2/shim'),'-I',str(ROOT/'mac/OLMSmoother2/Mac'),str(HARNESS),'-o',str(b)],check=True);o=subprocess.run([str(b)],check=True,text=True,capture_output=True).stdout
 return {k:bytes.fromhex(v) for k,v in (line.split() for line in o.splitlines())}
def encoded(depth):
 if depth=='PF8':return [tuple(typed.f32(v/255) for v in (*rgb,255)) for rgb in RGB]
 if depth=='PF16':return [tuple(typed.f32(v/32768) for v in (*(round(c*32768/255) for c in rgb),32768)) for rgb in RGB]
 return [tuple(typed.f32(v/255) for v in (*rgb,255)) for rgb in RGB]
def desc(l,b,s):p=l.bump_alloc(24,align=16);l.write_bytes(p,struct.pack('<QiiQ',b,W,H,s));return p
def key_actual(pixels,invert):
 l=typed.AexLoader(str(typed.AEX_PATH),verbose=False,fast=False);l.register_libm_impls(max_threads=1);s=16*W+16;b=l.bump_alloc(s*H,align=16)
 for y in range(H):l.write_bytes(b+y*s,b''.join(struct.pack('<4f',*pixels[y*W+x]) for x in range(W))+b'\x3c'*16)
 d=desc(l,b,s);ptr=[l.bump_alloc(4,align=4) for _ in range(4)]
 for p,n in zip(ptr,[W,0,H,0]):l.write_bytes(p,struct.pack('<i',n))
 v1.SmallStatic(l,H)
 if invert:
  c=l.bump_alloc(16,align=16);l.write_bytes(c,struct.pack('<4f',K,K,K,1.));q=l.bump_alloc(0x80,align=16);l.write_bytes(q,b'\0'*0x80);l.write_bytes(q+0x60,struct.pack('<Q',1));l.write_bytes(q+0x68,struct.pack('<Q',c));r=l.call_function(0x180002930,int_args=[*ptr,d,q],max_instructions=5000000)
 else:
  c=l.bump_alloc(16,align=16);l.write_bytes(c,struct.pack('<4f',1.,K,K,K));r=l.call_function(0x180002A70,int_args=[*ptr,d,c],max_instructions=5000000)
 out=[]
 for y in range(H):
  for x in range(W):out.append(struct.unpack('<4f',l.read_bytes(b+y*s+x*16,16)))
 return out,r['instructions']
def actual_v1(depth,pixels,pad):
 l=typed.AexLoader(str(typed.AEX_PATH),verbose=False,fast=False);l.register_libm_impls(max_threads=1);ss=16*W+16;sb=l.bump_alloc(ss*H,align=16)
 for y in range(H):l.write_bytes(sb+y*ss,b''.join(struct.pack('<4f',*pixels[y*W+x]) for x in range(W))+b'\x3c'*16)
 cs=4*W+4;cb=l.bump_alloc(cs*H,align=16);l.write_bytes(cb,b'\xa5'*(cs*H));sd,cd=desc(l,sb,ss),desc(l,cb,cs);rect=l.bump_alloc(16,align=16);l.write_bytes(rect,struct.pack('<4i',0,0,W,H));cfg=l.bump_alloc(0x80,align=16);l.write_bytes(cfg,b'\0'*0x80);l.write_bytes(cfg,struct.pack('<i',1));l.write_bytes(cfg+0x1c,struct.pack('<i',100));l.write_bytes(cfg+0x20,struct.pack('<ii',100,100));colors=l.bump_alloc(32,align=16);l.write_bytes(colors,b''.join(struct.pack('<4f',*c) for c in PALETTE));l.write_bytes(cfg+0x28,struct.pack('<f',typed.f32(2.4)));l.write_bytes(cfg+0x30,struct.pack('<Q',2));l.write_bytes(cfg+0x38,struct.pack('<Q',colors));l.write_bytes(cfg+0x40,b'\x03');v1.SmallStatic(l,H);cr=l.call_function(v1.FUN_ADA0,int_args=[sd,cd,rect,cfg],max_instructions=5000000);plane=b''.join(l.read_bytes(cb+y*cs,W*4) for y in range(H));req(all(x in (0,255) for x in plane),'invalid class plane')
 psz={'PF8':4,'PF16':8,'PF32':16}[depth];os=W*psz+pad;ob=l.bump_alloc(os*H,align=16);l.write_bytes(ob,b'\xa5'*(os*H));od=desc(l,ob,os);ctx=l.bump_alloc(0x20,align=16);l.write_bytes(ctx,b'\0'*0x20);dy=v1.Dynamic(l,typed.WORKERS[depth]);ptr=[l.bump_alloc(4,align=4) for _ in range(4)]
 for p,n in zip(ptr,[W,0,H,0]):l.write_bytes(p,struct.pack('<i',n))
 rr=l.call_function(typed.WORKERS[depth],int_args=[*ptr,sd,cd,od,cfg,ctx],max_instructions=20000000);raw=l.read_bytes(ob,os*H)
 for y in range(H):req(raw[y*os+W*psz:(y+1)*os]==b'\xa5'*pad,depth+' padding')
 return raw,plane,cr['instructions'],rr['instructions']
def main():
 prod=production();rows=[]
 for depth,pad in [('PF8',5),('PF16',7),('PF32',13)]:
  outputs={}
  for version in (1,2):
   for invert in (False,True):
    variant=f'v{version}_{"invert" if invert else "noninvert"}';pix,ki=key_actual(encoded(depth),invert);az=sum(x[3]==0. for x in pix);ao=sum(x[3]==1. for x in pix);req(az and ao,depth+' '+variant+' weak key fixture')
    if version==1:raw,plane,ci,wi=actual_v1(depth,pix,pad)
    else:raw,plane,_linear,ci,wi=v2.actual(depth,pix,pad,gamma_colors=True,gamma_palette=PALETTE,gamma_value=2.4,smoothness=100,smooth_range=100,extra_smooth=100,require_class_nonzero=False,width=W,height=H)
    req(raw==prod[f'{depth}_{variant}'],depth+' '+variant+' mismatch');outputs[variant]=raw;rows.append({'depth':depth,'version':version,'key_polarity':'invert' if invert else 'non-invert','raw_sha256':hashlib.sha256(raw).hexdigest(),'raw_hex':raw.hex(),'class_plane_sha256':hashlib.sha256(plane).hexdigest(),'class_nonzero_bytes':sum(x!=0 for x in plane),'post_key_alpha_zero':az,'post_key_alpha_one':ao,'padding_per_row':pad,'padding_preserved':True,'key_owner_instructions':ki,'classifier_instructions':ci,'worker_instructions':wi,'equal':True})
  req(outputs['v1_noninvert']!=outputs['v2_noninvert'],depth+' version toggle did not affect non-invert output')
  req(outputs['v1_noninvert']!=outputs['v1_invert'] and outputs['v2_noninvert']!=outputs['v2_invert'],depth+' key polarity did not affect output')
  if depth=='PF32':req(outputs['v1_invert']!=outputs['v2_invert'],'PF32 version toggle did not affect invert output')
  else:req(outputs['v1_invert']==outputs['v2_invert'],depth+' expected integer-depth invert version equivalence drift')
 report={'verdict':'PASS_VERSION1_2_KEY_POLARITY_GAMMA_COLORS_SMOOTHING_ALL_DEPTHS_EXACT','scope':'PF8/PF16/PF32 padded5x5; Version1/2 x non-invert/invert key x Gamma Colors [red,key] gamma2.4 x Smoothness/Range/Extra100','legacy_residual_relation':'This synthetic actual-AEX core fixture closes only its declared cross-product. It does not supersede the July legacy_case_0012 Mac-AE host residual, whose different practical geometry/descriptor and host boundary remain independently scoped.','parameter_contract':{'versions':[1,2],'key_polarities':['non-invert','invert'],'key_rgb':[K,K,K],'gamma_mode':'Gamma Colors','gamma_value':2.4,'ordered_gamma_palette':PALETTE,'smoothness':100,'smooth_range':100,'extra_smooth':100},'distinctness_contract':{'noninvert_version_outputs_distinct_all_depths':True,'key_polarities_distinct_each_version_all_depths':True,'invert_version_outputs':'PF8/PF16 equivalent on this one-retained-pixel integer fixture; PF32 distinct'},'fixture_rgb_u8':[list(x) for x in RGB],'aex_sha256':typed.AEX_SHA256,'production_source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'fixtures':rows,'claims_not_made':['Does not supersede legacy_case_0012 Mac AE residual','No arbitrary parameter products','No other geometry/palette/key color','No AE-host execution claim']};REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');DOC.write_text('# OLMSmoother2 Version × key × Gamma Colors × smoothing boundary\n\nVerdict: `'+report['verdict']+'`\n\nA padded 5x5 fixture crosses Version 1/2, non-invert/invert Color Key, Gamma Colors `[red,key]` at 2.4, and public Smoothness/Range/Extra Smooth upper endpoints. PF8/PF16/PF32 actual AEX key owner, natural classifier, and typed worker match production byte-for-byte. Non-invert Version 1/2 and both key polarities are distinct at every depth. The one-retained-pixel invert fixture is version-equivalent at PF8/PF16 but version-distinct at PF32; this equivalence is recorded rather than generalized.\n\nThis synthetic core fixture does **not** supersede the July `legacy_case_0012` Mac-AE residual. That record uses different practical geometry/descriptor and includes the AE host boundary, which remain independently scoped.\n');print(report['verdict'])
if __name__=='__main__':raise SystemExit(main())
