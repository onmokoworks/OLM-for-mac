#include "dg_renderbits_real_harness_20260716_sdk_shim.h"
#include "../../mac/OLMDistanceGradation/OLMDistanceGradation.cpp"
#include <array>
#include <cstdio>
#include <fstream>
#include <iterator>
#include <vector>
static std::vector<unsigned char> rd(const char*p){std::ifstream s(p,std::ios::binary);return {std::istreambuf_iterator<char>(s),{}};}
int main(int c,char**v){if(c!=3)return 2;auto s=rd(v[1]),e=rd(v[2]);if(s.size()!=2992||e.size()!=2992)return 3;std::vector<unsigned char>out(2992,0xcd);PF_LayerDef iw{s.data(),17,11,272,32,{0,0,17,11}},ow{out.data(),17,11,272,32,{0,0,17,11}};std::array<PF_ParamDef,DG_NUM_PARAMS>st{};PF_ParamDef*p[DG_NUM_PARAMS];for(int i=0;i<DG_NUM_PARAMS;i++)p[i]=&st[i];st[0].u.ld=iw;st[DG_INVERT].u.bd.value=1;st[DG_IN_OUT].u.pd.value=IN_OUT_INSIDE;st[DG_INSIDE_THRESHOLD].u.sd.value=4;st[DG_OUTSIDE_THRESHOLD].u.sd.value=4;st[DG_RENDER_MODE].u.pd.value=RENDER_MODE_RGB;st[DG_USE_BG_COLOR].u.bd.value=1;st[DG_GRAD_COLOR].u.cd.value={255,28,0,238};st[DG_BG_COLOR].u.cd.value={255,255,0,0};st[DG_INTERP_MODE].u.pd.value=INTERP_LINEAR;st[DG_POWER].u.fs_d.value=1;PF_InData id{};id.downsample_x={1,1};id.downsample_y={1,1};PF_OutData od{};auto err=EffectMain(PF_Cmd_RENDER,&id,&od,p,&ow,nullptr);if(err)return 4;if(out!=e){size_t n=0;for(size_t i=0;i<e.size();i++)n+=out[i]!=e[i];fprintf(stderr,"byte mismatches=%zu\n",n);return 1;}puts("PASS EffectMain PF_Cmd_RENDER PF32 bytes=2992 mismatches=0");}
