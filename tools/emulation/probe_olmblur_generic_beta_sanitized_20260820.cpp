#define OLMBLUR_PF8_RETAINED_NO_MAIN 1
#include "probe_olmblur_pf8_retained_public_admission_20260813.cpp"
#undef OLMBLUR_PF8_RETAINED_NO_MAIN

#include <type_traits>

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
    g_repeat=c.repeat;g_bias=c.bias;g_legacy=c.legacy;g_mode=NORMAL;g_fail_ordinal=0;
    g_input_format_override=g_output_format_override=PF_PixelFormat_INVALID;
    g_pre=g_pixels=g_output_hits=g_optional_checkin=g_param_out=g_param_in=g_copy=0;
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
  return ok?0:4;
}
