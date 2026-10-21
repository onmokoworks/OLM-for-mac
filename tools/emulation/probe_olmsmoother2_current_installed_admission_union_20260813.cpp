#include <cmath>
#include <cstdio>
#include <cstring>
#include <dlfcn.h>
#include <vector>

#include "AE_Effect.h"
#include "AE_EffectCBSuites.h"
#include "AE_EffectSuites.h"
#include "SPBasic.h"

#define EffectMain SourceBuiltOLMSmoother2EffectMain
#include "../../mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"
#undef EffectMain

using Effect = PF_Err (*)(PF_Cmd, PF_InData *, PF_OutData *, PF_ParamDef *[], PF_LayerDef *, void *);

enum Family { GAMMA18, GAMMA24, SMALL3X2, COVER17X11 };
struct Case { const char *name; Family family; int depth, version, key, gamma, count, palette, smooth, range, extra; double value; bool premul; };
static const Case CASES[] = {
    {"gamma18_pf8_v1_invert",GAMMA18,8,1,2,GAMMA_COLORS_ONLY,2,0,100,100,100,1.8,false},
    {"gamma18_pf8_v2_key",GAMMA18,8,2,1,GAMMA_COLORS_ONLY,2,0,100,100,100,1.8,false},
    {"gamma18_pf8_v2_invert",GAMMA18,8,2,2,GAMMA_COLORS_ONLY,2,0,100,100,100,1.8,false},
    {"gamma18_pf16_v1_invert",GAMMA18,16,1,2,GAMMA_COLORS_ONLY,2,0,100,100,100,1.8,false},
    {"gamma18_pf16_v2_key",GAMMA18,16,2,1,GAMMA_COLORS_ONLY,2,0,100,100,100,1.8,false},
    {"gamma18_pf16_v2_invert",GAMMA18,16,2,2,GAMMA_COLORS_ONLY,2,0,100,100,100,1.8,false},
    {"gamma18_pf32_v1_invert",GAMMA18,32,1,2,GAMMA_COLORS_ONLY,2,0,100,100,100,1.8,false},
    {"gamma18_pf32_v2_key",GAMMA18,32,2,1,GAMMA_COLORS_ONLY,2,0,100,100,100,1.8,false},
    {"gamma18_pf32_v2_invert",GAMMA18,32,2,2,GAMMA_COLORS_ONLY,2,0,100,100,100,1.8,false},
    {"gamma24_pf8_v1_key",GAMMA24,8,1,1,GAMMA_COLORS_ONLY,2,0,100,100,100,2.4,false},
    {"gamma24_pf8_v2_invert",GAMMA24,8,2,2,GAMMA_COLORS_ONLY,2,0,100,100,100,2.4,false},
    {"gamma24_pf16_v1_key",GAMMA24,16,1,1,GAMMA_COLORS_ONLY,2,0,100,100,100,2.4,false},
    {"gamma24_pf16_v2_invert",GAMMA24,16,2,2,GAMMA_COLORS_ONLY,2,0,100,100,100,2.4,false},
    {"gamma24_pf32_v1_key",GAMMA24,32,1,1,GAMMA_COLORS_ONLY,2,0,100,100,100,2.4,false},
    {"gamma24_pf32_v2_invert",GAMMA24,32,2,2,GAMMA_COLORS_ONLY,2,0,100,100,100,2.4,false},
    {"small3x2_pf32",SMALL3X2,32,2,0,GAMMA_NONE,0,0,100,1,0,2.4,false},
    {"cover_pf8_straight",COVER17X11,8,1,0,GAMMA_NONE,1,0,100,2,0,1.0,false},
    {"cover_pf8_premul",COVER17X11,8,2,2,GAMMA_COLORS_ONLY,5,2,50,50,50,2.4,true},
    {"cover_pf16_straight",COVER17X11,16,2,0,GAMMA_ALL_COLORS,1,0,50,50,50,2.4,false},
    {"cover_pf16_premul",COVER17X11,16,2,1,GAMMA_COLORS_ONLY,5,1,100,2,0,1.0,true},
    {"cover_pf32_premul",COVER17X11,32,1,0,GAMMA_NONE,1,0,50,50,50,1.0,true},
    {"cover_pf32_straight",COVER17X11,32,2,1,GAMMA_COLORS_ONLY,1,0,100,2,0,2.4,false},
};

