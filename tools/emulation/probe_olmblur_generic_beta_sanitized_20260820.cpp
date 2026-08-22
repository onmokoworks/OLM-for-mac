#include <cmath>
#include <cstdio>
#include <cstring>
#include <type_traits>
#include <vector>

#include "AE_Effect.h"
#include "AE_EffectCBSuites.h"
#include "AE_EffectSuites.h"
#include "SPBasic.h"

#include "../../mac/OLMBlur/OLMBlur.cpp"

// OLMBlur.cpp also contains the non-Smart entry points, so their references to
// AEGP_SuiteHandler must link even though this probe executes Smart Render only.
// Define the four small out-of-line methods here instead of depending on the
// ignored external-SDK utility translation units in a clean checkout.
AEGP_SuiteHandler::AEGP_SuiteHandler(const SPBasicSuite *pica_basicP)
    : i_pica_basicP(pica_basicP) {
  std::memset(&i_suites, 0, sizeof(i_suites));
  if (!i_pica_basicP) MissingSuiteError();
}

AEGP_SuiteHandler::~AEGP_SuiteHandler() { ReleaseAllSuites(); }

void AEGP_SuiteHandler::ReleaseSuite(const A_char *nameZ, A_long versionL) {
  i_pica_basicP->ReleaseSuite(nameZ, versionL);
}

void AEGP_SuiteHandler::MissingSuiteError() const {
  throw PF_Err_BAD_CALLBACK_PARAM;
}

// Minimal host implementation for the generic production lane. Keep this
// probe self-contained: the retained exact-admission probes are research
// artifacts and are intentionally not dependencies of the generic gate.
static PF_EffectWorld *g_input=nullptr,*g_output=nullptr;
static short g_depth=0;
static double g_amount=5.0;
static int g_smooth=100*65536,g_repeat=1,g_bias=1,g_legacy=0;
static int g_pixels=0,g_output_hits=0,g_optional_checkin=0;
static PF_Err g_checkin_error=PF_Err_NONE;
static int g_param_out=0,g_param_in=0,g_copy=0;
static int g_acquire=0,g_release=0,g_get_format=0;
static PF_WorldSuite2 g_world_suite{};

static PF_Err copy_world(PF_ProgPtr,PF_EffectWorld*src,PF_EffectWorld*dst,
                         PF_Rect*,PF_Rect*) {
  ++g_copy;
  if(!src||!dst||!src->data||!dst->data||src->width!=dst->width||src->height!=dst->height)
    return PF_Err_BAD_CALLBACK_PARAM;
  const size_t active=(size_t)src->width*(g_depth==8?4u:g_depth==16?8u:16u);
  if(src->rowbytes<(A_long)active||dst->rowbytes<(A_long)active)return PF_Err_BAD_CALLBACK_PARAM;
  for(A_long y=0;y<src->height;++y)std::memcpy((unsigned char*)dst->data+(size_t)y*dst->rowbytes,
    (const unsigned char*)src->data+(size_t)y*src->rowbytes,active);
  return PF_Err_NONE;
}

