#!/usr/bin/env python3
"""Public EffectMain SmartPreRender/SmartRender featureful six-case matrix."""
from __future__ import annotations
import hashlib, importlib.util, json, struct, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'tools/emulation/test_olmdirectionalblur_mac_smartrender_adapter_20260717.py'
FIXTURE=ROOT/'tools/emulation/dblur_fullrender_host_fixture_20260711.py'
SOURCE=ROOT/'refs/win_references/20260604_olm/OLMDirectionalBlur/case_0001_before_effects.png'
REPORT=ROOT/'refs/conformance/olmdirectionalblur_public_effectmain_feature_matrix_20260811.json'
NOTE=ROOT/'refs/conformance/olmdirectionalblur_public_effectmain_feature_matrix_20260811.md'

def load():
 spec=importlib.util.spec_from_file_location('dblur_smart_base',BASE)
 if spec is None or spec.loader is None: raise RuntimeError('adapter import')
 m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def build_probe(temp:Path)->Path:
 base=load(); base.compile_probe(temp); cpp=temp/'olmdirectionalblur_mac_smartrender_adapter_probe.cpp'; text=cpp.read_text()
 text=text.replace('static int g_render_entry_calls = 0;\nstatic PF_Err checkout_param(PF_InData*,A_long index,A_long,A_long,A_long,PF_ParamDef *p) { std::memset(p,0,sizeof(*p)); if(index==2)p->u.fs_d.value=1.0; else if(index==16)p->u.pd.value=1; else if(index==18)p->u.sd.value=1; else if(index==20)p->u.fs_d.value=10.0; return PF_Err_NONE; }',
 '''static int g_render_entry_calls=0,g_param_checkout=0,g_param_checkin=0; static PF_ParamDef g_params[23];
static PF_Err checkout_param(PF_InData*,A_long index,A_long,A_long,A_long,PF_ParamDef *p){++g_param_checkout;*p=g_params[index];return PF_Err_NONE;}
static void checkin_param(){++g_param_checkin;}''')
 text=text.replace('#define PF_CHECKIN_PARAM(...) ((void)0)','#define PF_CHECKIN_PARAM(...) checkin_param()')
 old='namespace { struct State { PF_EffectWorld *input, *output; int pre=0, layer=0, out=0, checkin=0; bool preserve=false; }; State *state(PF_ProgPtr p) { return static_cast<State*>(p); }\nPF_Err pre_checkout(PF_ProgPtr p,A_long index,A_long,PF_RenderRequest *r,A_long,A_long,A_long,PF_CheckoutResult *o) { auto*s=state(p); ++s->pre; s->preserve=r->preserve_rgb_of_zero_alpha; if(index==OLMDIRECTIONALBLUR_NOISE_LAYER) return PF_Err_BAD_CALLBACK_PARAM; o->result_rect={0,0,WIDTH,HEIGHT}; o->max_result_rect=o->result_rect; return PF_Err_NONE; }\nPF_Err layer_checkout(PF_ProgPtr p,A_long index,PF_EffectWorld **o) { ++state(p)->layer; if(index==OLMDIRECTIONALBLUR_NOISE_LAYER) { *o=nullptr; return PF_Err_BAD_CALLBACK_PARAM; } *o=state(p)->input; return PF_Err_NONE; } PF_Err output_checkout(PF_ProgPtr p,PF_EffectWorld **o) { ++state(p)->out; *o=state(p)->output; return PF_Err_NONE; } PF_Err checkin(PF_ProgPtr p,A_long) { ++state(p)->checkin; return PF_Err_NONE; }'
 new='''namespace { struct State { PF_EffectWorld *input,*noise,*output; int pre=0,layer=0,out=0,checkin_input=0,checkin_noise=0; bool preserve=false; }; State *state(PF_ProgPtr p){return static_cast<State*>(p);}
PF_Err pre_checkout(PF_ProgPtr p,A_long index,A_long,PF_RenderRequest *r,A_long,A_long,A_long,PF_CheckoutResult *o){auto*s=state(p);++s->pre;s->preserve=r->preserve_rgb_of_zero_alpha;PF_EffectWorld*w=index==OLMDIRECTIONALBLUR_NOISE_LAYER?s->noise:s->input;if(!w)return PF_Err_BAD_CALLBACK_PARAM;o->result_rect={0,0,w->width,w->height};o->max_result_rect=o->result_rect;return PF_Err_NONE;}
PF_Err layer_checkout(PF_ProgPtr p,A_long index,PF_EffectWorld **o){auto*s=state(p);++s->layer;*o=index==OLMDIRECTIONALBLUR_NOISE_LAYER?s->noise:s->input;return *o?PF_Err_NONE:PF_Err_BAD_CALLBACK_PARAM;} PF_Err output_checkout(PF_ProgPtr p,PF_EffectWorld **o){++state(p)->out;*o=state(p)->output;return PF_Err_NONE;} PF_Err checkin(PF_ProgPtr p,A_long index){auto*s=state(p);if(index==OLMDIRECTIONALBLUR_NOISE_LAYER)++s->checkin_noise;else ++s->checkin_input;return PF_Err_NONE;}'''
 if old not in text: raise RuntimeError('callback splice changed')
 text=text.replace(old,new)
 text=text[:text.index('int main()')] + r'''int main(){std::printf("{\"status\":\"pass\",\"cases\":[");bool first=true;for(short d:{8,16,32})for(int kind=0;kind<2;++kind){int W=kind==0?32:16,H=kind==0?18:16,ps=d==8?4:d==16?8:16,pad=d==8?12:d==16?16:32,rb=W*ps+pad,nrb=W*ps+pad+8;std::vector<std::uint8_t>ib(rb*H,0xa5),nb(nrb*H,0xb6),ob(rb*H,0xee);for(int y=0;y<H;y++)for(int x=0;x<W;x++){if(d==8){auto*q=reinterpret_cast<PF_Pixel8*>(ib.data()+y*rb+x*ps);q->alpha=(x+y)%5?255:96;q->red=(x*13+y*3)&255;q->green=(x*5+y*17)&255;q->blue=(x*19+y*7)&255;auto*n=reinterpret_cast<PF_Pixel8*>(nb.data()+y*nrb+x*ps);*n=*q;}else if(d==16){auto*q=reinterpret_cast<PF_Pixel16*>(ib.data()+y*rb+x*ps);q->alpha=(x+y)%5?32768:12288;q->red=(x*701+y*101)&32767;q->green=(x*211+y*907)&32767;q->blue=(x*997+y*307)&32767;auto*n=reinterpret_cast<PF_Pixel16*>(nb.data()+y*nrb+x*ps);*n=*q;}else{auto*q=reinterpret_cast<PF_PixelFloat*>(ib.data()+y*rb+x*ps);q->alpha=(x+y)%5?1.0f:0.375f;q->red=(x*13+y*3)/255.0f;q->green=(x*5+y*17)/255.0f;q->blue=(x*19+y*7)/255.0f;auto*n=reinterpret_cast<PF_PixelFloat*>(nb.data()+y*nrb+x*ps);*n=*q;}}PF_EffectWorld in{ib.data(),rb,W,H,d,{0,0,W,H}},noise{nb.data(),nrb,W,H,d,{0,0,W,H}},out{ob.data(),rb,W,H,d,{0,0,W,H}};State st{&in,kind?&noise:nullptr,&out};std::memset(g_params,0,sizeof(g_params));g_params[1].u.ad.value=45*65536;g_params[2].u.fs_d.value=1;g_params[5].u.sd.value=8;g_params[18].u.sd.value=1;g_params[20].u.fs_d.value=3;if(kind==0){g_params[3].u.fd.value=50*65536;g_params[6].u.sd.value=50;g_params[7].u.fd.value=100*65536;g_params[10].u.sd.value=8;g_params[11].u.sd.value=50;g_params[12].u.fd.value=50*65536;g_params[15].u.fd.value=100*65536;g_params[16].u.pd.value=2;}else{g_params[7].u.fd.value=50*65536;g_params[15].u.fd.value=100*65536;g_params[16].u.pd.value=3;}g_param_checkout=g_param_checkin=0;PF_InData id{&st,0,1,1,{1,1},{1,1},nullptr};PF_OutData od{};PF_PreRenderInput pi{};PF_PreRenderOutput po{};PF_PreRenderCallbacks pcb{pre_checkout};PF_PreRenderExtra pe{&pi,&po,&pcb};if(EffectMain(PF_Cmd_SMART_PRE_RENDER,&id,&od,nullptr,nullptr,&pe)!=0)return 10+d+kind;PF_SmartRenderInput si{d,po.pre_render_data};PF_SmartRenderCallbacks scb{layer_checkout,output_checkout,checkin};PF_SmartRenderExtra se{&si,&scb};PF_Err err=EffectMain(PF_Cmd_SMART_RENDER,&id,&od,nullptr,nullptr,&se);bool pads=true;for(int y=0;y<H;y++)for(int x=W*ps;x<rb;x++)pads&=ob[y*rb+x]==0xee;if(err||!pads||!st.preserve||st.pre!=2||st.layer!=2||st.out!=1||st.checkin_input!=1||st.checkin_noise!=(kind?1:0)||g_param_checkout!=21||g_param_checkin!=21)return 40+d+kind;if(!first)std::printf(",");first=false;std::printf("{\"depth\":%d,\"kind\":%d,\"width\":%d,\"height\":%d,\"rowbytes\":%d,\"noise_rowbytes\":%d,\"hex\":\"",d,kind,W,H,rb,nrb);for(int y=0;y<H;y++)for(int x=0;x<W*ps;x++)std::printf("%02x",ob[y*rb+x]);std::printf("\",\"pre_checkout\":%d,\"pixel_checkout\":%d,\"input_checkin\":%d,\"noise_checkin\":%d,\"param_checkout\":%d,\"param_checkin\":%d,\"padding\":true}",st.pre,st.layer,st.checkin_input,st.checkin_noise,g_param_checkout,g_param_checkin);if(po.delete_pre_render_data_func)po.delete_pre_render_data_func(po.pre_render_data);
if(kind==1){std::fill(ob.begin(),ob.end(),0xee);State bad{&in,nullptr,&out};id.effect_ref=&bad;PF_PreRenderOutput bpo{};PF_PreRenderExtra bpe{&pi,&bpo,&pcb};if(EffectMain(PF_Cmd_SMART_PRE_RENDER,&id,&od,nullptr,nullptr,&bpe)!=0)return 80+d;PF_SmartRenderInput bsi{d,bpo.pre_render_data};PF_SmartRenderExtra bse{&bsi,&scb};PF_Err be=EffectMain(PF_Cmd_SMART_RENDER,&id,&od,nullptr,nullptr,&bse);bool untouched=std::all_of(ob.begin(),ob.end(),[](std::uint8_t v){return v==0xee;});if(be!=PF_Err_BAD_CALLBACK_PARAM||!untouched||bad.checkin_input!=1||bad.checkin_noise!=0)return 90+d;if(bpo.delete_pre_render_data_func)bpo.delete_pre_render_data_func(bpo.pre_render_data);}}
std::printf("]}");return 0;}'''
 rgba=bytes(v for p in Image.open(SOURCE).convert('RGBA').crop((472,262,504,280)).get_flattened_data() for v in p)
 text=text.replace('int main(){',f'''static const std::uint8_t g_rgba[]={{{','.join(str(v) for v in rgba)}}};int main(){{''',1)
 text=text.replace('q->alpha=(x+y)%5?255:96;q->red=(x*13+y*3)&255;q->green=(x*5+y*17)&255;q->blue=(x*19+y*7)&255;', 'int z=(y*32+x)*4;q->alpha=g_rgba[z+3];q->red=g_rgba[z];q->green=g_rgba[z+1];q->blue=g_rgba[z+2];')
 text=text.replace('q->alpha=(x+y)%5?32768:12288;q->red=(x*701+y*101)&32767;q->green=(x*211+y*907)&32767;q->blue=(x*997+y*307)&32767;', 'int z=(y*32+x)*4;q->alpha=g_rgba[z+3]*128;q->red=g_rgba[z]*128;q->green=g_rgba[z+1]*128;q->blue=g_rgba[z+2]*128;')
 text=text.replace('q->alpha=(x+y)%5?1.0f:0.375f;q->red=(x*13+y*3)/255.0f;q->green=(x*5+y*17)/255.0f;q->blue=(x*19+y*7)/255.0f;', 'int z=(y*32+x)*4;q->alpha=g_rgba[z+3]/255.0f;q->red=g_rgba[z]/255.0f;q->green=g_rgba[z+1]/255.0f;q->blue=g_rgba[z+2]/255.0f;')
 cpp.write_text(text); exe=temp/'feature_probe'; sdk=subprocess.run(['xcrun','--show-sdk-path'],capture_output=True,text=True,check=True).stdout.strip(); cmd=['clang++','-std=c++17','-arch','arm64','-O2','-fno-fast-math','-ffp-contract=off','-isysroot',sdk,'-I',str(ROOT/'Headers'),'-I',str(ROOT/'Headers/SP'),'-I',str(ROOT/'Util'),'-I',str(ROOT/'Resources'),str(cpp),str(ROOT/'core/dblur_frontonly.cpp'),str(ROOT/'core/dblur_rotate.cpp'),str(ROOT/'core/dblur_rowdriver.cpp'),str(ROOT/'core/dblur_field.cpp'),'-framework','Cocoa','-o',str(exe)]; run=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True)
 if run.returncode: raise RuntimeError(run.stderr)
 return exe