static PF_ParamDef g_params[SM_NUM_PARAMS];
static PF_EffectWorld *g_input, *g_output;
static int g_depth, g_layer, g_output_calls, g_param_out, g_param_in, g_layer_in;
static int g_aw, g_rw, g_ac, g_rc, g_formats, g_colors;
static PF_WorldSuite2 g_world{}; static PF_ColorParamSuite1 g_color{};

static PF_Err GetFormat(const PF_EffectWorld *, PF_PixelFormat *f) { ++g_formats; *f=g_depth==8?PF_PixelFormat_ARGB32:g_depth==16?PF_PixelFormat_ARGB64:PF_PixelFormat_ARGB128; return 0; }
static PF_Err GetColor(PF_ProgPtr,const PF_ParamDef *p,PF_PixelFloat *o){++g_colors;o->alpha=p->u.cd.value.alpha/255.f;o->red=p->u.cd.value.red/255.f;o->green=p->u.cd.value.green/255.f;o->blue=p->u.cd.value.blue/255.f;return 0;}
static SPErr Acquire(const char*n,int32 v,const void**s){if(!std::strcmp(n,kPFWorldSuite)&&v==kPFWorldSuiteVersion2){++g_aw;g_world.PF_GetPixelFormat=GetFormat;*s=&g_world;return 0;}if(!std::strcmp(n,kPFColorParamSuite)&&v==kPFColorParamSuiteVersion1){++g_ac;g_color.PF_GetFloatingPointColorFromColorDef=GetColor;*s=&g_color;return 0;}return kSPBadParameterError;}
static SPErr Release(const char*n,int32 v){if(!std::strcmp(n,kPFWorldSuite)&&v==kPFWorldSuiteVersion2){++g_rw;return 0;}if(!std::strcmp(n,kPFColorParamSuite)&&v==kPFColorParamSuiteVersion1){++g_rc;return 0;}return kSPBadParameterError;}
static PF_Err Checkout(PF_ProgPtr,PF_ParamIndex i,A_long,A_long,A_u_long,PF_ParamDef*p){++g_param_out;*p=g_params[i];return 0;}
static PF_Err Checkin(PF_ProgPtr,PF_ParamDef*){++g_param_in;return 0;}
static PF_Err Layer(PF_ProgPtr,A_long i,PF_EffectWorld**w){++g_layer;if(i!=SM_INPUT)return PF_Err_BAD_CALLBACK_PARAM;*w=g_input;return 0;}
static PF_Err Output(PF_ProgPtr,PF_EffectWorld**w){++g_output_calls;*w=g_output;return 0;}
static PF_Err CheckinLayer(PF_ProgPtr,A_long i){if(i==SM_INPUT)++g_layer_in;return 0;}

struct RGBA { unsigned char r,g,b,a; };
static RGBA Logical17(int x,int y){unsigned u=(unsigned)(x+1)*0x9e3779b9u^(unsigned)(y+3)*0x85ebca6bu;u^=u>>16;u*=0x7feb352du;u^=u>>15;static const unsigned char a[]={0,1,64,128,192,255};if(x==0&&y==0)return{1,1,1,128};if(x==1&&y==0)return{255,0,0,192};return{(unsigned char)u,(unsigned char)(u>>8),(unsigned char)(u>>16),a[(x+3*y)%6]};}
template<class P> static P Pixel(RGBA,bool);
template<> PF_Pixel8 Pixel(RGBA q,bool pm){auto c=[&](unsigned v){return(unsigned char)(pm?((v*q.a+127u)/255u):v);};return{q.a,c(q.r),c(q.g),c(q.b)};}
template<> PF_Pixel16 Pixel(RGBA q,bool pm){auto n=[](unsigned v){return(unsigned)std::lround(v*32768.0/255.0);};unsigned a=n(q.a);auto c=[&](unsigned v){unsigned z=n(v);return(unsigned short)(pm?((z*a+16384u)/32768u):z);};return{(unsigned short)a,c(q.r),c(q.g),c(q.b)};}
template<> PF_PixelFloat Pixel(RGBA q,bool pm){float a=q.a/255.f;auto c=[&](unsigned v){float z=v/255.f;return pm?z*a:z;};return{a,c(q.r),c(q.g),c(q.b)};}