static PF_Err checkout_param(PF_ProgPtr,PF_ParamIndex index,A_long,A_long,A_u_long,
                             PF_ParamDef*param) {
  if(!param||index<1||index>5)return PF_Err_BAD_CALLBACK_PARAM;
  std::memset(param,0,sizeof(*param));++g_param_out;
  if(index==1)param->u.fs_d.value=g_amount;
  else if(index==2)param->u.fd.value=g_smooth;
  else if(index==3)param->u.sd.value=g_repeat;
  else if(index==4)param->u.pd.value=g_bias;
  else param->u.bd.value=g_legacy;
  return PF_Err_NONE;
}
static PF_Err checkin_param(PF_ProgPtr,PF_ParamDef*){++g_param_in;return PF_Err_NONE;}
static PF_Err pixels(PF_ProgPtr,A_long id,PF_EffectWorld**world){
  ++g_pixels;if(id!=0||!world)return PF_Err_BAD_CALLBACK_PARAM;*world=g_input;return PF_Err_NONE;
}
static PF_Err checkout_output(PF_ProgPtr,PF_EffectWorld**world){
  ++g_output_hits;if(!world)return PF_Err_BAD_CALLBACK_PARAM;*world=g_output;return PF_Err_NONE;
}
static PF_Err optional_checkin(PF_ProgPtr,A_long){++g_optional_checkin;return g_checkin_error;}
static PF_Err get_format(const PF_EffectWorld*world,PF_PixelFormat*format){
  ++g_get_format;if(!format||(world!=g_input&&world!=g_output))return PF_Err_BAD_CALLBACK_PARAM;
  *format=g_depth==8?PF_PixelFormat_ARGB32:g_depth==16?PF_PixelFormat_ARGB64:PF_PixelFormat_ARGB128;
  return PF_Err_NONE;
}
static SPErr acquire_suite(const char*name,int32 version,const void**suite){
  ++g_acquire;if(!name||std::strcmp(name,kPFWorldSuite)||version!=kPFWorldSuiteVersion2||!suite)
    return kSPBadParameterError;*suite=&g_world_suite;return kSPNoError;
}
static SPErr release_suite(const char*name,int32 version){
  ++g_release;return name&&!std::strcmp(name,kPFWorldSuite)&&version==kPFWorldSuiteVersion2?
    kSPNoError:kSPBadParameterError;
}

struct GenericCase {
  const char *id;
  int width, height, depth;
  double amount;
  int smooth_fixed, repeat, bias, legacy;
};

template<class Pixel>
static void fill_generic(unsigned char *data, int rowbytes, int width, int height) {
  for (int y=0;y<height;++y) for (int x=0;x<width;++x) {
    Pixel p{};
    if constexpr (std::is_same_v<Pixel,PF_Pixel8>) {
      p.alpha=(x+3*y)%11?255:0;p.red=(17*x+3*y+11)&255;
      p.green=(7*x+19*y+23)&255;p.blue=(29*x+13*y+37)&255;
    } else if constexpr (std::is_same_v<Pixel,PF_Pixel16>) {
      p.alpha=(x+3*y)%11?32768:0;p.red=(257*x+31*y+101)%32769;
      p.green=(113*x+211*y+307)%32769;p.blue=(401*x+97*y+503)%32769;
    } else {
      p.alpha=(x+3*y)%11?1.0f:0.0f;p.red=-0.25f+0.003f*x+0.001f*y;
      p.green=0.5f+0.002f*x-0.001f*y;p.blue=1.25f+0.001f*(x+y);
    }
    std::memcpy(data+(size_t)y*rowbytes+(size_t)x*sizeof(Pixel),&p,sizeof(p));
  }
}

