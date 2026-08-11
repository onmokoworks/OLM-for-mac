#!/usr/bin/env python3
"""Public EffectMain SmartPreRender/SmartRender covering matrix."""
from __future__ import annotations
import hashlib,json,math,subprocess,tempfile
from pathlib import Path
import test_olmsmoother2_geometry_classifier_matrix_actual_aex_20260811 as base
ROOT=Path(__file__).resolve().parents[2];HARNESS=ROOT/'tools/emulation/olmsmoother2_public_effectmain_all_depths_production_harness_20260812.cpp';SOURCE=ROOT/'mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp';REPORT=ROOT/'refs/conformance/olmsmoother2_public_effectmain_all_depths_actual_aex_20260812.json';DOC=ROOT/'refs/conformance/olmsmoother2_public_effectmain_all_depths_actual_aex_20260812.md';W,H=17,11
K=base.f32(1/255);NORMAL=[(1.,0.,0.,1.),(K,K,K,1.),(0.,0.,1.,1.),(0.,1.,0.,1.),(1.,1.,0.,1.)];REORDERED=[NORMAL[4],NORMAL[3],NORMAL[1],NORMAL[0],NORMAL[2]];DUPLICATE=[NORMAL[0],NORMAL[1],NORMAL[0],NORMAL[1],NORMAL[2]]
TUPLES=[('pf8_v1_none_keyoff_default_straight','PF8',1,'none','key_off',NORMAL[:1],1.,100,2,0,'straight'),('pf8_v2_colors_count5_duplicate_invert_mixed_premul','PF8',2,'gamma_colors','colors_invert',DUPLICATE,2.4,50,50,50,'premul'),('pf16_v2_all_keyoff_mixed_straight','PF16',2,'gamma_all','key_off',NORMAL[:1],2.4,50,50,50,'straight'),('pf16_v2_colors_count5_reordered_noninvert_default_premul','PF16',2,'gamma_colors','colors_noninvert',REORDERED,1.,100,2,0,'premul'),('pf32_v1_none_keyoff_mixed_premul','PF32',1,'none','key_off',NORMAL[:1],1.,50,50,50,'premul'),('pf32_v2_colors_count1_noninvert_default_straight','PF32',2,'gamma_colors','colors_noninvert',NORMAL[:1],2.4,100,2,0,'straight')]
ALPHAS=(0,1,64,128,192,255)
def req(x,m):
 if not x:raise RuntimeError('FAIL CLOSED: '+m)
def logical(x,y):
 u=((x+1)*0x9e3779b9)^((y+3)*0x85ebca6b);u&=0xffffffff;u^=u>>16;u=(u*0x7feb352d)&0xffffffff;u^=u>>15
 if x==0 and y==0:return(1,1,1,128)
 if x==1 and y==0:return(255,0,0,192)
 return(u&255,(u>>8)&255,(u>>16)&255,ALPHAS[(x+3*y)%6])