struct Fixture { int w,h,pixel,rowbytes; std::vector<unsigned char> input,output; PF_EffectWorld iw{},ow{}; Fixture(const Case&c):w(c.family==SMALL3X2?3:c.family==COVER17X11?17:5),h(c.family==SMALL3X2?2:c.family==COVER17X11?11:5),pixel(c.depth==8?4:c.depth==16?8:16),rowbytes(w*pixel+(c.family==SMALL3X2?12:c.depth==8?5:c.depth==16?7:13)),input(rowbytes*h,0xa5),output(rowbytes*h,0xee){iw.data=reinterpret_cast<PF_PixelPtr>(input.data());iw.width=w;iw.height=h;iw.rowbytes=rowbytes;iw.extent_hint={0,0,w,h};ow=iw;ow.data=reinterpret_cast<PF_PixelPtr>(output.data());Fill(c);} void Fill(const Case&c){static const unsigned char rgb[25][3]={{202,187,230},{255,0,0},{65,1,1},{0,255,0},{206,55,161},{86,55,26},{43,73,217},{231,16,235},{116,106,230},{1,9,43},{91,38,34},{99,183,84},{230,125,149},{208,155,60},{168,21,161},{233,157,226},{8,57,119},{159,56,196},{232,156,109},{50,140,246},{229,135,20},{36,6,46},{176,107,229},{168,83,193},{235,7,162}};for(int y=0;y<h;++y)for(int x=0;x<w;++x){unsigned char*d=input.data()+y*rowbytes+x*pixel;if(c.family==SMALL3X2){static const PF_PixelFloat p[6]={{1,0,0,0},{1,0,1,1},{1,1,0,1},{1,1,1,0},{1,.25f,.25f,.25f},{1,.75f,.75f,.75f}};std::memcpy(d,p+y*3+x,sizeof(PF_PixelFloat));continue;}RGBA q;if(c.family==COVER17X11)q=Logical17(x,y);else{q={rgb[y*5+x][0],rgb[y*5+x][1],rgb[y*5+x][2],255};if(c.family==GAMMA24&&x==0&&y==0)q={1,1,1,255};}if(c.depth==8){auto p=Pixel<PF_Pixel8>(q,c.premul);std::memcpy(d,&p,sizeof(p));}else if(c.depth==16){auto p=Pixel<PF_Pixel16>(q,c.premul);std::memcpy(d,&p,sizeof(p));}else{auto p=Pixel<PF_PixelFloat>(q,c.premul);std::memcpy(d,&p,sizeof(p));}}}};
static void Color(PF_ParamDef&d,RGBA q){d.u.cd.value={q.a,q.r,q.g,q.b};}
struct Result{PF_Err err;std::vector<unsigned char>input,output;int layer,out,po,pi,li,aw,rw,ac,rc,formats,colors;};
static Result Run(Effect effect,const Case&c){Fixture f(c);std::memset(g_params,0,sizeof(g_params));g_params[0].u.ld=f.iw;g_params[SM_ENABLE_KEY].u.bd.value=c.key!=0;g_params[SM_INVERT_KEY].u.bd.value=c.key==2;g_params[SM_SMOOTHNESS].u.sd.value=c.smooth;g_params[SM_SMOOTH_RANGE].u.sd.value=c.range;g_params[SM_EXTRA_SMOOTH].u.sd.value=c.extra;g_params[SM_VERSION].u.pd.value=c.version;g_params[SM_GAMMA_MODE].u.pd.value=c.gamma;g_params[SM_GAMMA_VALUE].u.fs_d.value=c.value;g_params[SM_NUM_GAMMA_COLORS].u.sd.value=c.count;if(c.family==GAMMA18)Color(g_params[SM_KEY_COLOR],{202,187,230,255});else if(c.family==GAMMA24)Color(g_params[SM_KEY_COLOR],{1,1,1,255});else if(c.family==COVER17X11)Color(g_params[SM_KEY_COLOR],{1,1,1,255});RGBA normal[5]={{255,0,0,255},{1,1,1,255},{0,0,255,255},{0,255,0,255},{255,255,0,255}},reordered[5]={{255,255,0,255},{0,255,0,255},{1,1,1,255},{255,0,0,255},{0,0,255,255}},duplicates[5]={{255,0,0,255},{1,1,1,255},{255,0,0,255},{1,1,1,255},{0,0,255,255}};RGBA *pal=c.palette==1?reordered:c.palette==2?duplicates:normal;if(c.family==GAMMA18){Color(g_params[SM_GAMMA_COLOR_0],{255,0,0,255});Color(g_params[SM_GAMMA_COLOR_1],{202,187,230,255});}else if(c.family==GAMMA24){Color(g_params[SM_GAMMA_COLOR_0],{255,0,0,255});Color(g_params[SM_GAMMA_COLOR_1],{1,1,1,255});}else for(int i=0;i<c.count;++i)Color(g_params[SM_GAMMA_COLOR_0+i],pal[i]);g_input=&f.iw;g_output=&f.ow;g_depth=c.depth;g_layer=g_output_calls=g_param_out=g_param_in=g_layer_in=g_aw=g_rw=g_ac=g_rc=g_formats=g_colors=0;SPBasicSuite basic{};basic.AcquireSuite=Acquire;basic.ReleaseSuite=Release;PF_InData in{};in.effect_ref=(PF_ProgPtr)1;in.pica_basicP=&basic;in.current_time=7;in.time_step=1;in.time_scale=24;in.downsample_x={1,1};in.downsample_y={1,1};in.inter.checkout_param=Checkout;in.inter.checkin_param=Checkin;PF_OutData out{};PF_SmartRenderInput si{};si.bitdepth=c.depth;PF_SmartRenderCallbacks cb{};cb.checkout_layer_pixels=Layer;cb.checkout_output=Output;cb.checkin_layer_pixels=CheckinLayer;PF_SmartRenderExtra ex{&si,&cb};PF_Err err=effect(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&ex);return{err,f.input,f.output,g_layer,g_output_calls,g_param_out,g_param_in,g_layer_in,g_aw,g_rw,g_ac,g_rc,g_formats,g_colors};}
static bool Padding(const Case&c,const std::vector<unsigned char>&b,unsigned char v){Fixture f(c);for(int y=0;y<f.h;++y)for(int x=f.w*f.pixel;x<f.rowbytes;++x)if(b[y*f.rowbytes+x]!=v)return false;return true;}

