#include "dg_renderbits_real_harness_20260716_sdk_shim.h"
#include "../../mac/OLMDistanceGradation/OLMDistanceGradation.cpp"
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iterator>
#include <vector>

static std::vector<std::uint8_t> read_all(const char *p){std::ifstream s(p,std::ios::binary);return {std::istreambuf_iterator<char>(s),{}};}
static std::uint16_t u16(const std::vector<std::uint8_t>&b,std::size_t o){std::uint16_t v;std::memcpy(&v,b.data()+o,2);return v;}
int main(int argc,char**argv){
 if(argc!=3)return 2; auto src=read_all(argv[1]), exp=read_all(argv[2]); if(src.size()!=1496||exp.size()!=1496)return 3;
 std::vector<PF_Pixel16> in(187),out(187); for(size_t i=0;i<187;i++){in[i]={u16(src,i*8),u16(src,i*8+4),u16(src,i*8+2),u16(src,i*8+6)};}
 PF_LayerDef iw{in.data(),17,11,17*8,16,{0,0,17,11}},ow{out.data(),17,11,17*8,16,{0,0,17,11}};
 std::array<PF_ParamDef,DG_NUM_PARAMS> st{}; PF_ParamDef* p[DG_NUM_PARAMS]; for(int i=0;i<DG_NUM_PARAMS;i++)p[i]=&st[i];
 st[DG_INPUT].u.ld=iw; st[DG_INVERT].u.bd.value=1; st[DG_IN_OUT].u.pd.value=IN_OUT_INSIDE; st[DG_INSIDE_THRESHOLD].u.sd.value=4; st[DG_OUTSIDE_THRESHOLD].u.sd.value=4; st[DG_RENDER_MODE].u.pd.value=RENDER_MODE_RGB; st[DG_USE_BG_COLOR].u.bd.value=1; st[DG_GRAD_COLOR].u.cd.value={255,28,0,238}; st[DG_BG_COLOR].u.cd.value={255,255,0,0}; st[DG_INTERP_MODE].u.pd.value=INTERP_LINEAR; st[DG_POWER].u.fs_d.value=1; st[DG_BLUR_MODE].u.pd.value=BLUR_MODE_NONE;
 PF_InData id{};id.downsample_x={1,1};id.downsample_y={1,1}; if(RenderBits<PF_Pixel16>(&id,p,&iw,&ow)!=0)return 4;
 size_t bad=0;for(size_t i=0;i<187;i++){auto a=u16(exp,i*8),g=u16(exp,i*8+2),r=u16(exp,i*8+4),b=u16(exp,i*8+6);if(out[i].alpha!=a||out[i].green!=g||out[i].red!=r||out[i].blue!=b){if(bad<5)std::fprintf(stderr,"bad %zu got %u,%u,%u,%u exp %u,%u,%u,%u\n",i,out[i].alpha,out[i].green,out[i].red,out[i].blue,a,g,r,b);bad++;}}
 if(bad)return 1;std::printf("PASS full_frame pixels=187 words=748 mismatches=0\n");return 0;
}
