#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>
#include "../../mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"

struct RGBA { unsigned char r,g,b,a; };

static RGBA pixel(const std::string &pattern,int x,int y,int w,int h) {
    if(pattern=="uniform") return {96,96,96,255};
    if(pattern=="isolated") return x==w/2&&y==h/2?RGBA{240,20,180,128}:RGBA{8,12,16,0};
    if(pattern=="vertical") return x<w/2?RGBA{16,32,220,255}:RGBA{230,180,20,255};
    if(pattern=="horizontal") return y<h/2?RGBA{20,220,64,255}:RGBA{210,24,180,255};
    if(pattern=="diagonal") return x*h<y*w?RGBA{245,40,32,255}:RGBA{18,80,224,255};
    if(pattern=="checker") return ((x+y)&1)?RGBA{250,8,170,255}:RGBA{2,220,40,64};
    unsigned u=(unsigned)(x+1)*0x9e3779b9u^(unsigned)(y+3)*0x85ebca6bu;
    u^=u>>16;u*=0x7feb352du;u^=u>>15;
    static const unsigned char alphas[]={0,1,64,128,192,255};
    return {(unsigned char)u,(unsigned char)(u>>8),(unsigned char)(u>>16),alphas[(x+3*y)%6]};
}
template<class P> static P cvt(RGBA q);
template<> PF_Pixel8 cvt(RGBA q){return {q.a,q.r,q.g,q.b};}
template<> PF_Pixel16 cvt(RGBA q){auto c=[](int v){return (unsigned short)std::lround(v*32768.0/255.0);};return {c(q.a),c(q.r),c(q.g),c(q.b)};}
template<> PF_PixelFloat cvt(RGBA q){return {q.a/255.f,q.r/255.f,q.g/255.f,q.b/255.f};}

template<class P> static int run(int w,int h,const std::string &pat,int ver,int s,int range,int extra,const char *depth,const std::string &feature,double gamma_value) {
    size_t pad=std::is_same<P,PF_Pixel8>::value?5:(std::is_same<P,PF_Pixel16>::value?7:13),rb=w*sizeof(P)+pad;
    std::vector<unsigned char> in(rb*h,0x3c),out(rb*h,0xa5);std::vector<RGBA> rgba(w*h);
    for(int y=0;y<h;y++)for(int x=0;x<w;x++){rgba[y*w+x]=pixel(pat,x,y,w,h);if(feature!="none"&&x==0&&y==0)rgba[0]={1,1,1,255};if(feature!="none"&&x==1&&y==0)rgba[1]={255,0,0,255};P p=cvt<P>(rgba[y*w+x]);memcpy(in.data()+y*rb+x*sizeof(P),&p,sizeof(P));}
    PF_EffectWorld iw{},ow{};iw.data=in.data();iw.width=w;iw.height=h;iw.rowbytes=rb;iw.extent_hint={0,0,w,h};ow.data=out.data();ow.width=w;ow.height=h;ow.rowbytes=rb;ow.extent_hint={0,0,w,h};
    PF_ParamDef d[SM_NUM_PARAMS]{};PF_ParamDef*q[SM_NUM_PARAMS]{};for(int n=0;n<SM_NUM_PARAMS;n++)q[n]=d+n;
    d[SM_SMOOTHNESS].u.sd.value=s;d[SM_EXTRA_SMOOTH].u.sd.value=extra;d[SM_SMOOTH_RANGE].u.sd.value=range;d[SM_VERSION].u.pd.value=ver;d[SM_GAMMA_MODE].u.pd.value=feature=="gamma_all"?GAMMA_ALL_COLORS:(feature=="none"?GAMMA_NONE:GAMMA_COLORS_ONLY);d[SM_GAMMA_VALUE].u.fs_d.value=gamma_value;
    if(feature=="colors_noninvert"||feature=="colors_invert"){d[SM_ENABLE_KEY].u.bd.value=1;d[SM_INVERT_KEY].u.bd.value=feature=="colors_invert";d[SM_KEY_COLOR].u.cd.value={255,1,1,1};d[SM_NUM_GAMMA_COLORS].u.sd.value=2;d[SM_GAMMA_COLOR_0].u.cd.value={255,255,0,0};d[SM_GAMMA_COLOR_1].u.cd.value={255,1,1,1};}
    const char *probe=getenv("SM2_PROBE_JSON");if(probe){const char*px=getenv("SM2_PROBE_X"),*py=getenv("SM2_PROBE_Y");OLMSmoother2SetWriterFrameProbe(px?atoi(px):w/2,py?atoi(py):h/2,probe);}
    OLMSmoother2ResetIndexHistogram(true);PF_InData id{};if(RenderBits<P>(&id,q,&iw,&ow))return 2;
    printf("RAW ");for(auto b:out)printf("%02x",b);puts("");printf("HIST ");bool first=true;for(int i=0;i<256;i++)if(g_olmsmoother2_index_hist[i]){if(!first)putchar(',');printf("%d:%llu",i,(unsigned long long)g_olmsmoother2_index_hist[i]);first=false;}puts("");
    if(pat=="checker"&&getenv("SM2_DEBUG_SCAN")){std::vector<unsigned char>cp(w*h*4);for(int yy=0;yy<h;yy++)for(int xx=0;xx<w;xx++){auto*z=&cp[(yy*w+xx)*4];z[0]=xx?255:0;z[1]=yy?255:0;}GridDesc g{cp.data(),w,h,w*4};int in2[2]={getenv("SM2_PROBE_X")?atoi(getenv("SM2_PROBE_X")):w/2,getenv("SM2_PROBE_Y")?atoi(getenv("SM2_PROBE_Y")):0},o[2];printf("SCAN");scan_108d0(o,&g,in2);printf(" 108d0=%d,%d",o[0],o[1]);scan_109d0(o,&g,in2);printf(" 109d0=%d,%d",o[0],o[1]);scan_10ad0(o,&g,in2);printf(" 10ad0=%d,%d",o[0],o[1]);scan_10bd0(o,&g,in2);printf(" 10bd0=%d,%d",o[0],o[1]);scan_10d20(o,&g,in2);printf(" 10d20=%d,%d",o[0],o[1]);scan_10e40(o,&g,in2);printf(" 10e40=%d,%d\n",o[0],o[1]);}
    for(int y=0;y<h;y++)for(size_t k=w*sizeof(P);k<rb;k++)if(out[y*rb+k]!=0xa5)return 3;
    return 0;
}
int main(int argc,char**argv){if(argc<9||argc>11)return 64;int w=atoi(argv[1]),h=atoi(argv[2]),ver=atoi(argv[4]),s=atoi(argv[5]),r=atoi(argv[6]),e=atoi(argv[7]);std::string p=argv[3],d=argv[8],f=argc>=10?argv[9]:"none";double g=argc==11?strtod(argv[10],nullptr):2.4;if(d=="PF8")return run<PF_Pixel8>(w,h,p,ver,s,r,e,"PF8",f,g);if(d=="PF16")return run<PF_Pixel16>(w,h,p,ver,s,r,e,"PF16",f,g);if(d=="PF32")return run<PF_PixelFloat>(w,h,p,ver,s,r,e,"PF32",f,g);return 65;}