int main(){const char*path=std::getenv("OLMSMOOTHER2_INSTALLED_BINARY");if(!path)return 2;void*h=dlopen(path,RTLD_NOW|RTLD_LOCAL);if(!h){std::fprintf(stderr,"%s\n",dlerror());return 3;}auto installed=(Effect)dlsym(h,"EffectMain");if(!installed)return 4;int pass=0;for(const auto&c:CASES){auto s=Run(SourceBuiltOLMSmoother2EffectMain,c),i=Run(installed,c);bool life=s.layer==1&&s.out==1&&s.po==SM_NUM_PARAMS-1&&s.pi==s.po&&s.li==1&&s.aw==2&&s.rw==2&&s.ac==1&&s.rc==1&&s.formats==2&&s.colors==1+NUM_GAMMA_COLORS;bool same=i.layer==s.layer&&i.out==s.out&&i.po==s.po&&i.pi==s.pi&&i.li==s.li&&i.aw==s.aw&&i.rw==s.rw&&i.ac==s.ac&&i.rc==s.rc&&i.formats==s.formats&&i.colors==s.colors;bool ok=s.err==0&&i.err==0&&s.input==i.input&&s.output==i.output&&Padding(c,s.output,0xee)&&Padding(c,i.output,0xee)&&life&&same;if(ok)++pass;std::printf("POS %s pass=%d source_err=%d installed_err=%d\n",c.name,ok?1:0,s.err,i.err);}std::printf("SUMMARY pass=%d total=%zu\n",pass,sizeof(CASES)/sizeof(CASES[0]));dlclose(h);return pass==(int)(sizeof(CASES)/sizeof(CASES[0]))?0:5;}
