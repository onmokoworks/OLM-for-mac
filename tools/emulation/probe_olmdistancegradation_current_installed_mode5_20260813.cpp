#include <cstdio>
#include <cstring>
#include <dlfcn.h>
#include <vector>

#include "AE_Effect.h"
#include "AE_EffectCBSuites.h"
#include "AE_EffectSuites.h"
#include "SPBasic.h"

#define EffectMain SourceBuiltOLMDistanceGradationEffectMain
#include "../../mac/OLMDistanceGradation/OLMDistanceGradation.cpp"
#undef EffectMain

using Effect = PF_Err (*)(PF_Cmd,PF_InData*,PF_OutData*,PF_ParamDef*[],PF_LayerDef*,void*);
constexpr int W=17,H=11,RB=W*(int)sizeof(PF_PixelFloat)+16;
static PF_ParamDef g_params[DG_NUM_PARAMS]; static PF_EffectWorld *g_input=nullptr,*g_output=nullptr;
static int g_pre=0,g_layer=0,g_output_calls=0,g_layer_in=0,g_param_out=0,g_param_in=0,g_aw=0,g_rw=0,g_ac=0,g_rc=0,g_formats=0,g_colors=0;
static PF_WorldSuite2 g_world_suite{}; static PF_ColorParamSuite1 g_color_suite{};
static PF_Err GetFormat(const PF_EffectWorld*,PF_PixelFormat *f){++g_formats;*f=PF_PixelFormat_ARGB128;return PF_Err_NONE;}
static PF_Err GetColor(PF_ProgPtr,const PF_ParamDef*p,PF_PixelFloat*out){++g_colors;out->alpha=p->u.cd.value.alpha/255.f;out->red=p->u.cd.value.red/255.f;out->green=p->u.cd.value.green/255.f;out->blue=p->u.cd.value.blue/255.f;return PF_Err_NONE;}
static SPErr Acquire(const char*n,int32 v,const void**s){
 if(!std::strcmp(n,kPFWorldSuite)&&v==kPFWorldSuiteVersion2){++g_aw;g_world_suite.PF_GetPixelFormat=GetFormat;*s=&g_world_suite;return kSPNoError;}
 if(!std::strcmp(n,kPFColorParamSuite)&&v==kPFColorParamSuiteVersion1){++g_ac;g_color_suite.PF_GetFloatingPointColorFromColorDef=GetColor;*s=&g_color_suite;return kSPNoError;}
 return kSPBadParameterError;
}
static SPErr Release(const char*n,int32 v){if(!std::strcmp(n,kPFWorldSuite)&&v==kPFWorldSuiteVersion2){++g_rw;return kSPNoError;}if(!std::strcmp(n,kPFColorParamSuite)&&v==kPFColorParamSuiteVersion1){++g_rc;return kSPNoError;}return kSPBadParameterError;}
static PF_Err CheckoutParam(PF_ProgPtr,PF_ParamIndex i,A_long,A_long,A_u_long,PF_ParamDef*p){++g_param_out;*p=g_params[i];return PF_Err_NONE;}
static PF_Err CheckinParam(PF_ProgPtr,PF_ParamDef*){++g_param_in;return PF_Err_NONE;}
static PF_Err PreCheckout(PF_ProgPtr,PF_ParamIndex i,A_long id,const PF_RenderRequest*,A_long,A_long,A_u_long,PF_CheckoutResult*r){++g_pre;if(i!=DG_INPUT||id!=DG_INPUT||!r)return PF_Err_BAD_CALLBACK_PARAM;r->result_rect={0,0,W,H};r->max_result_rect={0,0,W,H};return PF_Err_NONE;}
static PF_Err Layer(PF_ProgPtr,A_long i,PF_EffectWorld**w){++g_layer;if(i!=DG_INPUT||!w)return PF_Err_BAD_CALLBACK_PARAM;*w=g_input;return PF_Err_NONE;}
static PF_Err Output(PF_ProgPtr,PF_EffectWorld**w){++g_output_calls;if(!w)return PF_Err_BAD_CALLBACK_PARAM;*w=g_output;return PF_Err_NONE;}
static PF_Err CheckinLayer(PF_ProgPtr,A_long i){if(i==DG_INPUT)++g_layer_in;return i==DG_INPUT?PF_Err_NONE:PF_Err_BAD_CALLBACK_PARAM;}
static void Fill(std::vector<unsigned char>&b){for(int y=0;y<H;++y)for(int x=0;x<W;++x){auto*p=reinterpret_cast<PF_PixelFloat*>(b.data()+(size_t)y*RB)+x;bool t=x>=4&&x<13&&y>=2&&y<9;*p={t?0.f:1.f,((x*613+y*1231)%256)/255.f,((x*997+y*211)%256)/255.f,((x*1499+y*307)%256)/255.f};}}
static void Params(A_long interp,A_long blur,bool bg,const PF_EffectWorld&iw){std::memset(g_params,0,sizeof(g_params));g_params[DG_INPUT].u.ld=iw;g_params[DG_INVERT].u.bd.value=1;g_params[DG_IN_OUT].u.pd.value=IN_OUT_INSIDE;g_params[DG_INSIDE_THRESHOLD].u.sd.value=4;g_params[DG_OUTSIDE_THRESHOLD].u.sd.value=4;g_params[DG_RENDER_MODE].u.pd.value=RENDER_MODE_RGB;g_params[DG_USE_BG_COLOR].u.bd.value=bg;g_params[DG_GRAD_COLOR].u.cd.value={255,28,0,238};g_params[DG_BG_COLOR].u.cd.value={255,16,160,48};g_params[DG_INTERP_MODE].u.pd.value=interp;g_params[DG_POWER].u.fs_d.value=2.25;g_params[DG_BLUR_MODE].u.pd.value=blur;g_params[DG_BLUR_SIZE].u.sd.value=1;}
struct Result{PF_Err pre_err,render_err;std::vector<unsigned char>input,output;PF_EffectWorld ih,oh;int pre,layer,out,layer_in,param_out,param_in,aw,rw,ac,rc,formats,colors;bool rects;};
static Result Run(Effect effect,A_long interp,A_long blur,bool bg){
 std::vector<unsigned char>input((size_t)RB*H,0xa5),output((size_t)RB*H,0x5a);Fill(input);PF_EffectWorld iw{},ow{};iw.data=reinterpret_cast<PF_PixelPtr>(input.data());iw.rowbytes=RB;iw.width=W;iw.height=H;iw.extent_hint={0,0,W,H};ow=iw;ow.data=reinterpret_cast<PF_PixelPtr>(output.data());Params(interp,blur,bg,iw);g_input=&iw;g_output=&ow;
 g_pre=g_layer=g_output_calls=g_layer_in=g_param_out=g_param_in=g_aw=g_rw=g_ac=g_rc=g_formats=g_colors=0;SPBasicSuite basic{};basic.AcquireSuite=Acquire;basic.ReleaseSuite=Release;PF_InData in{};PF_OutData out{};in.effect_ref=reinterpret_cast<PF_ProgPtr>(1);in.pica_basicP=&basic;in.current_time=7;in.time_step=1;in.time_scale=24;in.downsample_x={1,1};in.downsample_y={1,1};in.inter.checkout_param=CheckoutParam;in.inter.checkin_param=CheckinParam;
 PF_PreRenderInput pi{};pi.bitdepth=32;pi.output_request.rect={0,0,W,H};PF_PreRenderOutput po{};PF_PreRenderCallbacks pcb{};pcb.checkout_layer=PreCheckout;PF_PreRenderExtra pe{&pi,&po,&pcb};PF_Err pre=effect(PF_Cmd_SMART_PRE_RENDER,&in,&out,nullptr,nullptr,&pe);bool rects=po.result_rect.left==0&&po.result_rect.top==0&&po.result_rect.right==W&&po.result_rect.bottom==H&&po.max_result_rect.left==0&&po.max_result_rect.top==0&&po.max_result_rect.right==W&&po.max_result_rect.bottom==H;
 PF_SmartRenderInput si{};si.bitdepth=32;PF_SmartRenderCallbacks cb{};cb.checkout_layer_pixels=Layer;cb.checkout_output=Output;cb.checkin_layer_pixels=CheckinLayer;PF_SmartRenderExtra se{&si,&cb};PF_Err render=pre?pre:effect(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&se);return{pre,render,input,output,iw,ow,g_pre,g_layer,g_output_calls,g_layer_in,g_param_out,g_param_in,g_aw,g_rw,g_ac,g_rc,g_formats,g_colors,rects};
}
static bool Padding(const std::vector<unsigned char>&b,unsigned char v){for(int y=0;y<H;++y)for(int x=W*(int)sizeof(PF_PixelFloat);x<RB;++x)if(b[(size_t)y*RB+x]!=v)return false;return true;}
int main(){const char*path=std::getenv("OLMDISTANCEGRADATION_INSTALLED_BINARY");if(!path)return 2;void*h=dlopen(path,RTLD_NOW|RTLD_LOCAL);if(!h){std::fprintf(stderr,"%s\n",dlerror());return 3;}auto installed=reinterpret_cast<Effect>(dlsym(h,"EffectMain"));if(!installed)return 4;int pass=0,total=0;auto row=[&](const char*n,bool ok,const Result&s,const Result&i){++total;if(ok)++pass;std::printf("%s pass=%d source=%d/%d installed=%d/%d\n",n,ok,s.pre_err,s.render_err,i.pre_err,i.render_err);};
 for(A_long interp:{INTERP_CONSTANT,INTERP_LINEAR,INTERP_SPHERE})for(bool bg:{false,true}){auto s=Run(SourceBuiltOLMDistanceGradationEffectMain,interp,BLUR_MODE_BILATERAL,bg),i=Run(installed,interp,BLUR_MODE_BILATERAL,bg);char n[80];std::snprintf(n,sizeof(n),"POS mode5_interp%ld_bg%d",(long)interp,bg);bool life=s.pre==1&&s.layer==1&&s.out==1&&s.layer_in==1&&s.param_out==DG_NUM_PARAMS-1&&s.param_in==DG_NUM_PARAMS-1&&s.aw==1&&s.rw==1&&s.ac==1&&s.rc==1&&s.formats==2&&s.colors==2&&s.rects;bool ilife=i.pre==s.pre&&i.layer==s.layer&&i.out==s.out&&i.layer_in==s.layer_in&&i.param_out==s.param_out&&i.param_in==s.param_in&&i.aw==s.aw&&i.rw==s.rw&&i.ac==s.ac&&i.rc==s.rc&&i.formats==s.formats&&i.colors==s.colors&&i.rects;std::printf("DIAG interp=%ld bg=%d output=%d input=%d padding=%d/%d life=%d/%d counts=%d/%d/%d/%d/%d/%d/%d/%d/%d/%d/%d\n",(long)interp,bg,s.output==i.output,s.input==i.input,Padding(s.output,0x5a),Padding(i.output,0x5a),life,ilife,s.pre,s.layer,s.out,s.layer_in,s.param_out,s.param_in,s.aw,s.rw,s.ac,s.rc,s.formats);row(n,s.pre_err==0&&s.render_err==0&&i.pre_err==0&&i.render_err==0&&s.input==i.input&&s.output==i.output&&Padding(s.output,0x5a)&&Padding(i.output,0x5a)&&life&&ilife,s,i);}
 for(A_long blur:{BLUR_MODE_NO_SCALE,BLUR_MODE_SCALE,BLUR_MODE_MEDIAN,BLUR_MODE_BILATERAL})for(bool bg:{false,true}){auto s=Run(SourceBuiltOLMDistanceGradationEffectMain,INTERP_POWER,blur,bg),i=Run(installed,INTERP_POWER,blur,bg);char n[80];std::snprintf(n,sizeof(n),"NEG power_blur%ld_bg%d",(long)blur,bg);std::vector<unsigned char>untouched((size_t)RB*H,0x5a);row(n,s.pre_err==0&&s.render_err==PF_Err_BAD_CALLBACK_PARAM&&i.pre_err==0&&i.render_err==s.render_err&&s.output==untouched&&i.output==untouched&&s.input==i.input,s,i);}
 std::printf("SUMMARY pass=%d total=%d\n",pass,total);dlclose(h);return pass==total?0:5;}