def actual(temp:Path,depth:int,kind:int)->bytes:
 w,h=(32,18) if kind==0 else (16,16); image=Image.open(SOURCE).convert('RGBA').crop((472,262,472+w,262+h)); src=temp/f's{w}.png'; image.save(src); out=temp/f'a{depth}_{kind}.raw'; meta=temp/f'a{depth}_{kind}.json'; pad={8:12,16:16,32:32}[depth]
 cmd=[sys.executable,str(FIXTURE),'--source',str(src),'--output',str(meta),'--host-output-raw',str(out),'--bitdepth',str(depth),'--angle','45','--brightness-gain','1','--downsample-num','1','--downsample-den','1','--front-strength','8','--size-variation',str(50 if kind==0 else 0),'--front-alpha-fade',str(50 if kind==0 else 0),'--front-sharp-tail','100' if kind==0 else '50','--back-strength','8' if kind==0 else '0','--back-alpha-fade','50' if kind==0 else '0','--back-sharp-tail','50' if kind==0 else '0','--noise-variation','100','--noise-type','2' if kind==0 else '3','--seed','1','--noise-offset','0','--thickness','3','--world-area','0','0',str(w),str(h),'--row-padding',str(pad),'--no-detour-rotate','--max-instructions','40000000']
 if kind==1: cmd += ['--noise-layer-row-padding',str(pad+8),'--noise-layer-origin','0','0']
 run=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True)
 if run.returncode: raise RuntimeError(run.stderr)
 return out.read_bytes()