template<class Pixel>
static bool run_generic(const GenericCase& c) {
  const int active=c.width*(int)sizeof(Pixel),input_rb=active+7,output_rb=active+29;
  const size_t input_size=(size_t)input_rb*c.height,output_size=(size_t)output_rb*c.height;
  std::vector<unsigned char> input(input_size,0xa5),before,output1(output_size,0xee),output2(output_size,0xee);
  fill_generic<Pixel>(input.data(),input_rb,c.width,c.height);before=input;
  auto render=[&](std::vector<unsigned char>&output)->PF_Err {
    PF_EffectWorld iw{},ow{};iw.data=(PF_PixelPtr)input.data();iw.rowbytes=input_rb;
    iw.width=c.width;iw.height=c.height;iw.extent_hint={0,0,c.width,c.height};
    ow=iw;ow.data=(PF_PixelPtr)output.data();ow.rowbytes=output_rb;
    if(c.depth!=8)iw.world_flags=ow.world_flags=PF_WorldFlag_DEEP;
    g_input=&iw;g_output=&ow;g_depth=c.depth;g_amount=c.amount;g_smooth=c.smooth_fixed;
    g_repeat=c.repeat;g_bias=c.bias;g_legacy=c.legacy;
    g_pixels=g_output_hits=g_optional_checkin=g_param_out=g_param_in=g_copy=0;
    g_acquire=g_release=g_get_format=0;
    SPBasicSuite basic{};basic.AcquireSuite=acquire_suite;basic.ReleaseSuite=release_suite;
    PF_UtilCallbacks utils{};utils.copy=copy_world;PF_InData in{};PF_OutData out{};
    in.effect_ref=(PF_ProgPtr)1;in.current_time=7;in.time_step=1;in.time_scale=24;
    in.downsample_x={1,1};in.downsample_y={1,1};in.pica_basicP=&basic;in.utils=&utils;
    in.inter.checkout_param=checkout_param;in.inter.checkin_param=checkin_param;
    PF_SmartRenderInput si{};si.bitdepth=c.depth;PF_SmartRenderCallbacks cb{};
    cb.checkout_layer_pixels=pixels;cb.checkout_output=checkout_output;cb.checkin_layer_pixels=optional_checkin;
    PF_SmartRenderExtra se{&si,&cb};
    const PF_Err err=EffectMain(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&se);
    if(!err && (g_optional_checkin!=1 || g_param_out!=5 || g_param_in!=5 || g_get_format!=2)) return 99;
    return err;
  };
  const PF_Err e1=render(output1),e2=render(output2);
  bool pads=true,changed=false;
  for(int y=0;y<c.height;++y){
    for(int i=active;i<input_rb;++i)pads&=input[(size_t)y*input_rb+i]==0xa5;
    for(int i=active;i<output_rb;++i)pads&=output1[(size_t)y*output_rb+i]==0xee&&output2[(size_t)y*output_rb+i]==0xee;
    changed|=std::memcmp(output1.data()+(size_t)y*output_rb,input.data()+(size_t)y*input_rb,active)!=0;
  }
  const bool ok=e1==PF_Err_NONE&&e2==PF_Err_NONE&&input==before&&pads&&output1==output2&&changed;
  std::printf("GENERIC %s depth=%d %dx%d legacy=%d ok=%d err=%d/%d input=%d padding=%d deterministic=%d changed=%d\n",
    c.id,c.depth,c.width,c.height,c.legacy,ok,e1,e2,input==before,pads,output1==output2,changed);
  return ok;
}

template<class Pixel>
static bool run_safety_rejections(int depth) {
  const int w=65,h=33,active=w*(int)sizeof(Pixel),rb=active+29;
  std::vector<unsigned char> input((size_t)rb*h+sizeof(Pixel),0xa5),output((size_t)rb*h,0xee);
  fill_generic<Pixel>(input.data(),rb,w,h);const auto input_before=input,output_before=output;
  PF_EffectWorld iw{},ow{};iw.data=(PF_PixelPtr)input.data();iw.rowbytes=rb;
  iw.width=w;iw.height=h;iw.extent_hint={0,0,w,h};ow=iw;
  if(depth!=8)iw.world_flags=ow.world_flags=PF_WorldFlag_DEEP;
  auto invoke=[&]()->PF_Err{
    g_input=&iw;g_output=&ow;g_depth=depth;g_amount=5.0;g_smooth=100*65536;
    g_repeat=2;g_bias=1;g_legacy=0;g_optional_checkin=0;
    SPBasicSuite basic{};basic.AcquireSuite=acquire_suite;basic.ReleaseSuite=release_suite;
    PF_UtilCallbacks utils{};utils.copy=copy_world;PF_InData in{};PF_OutData out{};
    in.effect_ref=(PF_ProgPtr)1;in.current_time=7;in.time_step=1;in.time_scale=24;
    in.downsample_x={1,1};in.downsample_y={1,1};in.pica_basicP=&basic;in.utils=&utils;
    in.inter.checkout_param=checkout_param;in.inter.checkin_param=checkin_param;
    PF_SmartRenderInput si{};si.bitdepth=depth;PF_SmartRenderCallbacks cb{};
    cb.checkout_layer_pixels=pixels;cb.checkout_output=checkout_output;cb.checkin_layer_pixels=optional_checkin;
    PF_SmartRenderExtra se{&si,&cb};return EffectMain(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&se);
  };
  // Partial overlap must be detected from addressable active spans before work.
  ow.data=(PF_PixelPtr)(input.data()+sizeof(Pixel));g_checkin_error=PF_Err_NONE;
  const PF_Err overlap_err=invoke();const bool overlap_ok=overlap_err!=PF_Err_NONE&&input==input_before;
  // Successful numerical work followed by host cleanup failure must not commit.
  ow.data=(PF_PixelPtr)output.data();g_checkin_error=97;
  const PF_Err cleanup_err=invoke();g_checkin_error=PF_Err_NONE;
  const bool cleanup_ok=cleanup_err==97&&output==output_before&&g_optional_checkin==1;
  std::printf("SAFETY depth=%d overlap=%d cleanup_atomic=%d\n",depth,overlap_ok,cleanup_ok);
  return overlap_ok&&cleanup_ok;
}

