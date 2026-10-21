#include "olm_sha256_rows.h"
#define OLM_RADIALBLUR_TEST_SEAM 1
#ifndef OLM_RADIAL_SOURCE_INCLUDE
#define OLM_RADIAL_SOURCE_INCLUDE "../../mac/OLMRadialBlur/OLMRadialBlur.cpp"
#endif
#include OLM_RADIAL_SOURCE_INCLUDE
#include <algorithm>
#include <cstdio>
#include <cstring>
#include <vector>

template <typename P> static void Fill(std::vector<unsigned char>& raw,int rb){
 for(int y=0;y<18;y++){for(int x=0;x<32;x++){P p{};
  if constexpr(std::is_same<P,PF_Pixel8>::value)p={(A_u_char)((x+y)%5?255:127),(A_u_char)((x*31+y*7)%256),(A_u_char)((x*11+y*29)%256),(A_u_char)((x*47+y*13)%256)};
  else if constexpr(std::is_same<P,PF_Pixel16>::value)p={(A_u_short)((x+y)%5?32768:16384),(A_u_short)((x*4093+y*257)%32769),(A_u_short)((x*1237+y*3559)%32769),(A_u_short)((x*7919+y*911)%32769)};
  else p={(x+y)%5?1.f:.5f,(float)(((x*4093+y*257)%32769)/32768.),(float)(((x*1237+y*3559)%32769)/32768.),(float)(((x*7919+y*911)%32769)/32768.)};
  std::memcpy(raw.data()+(size_t)y*rb+(size_t)x*sizeof(P),&p,sizeof p);}
  std::fill(raw.begin()+(size_t)y*rb+32*sizeof(P),raw.begin()+(size_t)(y+1)*rb,(unsigned char)(0xa0+y));}}

static std::string Digest(const std::vector<unsigned char>& raw,int rb,int active){olm::Sha256 h;for(int y=0;y<18;y++)h.update(raw.data()+(size_t)y*rb,active);unsigned char d[32];h.final(d);char s[65];for(int i=0;i<32;i++)std::snprintf(s+i*2,3,"%02x",d[i]);s[64]=0;return s;}

static OLMRadialBlurInfo Info(int side,int fade,double nv){OLMRadialBlurInfo i{};i.blur_type=2;i.center_x=16;i.center_y=9;
 if(side==0){i.outer_strength=4;i.outer_edge_fade=fade;}else{i.inner_strength=4;i.inner_edge_fade=fade;}
 i.outer_offset_mode=1;i.inner_offset_mode=1;i.repeat_border=TRUE;i.ratio=1;i.quality=5;i.brightness_gain=1;
 i.noise_variation=nv;i.noise_type=1;i.seed=1;i.thickness=10;i.comp_width=32;i.comp_height=18;return i;}

template<typename P>static int Run(int depth){int active=32*(int)sizeof(P),rb=active+(depth==8?8:16);std::vector<unsigned char> canonical((size_t)rb*18);Fill<P>(canonical,rb);
 for(int side:{0,1})for(int fade:{50,100})for(double nv:{25.,100.}){auto in=canonical,before=in;std::vector<unsigned char> out((size_t)rb*18,0xee);PF_EffectWorld iw{},ow{};iw.data=(PF_PixelPtr)in.data();iw.rowbytes=rb;iw.width=32;iw.height=18;ow=iw;ow.data=(PF_PixelPtr)out.data();auto info=Info(side,fade,nv);auto e=OLMRadialBlurTestRenderWorld(&iw,&ow,&info,depth);if(e||in!=before)return 10+depth;for(int y=0;y<18;y++)for(int x=active;x<rb;x++)if(out[(size_t)y*rb+x]!=0xee)return 20+depth;std::printf("POS PF%d %s f%d nv%.0f %s\n",depth,side?"inner":"outer",fade,nv,Digest(out,rb,active).c_str());}
#ifndef OLM_RADIAL_SKIP_MUTATION_CHECKS
 for(int m=0;m<3;m++){auto in=canonical;size_t off=m==0?0:m==1?(size_t)9*rb+active/2:(size_t)17*rb+active-1;in[off]^=1;auto before=in;std::vector<unsigned char> out((size_t)rb*18,0xee);PF_EffectWorld iw{},ow{};iw.data=(PF_PixelPtr)in.data();iw.rowbytes=rb;iw.width=32;iw.height=18;ow=iw;ow.data=(PF_PixelPtr)out.data();auto info=Info(0,50,25);auto e=OLMRadialBlurTestRenderWorld(&iw,&ow,&info,depth);if(e!=PF_Err_BAD_CALLBACK_PARAM||in!=before||!std::all_of(out.begin(),out.end(),[](unsigned char v){return v==0xee;}))return 100+depth+m;std::printf("NEG PF%d m%d reject\n",depth,m);}
#endif
 return 0;}
int main(){if(int e=Run<PF_Pixel8>(8))return e;if(int e=Run<PF_Pixel16>(16))return e;return Run<PF_PixelFloat>(32);}
