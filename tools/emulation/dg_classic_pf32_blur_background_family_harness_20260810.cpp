#include "dg_renderbits_real_harness_20260716_sdk_shim.h"
#include "../../mac/OLMDistanceGradation/OLMDistanceGradation.cpp"
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iterator>
#include <string>
#include <vector>
static std::vector<std::uint8_t>read_all(const char*p){std::ifstream s(p,std::ios::binary);return {std::istreambuf_iterator<char>(s),{}};}
int main(int argc,char**argv){if(argc!=6)return 2;auto src=read_all(argv[1]),exp=read_all(argv[2]),before=src;const std::string interp(argv[3]);int bg=std::atoi(argv[4]),blur=std::atoi(argv[5]);constexpr int w=17,h=11,irb=280,orb=288;if(src.size()!=irb*h||exp.size()!=orb*h||bg<0||bg>1||blur<2||blur>3)return 3;std::vector<std::uint8_t>out(orb*h,0xa5);PF_LayerDef iw{src.data(),w,h,irb,32,{0,0,w,h}},ow{out.data(),w,h,orb,32,{0,0,w,h}};
 std::array<PF_ParamDef,DG_NUM_PARAMS>st{};PF_ParamDef*p[DG_NUM_PARAMS];for(int i=0;i<DG_NUM_PARAMS;i++)p[i]=&st[i];st[DG_INPUT].u.ld=iw;st[DG_INVERT].u.bd.value=1;st[DG_IN_OUT].u.pd.value=IN_OUT_INSIDE;st[DG_INSIDE_THRESHOLD].u.sd.value=4;st[DG_OUTSIDE_THRESHOLD].u.sd.value=4;st[DG_RENDER_MODE].u.pd.value=RENDER_MODE_RGB;st[DG_USE_BG_COLOR].u.bd.value=bg;st[DG_GRAD_COLOR].u.cd.value={255,28,0,238};st[DG_BG_COLOR].u.cd.value={255,16,160,48};st[DG_INTERP_MODE].u.pd.value=interp=="constant"?INTERP_CONSTANT:INTERP_LINEAR;st[DG_POWER].u.fs_d.value=1;st[DG_BLUR_MODE].u.pd.value=blur;st[DG_BLUR_SIZE].u.sd.value=1;PF_InData id{};id.downsample_x={1,1};id.downsample_y={1,1};if(RenderBits<PF_PixelFloat>(&id,p,&iw,&ow)!=0)return 4;if(src!=before)return 5;size_t bad=0;for(size_t i=0;i<out.size();i++)bad+=out[i]!=exp[i];if(bad){std::fprintf(stderr,"mismatched bytes=%zu interp=%s bg=%d blur=%d\n",bad,interp.c_str(),bg,blur);for(size_t i=0,n=0;i<out.size()&&n<16;i++)if(out[i]!=exp[i]){std::fprintf(stderr,"bad %zu got %u expected %u\n",i,(unsigned)out[i],(unsigned)exp[i]);n++;}return 1;}std::printf("PASS interp=%s bg=%d blur=%d bytes=%zu mismatches=0\n",interp.c_str(),bg,blur,out.size());return 0;}
