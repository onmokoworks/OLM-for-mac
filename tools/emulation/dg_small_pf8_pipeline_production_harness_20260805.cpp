#include "dg_renderbits_real_harness_20260716_sdk_shim.h"
#include "../../mac/OLMDistanceGradation/OLMDistanceGradation.cpp"
#include <array>
#include <cstdint>
#include <cstdio>
#include <fstream>
#include <iterator>
#include <vector>
static std::vector<std::uint8_t> rd(const char*p){std::ifstream s(p,std::ios::binary);return {std::istreambuf_iterator<char>(s),{}};}
int main(int c,char**v){if(c!=3)return 2;auto s=rd(v[1]),e=rd(v[2]);if(s.size()!=748||e.size()!=748)return 3;std::vector<PF_Pixel8>in(187),out(187);for(size_t i=0;i<187;i++)in[i]={s[i*4],s[i*4+2],s[i*4+1],s[i*4+3]};PF_LayerDef iw{in.data(),17,11,68,8,{0,0,17,11}},ow{out.data(),17,11,68,8,{0,0,17,11}};std::array<PF_ParamDef,DG_NUM_PARAMS>st{};PF_ParamDef*p[DG_NUM_PARAMS];for(int i=0;i<DG_NUM_PARAMS;i++)p[i]=&st[i];st[0].u.ld=iw;st[DG_INVERT].u.bd.value=1;st[DG_IN_OUT].u.pd.value=IN_OUT_INSIDE;st[DG_INSIDE_THRESHOLD].u.sd.value=4;st[DG_OUTSIDE_THRESHOLD].u.sd.value=4;st[DG_RENDER_MODE].u.pd.value=RENDER_MODE_RGB;st[DG_USE_BG_COLOR].u.bd.value=1;st[DG_GRAD_COLOR].u.cd.value={255,28,0,238};st[DG_BG_COLOR].u.cd.value={255,255,0,0};st[DG_INTERP_MODE].u.pd.value=INTERP_LINEAR;st[DG_POWER].u.fs_d.value=1;PF_InData id{};id.downsample_x={1,1};id.downsample_y={1,1};if(RenderBits<PF_Pixel8>(&id,p,&iw,&ow))return 4;size_t bad=0;for(size_t i=0;i<187;i++){auto a=e[i*4],g=e[i*4+1],r=e[i*4+2],b=e[i*4+3];if(out[i].alpha!=a||out[i].green!=g||out[i].red!=r||out[i].blue!=b){if(bad<5)fprintf(stderr,"bad %zu got %u,%u,%u,%u exp %u,%u,%u,%u\n",i,out[i].alpha,out[i].green,out[i].red,out[i].blue,a,g,r,b);bad++;}}if(bad)return 1;puts("PASS full_frame pixels=187 words=748 mismatches=0");}