def main()->int:
 with tempfile.TemporaryDirectory(prefix='olm_dblur_public_feature_') as raw:
  temp=Path(raw); exe=build_probe(temp); run=subprocess.run([str(exe)],cwd=ROOT,capture_output=True,text=True)
  if run.returncode: raise RuntimeError(f'probe rc={run.returncode} {run.stderr}')
  data=json.loads(run.stdout); rows=[]
  for case in data['cases']:
   depth,kind=case['depth'],case['kind']; got=bytes.fromhex(case.pop('hex')); expected=actual(temp,depth,kind); mismatch=sum(a!=b for a,b in zip(got,expected))
   if len(got)!=len(expected) or mismatch:
    first=next((i for i,(a,b) in enumerate(zip(got,expected)) if a!=b),-1)
    raise RuntimeError(f'PF{depth} kind={kind} mismatch={mismatch} first={first} got={got[first:first+16].hex()} expected={expected[first:first+16].hex()}')
   expected_noise_checkin=1 if kind else 0
   if (case['pre_checkout']!=2 or case['pixel_checkout']!=2 or
       case['input_checkin']!=1 or case['noise_checkin']!=expected_noise_checkin or
       case['param_checkout']!=21 or case['param_checkin']!=21 or not case['padding']):
    raise RuntimeError(f'PF{depth} kind={kind} callback contract mismatch: {case}')
   case.update({'route':'dual_side_type2' if kind==0 else 'valid_type3_layer','raw_sha256':hashlib.sha256(got).hexdigest(),'raw_exact':True,'missing_type3_layer_bad_callback':kind==1}); rows.append(case)
 report={'schema_version':1,'status':'exact_public_effectmain_feature_matrix','plugin':'OLMDirectionalBlur','cases':rows,'depths':['PF8','PF16','PF32'],'fixed_source':'top-left 32x18 / 16x16 crops at (472,262) from the pinned case_0001 before-effects reference','routes':['32x18 dual-side Type2 existing tuple','16x16 valid same-size padded Type3 existing tuple'],'public_contract':'EffectMain SMART_PRE_RENDER then SMART_RENDER; all 21 non-input public params checkout/checkin, input/noise/output world lifecycle, output padding, and typed raw output verified. Missing Type3 Layer returns BAD_CALLBACK_PARAM with output untouched.','not_proven':['other source content','unlisted tuple','other Layer dimensions/origins','interactive AE export']}
 REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n'); NOTE.write_text('# OLMDirectionalBlur public EffectMain feature matrix — 2026-08-11\n\nPublic `EffectMain` SmartPreRender→SmartRender is raw exact against actual AEX for PF8/PF16/PF32 on two nondefault routes: the proven 32×18 dual-side Type 2 tuple and a proven 16×16 same-size padded Type 3 Layer tuple (6 cases). All 21 non-input public parameters are checked out/in, input/noise/output world lifecycle and row padding are verified, and a missing Type 3 Layer returns `PF_Err_BAD_CALLBACK_PARAM` without touching output. The claim remains limited to the pinned case_0001 source crops; a synthetic PF32 source exposed a different owner result and was not generalized.\n\nReproduction: `python3 tools/emulation/test_olmdirectionalblur_public_effectmain_feature_matrix_20260811.py`\n'); print('PASS_OLMDIRECTIONALBLUR_PUBLIC_EFFECTMAIN_FEATURE cases=6 raw=exact'); return 0
if __name__=='__main__': raise SystemExit(main())
