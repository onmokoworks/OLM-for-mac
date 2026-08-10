#include <cmath>
#include <cstdio>
#include <cstring>
#include <vector>
#include "../../mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"

static constexpr int W=5,H=5,N=W*H;
static const unsigned char RGB[N][3]={{1,1,1},{255,0,0},{65,1,1},{0,255,0},{206,55,161},{86,55,26},{43,73,217},{231,16,235},{116,106,230},{1,9,43},{91,38,34},{99,183,84},{230,125,149},{208,155,60},{168,21,161},{233,157,226},{8,57,119},{159,56,196},{232,156,109},{50,140,246},{229,135,20},{36,6,46},{176,107,229},{168,83,193},{235,7,162}};

template<class P> static int run(const char*depth,const P*p){
  const size_t pad=std::is_same<P,PF_Pixel8>::value?5:(std::is_same<P,PF_Pixel16>::value?7:13),rb=W*sizeof(P)+pad;
  std::vector<unsigned char>i(rb*H,0x3c),o(rb*H,0xa5);
  for(int y=0;y<H;y++)for(int x=0;x<W;x++)memcpy(i.data()+y*rb+x*sizeof(P),p+y*W+x,sizeof(P));
  PF_EffectWorld iw{},ow{};iw.data=i.data();iw.width=W;iw.height=H;iw.rowbytes=rb;iw.extent_hint={0,0,W,H};ow.data=o.data();ow.width=W;ow.height=H;ow.rowbytes=rb;ow.extent_hint={0,0,W,H};
  PF_ParamDef d[SM_NUM_PARAMS]{};PF_ParamDef*q[SM_NUM_PARAMS]{};for(int n=0;n<SM_NUM_PARAMS;n++)q[n]=d+n;
  d[SM_ENABLE_KEY].u.bd.value=1;d[SM_INVERT_KEY].u.bd.value=1;d[SM_KEY_COLOR].u.cd.value={255,1,1,1};
  d[SM_SMOOTHNESS].u.sd.value=100;d[SM_EXTRA_SMOOTH].u.sd.value=100;d[SM_SMOOTH_RANGE].u.sd.value=100;d[SM_VERSION].u.pd.value=SMOOTHER_V2;
  d[SM_GAMMA_MODE].u.pd.value=GAMMA_COLORS_ONLY;d[SM_GAMMA_VALUE].u.fs_d.value=2.4;d[SM_NUM_GAMMA_COLORS].u.sd.value=2;
  d[SM_GAMMA_COLOR_0].u.cd.value={255,255,0,0};d[SM_GAMMA_COLOR_1].u.cd.value={255,1,1,1};
  PF_InData id{};if(RenderBits<P>(&id,q,&iw,&ow))return 2;printf("%s ",depth);for(auto b:o)printf("%02x",b);puts("");return 0;
}
int main(){
  PF_Pixel8 p8[N]{};PF_Pixel16 p16[N]{};PF_PixelFloat p32[N]{};
  for(int n=0;n<N;n++){p8[n]={255,RGB[n][0],RGB[n][1],RGB[n][2]};p16[n].alpha=32768;p16[n].red=(unsigned short)std::lround(RGB[n][0]*32768.0/255.0);p16[n].green=(unsigned short)std::lround(RGB[n][1]*32768.0/255.0);p16[n].blue=(unsigned short)std::lround(RGB[n][2]*32768.0/255.0);p32[n]={1.f,RGB[n][0]/255.f,RGB[n][1]/255.f,RGB[n][2]/255.f};}
  return run("PF8",p8)||run("PF16",p16)||run("PF32",p32);
}