template<class Pixel>
static bool run_classic_copy(int depth,int width,int height) {
  const int active=width*(int)sizeof(Pixel),input_rb=active+7,output_rb=active+29;
  std::vector<unsigned char> input((size_t)input_rb*height,0xa5);
  std::vector<unsigned char> output((size_t)output_rb*height,0xee);
  fill_generic<Pixel>(input.data(),input_rb,width,height);
  const auto input_before=input,output_before=output;
  PF_ParamDef defs[6]{};PF_ParamDef*params[6]{};
  for(int i=0;i<6;++i)params[i]=&defs[i];
  defs[0].u.ld.data=(PF_PixelPtr)input.data();defs[0].u.ld.rowbytes=input_rb;
  defs[0].u.ld.width=width;defs[0].u.ld.height=height;
  defs[1].u.fs_d.value=5.0;defs[2].u.fd.value=100*65536;defs[3].u.sd.value=2;
  PF_LayerDef out=defs[0].u.ld;out.data=(PF_PixelPtr)output.data();out.rowbytes=output_rb;
  if(depth!=8)defs[0].u.ld.world_flags=out.world_flags=PF_WorldFlag_DEEP;
  g_input=&defs[0].u.ld;g_output=&out;g_depth=depth;
  SPBasicSuite basic{};basic.AcquireSuite=acquire_suite;basic.ReleaseSuite=release_suite;
  PF_InData in{};PF_OutData od{};in.pica_basicP=&basic;
  const PF_Err err=EffectMain(PF_Cmd_RENDER,&in,&od,params,&out,nullptr);
  bool exact=err==PF_Err_NONE&&input==input_before;
  for(int y=0;y<height;++y){
    exact&=std::memcmp(output.data()+(size_t)y*output_rb,input.data()+(size_t)y*input_rb,active)==0;
    for(int i=active;i<output_rb;++i)exact&=output[(size_t)y*output_rb+i]==0xee;
  }
  out.data=(PF_PixelPtr)(input.data()+sizeof(Pixel));
  const PF_Err overlap=EffectMain(PF_Cmd_RENDER,&in,&od,params,&out,nullptr);
  const bool safe=overlap!=PF_Err_NONE&&input==input_before;
  std::printf("CLASSIC depth=%d %dx%d exact=%d overlap=%d err=%d\n",
    depth,width,height,exact,safe,err);
  return exact&&safe&&output!=output_before;
}

