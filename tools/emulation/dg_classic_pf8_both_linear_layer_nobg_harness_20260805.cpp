#include "dg_renderbits_real_harness_20260716_sdk_shim.h"
#include "../../mac/OLMDistanceGradation/OLMDistanceGradation.cpp"
#include <cstdint>
#include <cstdio>
#include <fstream>
#include <iterator>
#include <vector>
static std::vector<std::uint8_t>read_all(const char*p){std::ifstream s(p,std::ios::binary);return {std::istreambuf_iterator<char>(s),{}};}
int main(int argc,char**argv){if(argc!=3)return 2;auto src=read_all(argv[1]),exp=read_all(argv[2]);constexpr int w=17,h=11,irb=75,orb=79;if(src.size()!=irb*h||exp.size()!=orb*h)return 3;std::vector<std::uint8_t>out(orb*h,0xa5);PF_LayerDef iw{src.data(),w,h,irb,8,{0,0,w,h}},ow{out.data(),w,h,orb,8,{0,0,w,h}};
 std::array<PF_ParamDef,DG_NUM_PARAMS>st{};PF_ParamDef*p[DG_NUM_PARAMS];for(int i=0;i<DG_NUM_PARAMS;i++)p[i]=&st[i];st[DG_INPUT].u.ld=iw;st[DG_INVERT].u.bd.value=1;st[DG_IN_OUT].u.pd.value=IN_OUT_BOTH;st[DG_INSIDE_THRESHOLD].u.sd.value=6;st[DG_OUTSIDE_THRESHOLD].u.sd.value=5;st[DG_RENDER_MODE].u.pd.value=RENDER_MODE_LAYER;st[DG_USE_BG_COLOR].u.bd.value=0;st[DG_GRAD_COLOR].u.cd.value={255,28,0,238};st[DG_BG_COLOR].u.cd.value={255,16,160,48};st[DG_INTERP_MODE].u.pd.value=INTERP_LINEAR;st[DG_POWER].u.fs_d.value=1;st[DG_BLUR_MODE].u.pd.value=BLUR_MODE_NONE;PF_InData id{};id.downsample_x={1,1};id.downsample_y={1,1};if(RenderBits<PF_Pixel8>(&id,p,&iw,&ow)!=0)return 4;size_t bad=0;for(size_t i=0;i<out.size();i++)if(out[i]!=exp[i])bad++;if(bad){std::fprintf(stderr,"mismatched bytes=%zu\n",bad);for(size_t i=0,n=0;i<out.size()&&n<12;i++)if(out[i]!=exp[i]){std::fprintf(stderr,"bad %zu got %u exp %u\n",i,(unsigned)out[i],(unsigned)exp[i]);n++;}return 1;}std::printf("PASS classic_pf8_both_linear_layer_nobg bytes=%zu mismatches=0 rowbytes=%d/%d\n",out.size(),irb,orb);return 0;}