def pixels(depth,representation):
 out=[]
 for y in range(H):
  for x in range(W):
   r,g,b,a=logical(x,y)
   if depth=='PF8':
    if representation=='premul':r,g,b=((c*a+127)//255 for c in (r,g,b))
    inv=base.f32(1/255);out.append(tuple(base.f32(base.f32(c)*inv) for c in (r,g,b,a)))
   elif depth=='PF16':
    n=lambda c:int(math.floor(c*32768/255+.5));r,g,b,a=n(r),n(g),n(b),n(a)
    if representation=='premul':r,g,b=((c*a+16384)//32768 for c in (r,g,b))
    out.append(tuple(base.f32(c/32768) for c in (r,g,b,a)))
   else:
    r,g,b,a=(base.f32(c/255) for c in (r,g,b,a))
    if representation=='premul':r,g,b=(base.f32(c*a) for c in (r,g,b))
    out.append((r,g,b,a))
 return out
def main():
 with tempfile.TemporaryDirectory(prefix='sm2_effectmain_all_') as td:
  binary=Path(td)/'h';subprocess.run(['clang++','-std=c++17','-O2','-I',str(ROOT/'cli/OLMSmoother2/shim'),'-I',str(ROOT/'mac/OLMSmoother2/Mac'),str(HARNESS),'-o',str(binary)],check=True);lines=subprocess.run([str(binary)],check=True,text=True,capture_output=True).stdout.splitlines();prod={int(line.split()[1]):bytes.fromhex(line.split()[2]) for line in lines if line.startswith('CASE ')};meta={int(line.split()[1]):[int(x) for x in line.split()[2:]] for line in lines if line.startswith('META ')};req(len(prod)==len(meta)==6,'harness cases')
  rows=[]
  for i,(name,depth,version,feature,key_mode,palette,gamma,s,r,e,representation) in enumerate(TUPLES):
   psz,pad=base.DEPTHS[depth];actual,plane,ci,wi=base.actual(depth,version,pixels(depth,representation),pad,W,H,s,r,e,feature,gamma,None,palette,key_mode);req(actual==prod[i],name+' actual/core mismatch');m=meta[i];req(m[:7]==[1,1,1,15,15,16,-1],name+' callbacks/rect');classic=(m[7]==1) if depth!='PF32' else None;req(depth=='PF32' or classic,name+' classic mismatch');rb=W*psz+pad;req(all(actual[y*rb+W*psz:(y+1)*rb]==b'\xa5'*pad for y in range(H)),name+' padding');rows.append({'id':name,'depth':depth,'version':version,'gamma_mode':feature,'gamma_value':gamma,'key_mode':key_mode,'palette_count':len(palette),'palette_rgba':palette,'smoothing':[s,r,e],'input_representation':representation,'alpha_native_codes':list(ALPHAS),'raw_sha256':hashlib.sha256(actual).hexdigest(),'class_plane_sha256':hashlib.sha256(plane).hexdigest(),'classifier_instructions':ci,'worker_instructions':wi,'callbacks':{'smart_pre_checkout_layer':1,'smart_checkout_layer_pixels':1,'smart_checkout_output':1,'parameter_checkout':15,'parameter_checkin':15},'result_rect':[1,2,16,10],'max_result_rect':[-1,-2,18,13],'classic_same_params_raw_equal':classic,'input_unchanged':True,'padding_preserved':True,'exact':True})
  source=SOURCE.read_text();req('pre_render_data' not in source,'unexpected pre-render ownership added')
  report={'schema':'olmsmoother2.public-effectmain-all-depths/1','verdict':'PASS_6_PUBLIC_EFFECTMAIN_SMARTPRE_SMARTRENDER_ALL_DEPTHS_ACTUAL_AEX_CORE_EXACT','scope':'PF8/PF16/PF32 two cases each; padded 17x11 semi-transparent practical fixture; SmartPreRender then SmartRender public EffectMain','case_count':len(rows),'cases':rows,'smart_pre_render_ownership':{'pre_render_data':'none','free_callback':'not applicable: OLMSmoother2 SmartPreRender allocates no pre-render data','result_rect_union_verified':True},'classic_boundary':{'PF8':'same-params raw exact in both cases','PF16':'same-params raw exact in both cases','PF32':'fail-closed/not applicable: classic Render dispatch has no PF32 branch; PF32 numerical public path is SmartRender'},'actual_aex_oracle':'actual AEX natural owner/classifier/typed worker for identical normalized typed inputs','actual_aex_sha256':base.typed.AEX_SHA256,'production_source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'claims_not_made':['No AE process execution','No actual-AEX exported owner claim from this fixture','No PF32 classic Render claim','No arbitrary parameters/geometry/input-representation generalization']};REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');DOC.write_text('# OLMSmoother2 public EffectMain all-depth covering\n\nVerdict: `'+report['verdict']+'`\n\nSix padded 17x11 semi-transparent cases (two per depth) cross Version 1/2, Gamma None/All/Colors, key off/non-invert/invert, palette count 1/5 with reorder/duplicate, default/mixed smoothing, and straight/native-premultiplied inputs. Production `EffectMain(SmartPreRender -> SmartRender)` matches the actual-AEX core raw bytes or PF32 float words in all cases. Input bytes and row padding remain unchanged/preserved; callback counts and result/max-result rectangles are exact.\n\nPF8/PF16 same-parameter classic Render is raw-identical. PF32 classic is deliberately fail-closed because that dispatcher has no PF32 branch. SmartPreRender owns no pre-render allocation, so no free callback applies. AE-host execution and unlisted combinations are not generalized.\n');print(report['verdict'],len(rows))
 return 0
if __name__=='__main__':raise SystemExit(main())