int main(int argc,char**argv){
  const char*geometry=argc>1?argv[1]:"all";
  g_world_suite.PF_GetPixelFormat=get_format;bool ok=true;
  const GenericCase cases[]={
    {"odd_min",65,33,8,1.0,65536,1,1,0},
    {"odd_max",65,33,8,1000.0,6553600,10,2,1},
    {"sd",720,480,8,5.0,6553600,2,1,0},
    {"sd_high",720,480,8,1000.0,6553600,10,2,1},
    {"hd_nl",1920,1080,8,3.0,6553600,1,2,0},
    {"hd_l",1920,1080,8,3.0,6553600,1,2,1},
    {"hd_high",1920,1080,8,500.0,6553600,1,1,0},
    {"uhd_nl",3840,2160,8,1.0,6553600,1,1,0},
    {"uhd_l",3840,2160,8,1.0,6553600,1,1,1},
    {"odd_min",65,33,16,1.0,65536,1,1,0},
    {"odd_max",65,33,16,1000.0,6553600,10,2,1},
    {"sd",720,480,16,5.0,6553600,2,1,1},
    {"hd_nl",1920,1080,16,3.0,6553600,1,2,0},
    {"hd_l",1920,1080,16,3.0,6553600,1,2,1},
    {"uhd_nl",3840,2160,16,1.0,6553600,1,1,0},
    {"uhd_l",3840,2160,16,1.0,6553600,1,1,1},
    {"odd_min",65,33,32,1.0,65536,1,1,0},
    {"odd_max",65,33,32,1000.0,6553600,10,2,1},
    {"sd",720,480,32,5.0,6553600,2,1,0},
    {"hd_nl",1920,1080,32,3.0,6553600,1,2,0},
    {"hd_l",1920,1080,32,3.0,6553600,1,2,1},
    {"uhd_nl",3840,2160,32,1.0,6553600,1,1,0},
    {"uhd_l",3840,2160,32,1.0,6553600,1,1,1},
  };
  for(const auto&c:cases){
    if(!std::strcmp(geometry,"hd")&&(c.width!=1920||c.height!=1080))continue;
    if(!std::strcmp(geometry,"uhd")&&(c.width!=3840||c.height!=2160))continue;
    if(!std::strcmp(geometry,"odd")&&(c.width!=65||c.height!=33))continue;
    if(!std::strcmp(geometry,"sd")&&(c.width!=720||c.height!=480))continue;
    if(c.depth==8)ok&=run_generic<PF_Pixel8>(c);else if(c.depth==16)ok&=run_generic<PF_Pixel16>(c);else ok&=run_generic<PF_PixelFloat>(c);
  }
  if(!std::strcmp(geometry,"odd")||!std::strcmp(geometry,"all")){
    ok&=run_safety_rejections<PF_Pixel8>(8);
    ok&=run_safety_rejections<PF_Pixel16>(16);
    ok&=run_safety_rejections<PF_PixelFloat>(32);
  }
  if(!std::strcmp(geometry,"odd")||!std::strcmp(geometry,"all")){
    ok&=run_classic_copy<PF_Pixel8>(8,65,33);
    ok&=run_classic_copy<PF_Pixel16>(16,65,33);
  }
  if(!std::strcmp(geometry,"sd")||!std::strcmp(geometry,"all")){
    ok&=run_classic_copy<PF_Pixel8>(8,720,480);
    ok&=run_classic_copy<PF_Pixel16>(16,720,480);
  }
  if(!std::strcmp(geometry,"hd")||!std::strcmp(geometry,"all")){
    ok&=run_classic_copy<PF_Pixel8>(8,1920,1080);
    ok&=run_classic_copy<PF_Pixel16>(16,1920,1080);
  }
  if(!std::strcmp(geometry,"uhd")||!std::strcmp(geometry,"all")){
    ok&=run_classic_copy<PF_Pixel8>(8,3840,2160);
    ok&=run_classic_copy<PF_Pixel16>(16,3840,2160);
  }
  return ok?0:4;
}
