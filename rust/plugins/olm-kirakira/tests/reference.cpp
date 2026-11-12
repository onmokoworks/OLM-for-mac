#include <algorithm>
#include <cmath>
#include <cstring>
#include <vector>
#include "core/kirakira_mode4.h"
#include "core/kirakira_gaussian.h"
#include "core/kirakira_highlight.h"
#include "core/kirakira_highlight_gaussian.h"
#include "core/kirakira_merge2.h"
using A_long=int; using A_u_long=unsigned; using PF_FpLong=double; using PF_Boolean=bool;
struct PF_PixelFloat {float alpha,red,green,blue;};
struct PF_EffectWorld {int width,height;void* data;};
struct FloatRGBA {float r=0,g=0,b=0,a=0;};
constexpr float kFd90RayEpsilon=0.001f;
constexpr double kColorRayEpsilon=0.001;
float Clamp01(float v){return std::min(1.f,std::max(0.f,v));}
int Reflect101Index(int x,int n){return olm::kirakira::highlight_reflect101(x,n);}
int AexRotatedExtent(int a,int b,float c,float s){return olm::kirakira::rotated_extent(a,b,c,s);}
template<class T> struct PixelTraits;
template<class T> T LoadWorldPixel(PF_EffectWorld*,int,int);
struct OLMKiraKiraRampStop {
	float position;
	float alpha;
	float red;
	float green;
	float blue;
};

struct OLMKiraKiraRampData {
	A_u_long count;
	OLMKiraKiraRampStop stops[16];
};

static_assert(sizeof(OLMKiraKiraRampData) == 0x144, "Windows ramp payload ABI");

typedef struct {
	PF_FpLong glow_rotation;
	PF_FpLong brightness_gain;
	PF_FpLong fade_out;
	A_long vertical_length;
	A_long horizontal_length;
	A_long diagonal_length;
	A_long diagonal2_length;
	A_long highlight_radius;
	PF_FpLong glow_opacity;
	A_long channel;
	A_long blur_mode;
	A_long merge_mode;
	PF_Boolean approximated_input;
	PF_FpLong strength_multiplier;
	PF_FpLong source_opacity;
	PF_PixelFloat vertical_color;
	PF_PixelFloat horizontal_color;
	PF_PixelFloat diagonal_color;
	PF_PixelFloat highlight_color;
	PF_PixelFloat diagonal2_color;
	PF_Boolean vertical_use_ramp;
	PF_Boolean horizontal_use_ramp;
	PF_Boolean diagonal_use_ramp;
	PF_Boolean highlight_use_ramp;
	PF_Boolean diagonal2_use_ramp;
	OLMKiraKiraRampData vertical_ramp;
	OLMKiraKiraRampData horizontal_ramp;
	OLMKiraKiraRampData diagonal_ramp;
	OLMKiraKiraRampData highlight_ramp;
	OLMKiraKiraRampData diagonal2_ramp;
	PF_FpLong comp_width;
} OLMKiraKiraInfo;


static bool UsesRecoveredSeedPipeline(const OLMKiraKiraInfo&);
static bool UsesRecoveredColorPipeline(const OLMKiraKiraInfo&);
static bool UsesRecoveredApproximation(const OLMKiraKiraInfo&);
#include "mac/OLMKiraKira/KiraFilters.inc"
extern "C" void ref_trig(double x,float* out) {auto v=olm::kirakira::extent_sincos(x);out[0]=v.sine;out[1]=v.cosine;}
extern "C" void ref_filter(const float* src,float* dst,int w,int h,int len,double angle,int kind,int normalize) {
 std::vector<float> input(src,src+w*h),out;
 if(kind<=4) out=RotatedAxisBoxBlur(input,w,h,len,angle,kind==1?1:3,kind,true,true,normalize);
 else if(kind==5) out=olm::kirakira::highlight_isotropic_box_blur(input,w,h,len*2+1,1,normalize);
 else if(kind==6) out=olm::kirakira::highlight_isotropic_box_blur(input,w,h,len*2+1,3,normalize);
 else out=olm::kirakira::highlight_gaussian(input,w,h,len);
 std::memcpy(dst,out.data(),out.size()*4);
}
extern "C" void ref_seed(const FloatRGBA* src,float* dst,int n,int channel,float strength,float fade) {
 OLMKiraKiraInfo info{};info.channel=channel;info.blur_mode=2;info.strength_multiplier=strength;info.fade_out=fade;
 std::vector<FloatRGBA> pixels(src,src+n);auto out=MakeSeed(pixels,n,1,info);std::memcpy(dst,out.data(),out.size()*4);
}
extern "C" void ref_compose(const FloatRGBA* g,const FloatRGBA* s,FloatRGBA* out,float go,float so,int merge) {
 *out=merge==2?ComposeMerge2Pixel(*g,*s,go,so):ComposePremultiplyPixel(*g,*s,go,so);
}
extern "C" void ref_resize(const FloatRGBA* src,FloatRGBA* dst,int sw,int sh,int dw,int dh){
 std::vector<FloatRGBA> input(src,src+sw*sh);auto out=ResizeLinearRGBA(input,sw,sh,dw,dh);std::memcpy(dst,out.data(),out.size()*16);
}

using PF_Err=int;
constexpr int PF_Err_BAD_CALLBACK_PARAM=4,PF_Err_NONE=0;
using PF_Pixel8=FloatRGBA;using PF_Pixel16=FloatRGBA;
template<class T> struct PixelTraits {static FloatRGBA Read(T p){return {p.r,p.g,p.b,p.a};} static T WriteAexTruncate(FloatRGBA p){return {p.r,p.g,p.b,p.a};}};
template<> struct PixelTraits<PF_PixelFloat> {static FloatRGBA Read(PF_PixelFloat p){return {p.red,p.green,p.blue,p.alpha};} static PF_PixelFloat WriteAexTruncate(FloatRGBA p){return {p.a,p.r,p.g,p.b};}};
template<class T> T LoadWorldPixel(PF_EffectWorld* w,int x,int y){return ((T*)w->data)[y*w->width+x];}
template<class T> void StoreWorldPixel(PF_EffectWorld* w,int x,int y,T p){((T*)w->data)[y*w->width+x]=p;}
struct KiraKiraDebugConfig{};KiraKiraDebugConfig LoadKiraKiraDebugConfig(){return {};}
template<class... T> void KiraKiraDebugDumpPoint(T... ){}
#include "mac/OLMKiraKira/KiraRender.inc"
extern "C" void ref_render(const FloatRGBA* src,FloatRGBA* dst,int w,int h,const double* params,float scale){
 OLMKiraKiraInfo p{};p.channel=int(params[0]);p.blur_mode=int(params[1]);p.merge_mode=int(params[2]);p.approximated_input=params[3]!=0;
 p.brightness_gain=params[4];p.strength_multiplier=params[5];p.fade_out=params[6];p.glow_opacity=params[7];p.source_opacity=params[8];
 p.glow_rotation=params[9];p.vertical_length=int(params[10]);p.horizontal_length=int(params[11]);p.diagonal_length=int(params[12]);p.diagonal2_length=int(params[13]);p.highlight_radius=int(params[14]);
 p.vertical_color=p.horizontal_color=p.diagonal_color=p.diagonal2_color=p.highlight_color={1,1,1,1};
 PF_EffectWorld iw{w,h,(void*)src},ow{w,h,dst};RenderTyped<FloatRGBA>(&iw,&ow,p,32,scale);
}
#include "mac/OLMKiraKira/RampEditor.h"
extern "C" int ref_ui(OLMKiraKiraRampData* ramp,int* state,OLMKiraKiraRampData* clip,int* available,uint32_t* rng,int event,int x,int y,uint64_t* digest){
 namespace e=olm::kirakira::editor;
 e::State s{state[0],state[1],state[2],state[3],state[4],state[5]!=0,state[6],state[7]};
 e::Clipboard<OLMKiraKiraRampData> c{*available!=0,*clip};
 auto r=e::dispatch(*ramp,s,c,*rng,{static_cast<e::EventType>(event),x,y});
 *clip=c.data;*available=c.available;
 int a[]={s.selected,s.armed,s.hover_x,s.hover_y,s.anchor_y,s.menu_open,s.preset_row,s.scroll};std::memcpy(state,a,sizeof(a));
 e::Theme theme{{0,0,0,1,7},{0,0,0,1,8},{0,0,0,1,2},{0,0,0,1,42}};
 uint64_t h=1469598103934665603ull;auto word=[&](uint32_t v){h^=v;h*=1099511628211ull;};auto f=[&](float v){uint32_t u;std::memcpy(&u,&v,4);word(u);};
 for(const auto& d:e::draw(*ramp,s,c.available,theme)){
  word((int)d.kind);for(float v:{d.x,d.y,d.w,d.h,d.color.red,d.color.green,d.color.blue,d.color.alpha})f(v);
  word(d.color.theme_role);f(d.color.factor);f(d.font);if(d.text)for(auto t=d.text;*t;++t)word(*t);word(0);
 }
 *digest=h;return r.picker;
}
extern "C" void ref_ramp_interp(const OLMKiraKiraRampData* a,const OLMKiraKiraRampData* b,float t,OLMKiraKiraRampData* out){
 *out={};out->count=(unsigned)olm::kirakira::interpolate_merge2_ramps(
 reinterpret_cast<olm::kirakira::Merge2RampStop*>(out->stops),reinterpret_cast<const olm::kirakira::Merge2RampStop*>(a->stops),a->count,
 reinterpret_cast<const olm::kirakira::Merge2RampStop*>(b->stops),b->count,t);
}
extern "C" void ref_legacy(const FloatRGBA* src,FloatRGBA* dst,int w,int h,int variant){
 OLMKiraKiraInfo p{};p.channel=1;p.blur_mode=4;p.merge_mode=variant?2:1;p.brightness_gain=variant?0.73:1.0;p.strength_multiplier=1;p.source_opacity=p.glow_opacity=1;
 p.glow_rotation=variant?1:0;p.horizontal_length=(variant==1||variant==4)?5:0;p.diagonal2_length=(variant==2||variant==4)?7:0;p.highlight_radius=(variant==0||variant==3||variant==4)?3:0;
 p.horizontal_use_ramp=p.horizontal_length!=0;p.highlight_use_ramp=variant!=0 && p.highlight_radius!=0;
 p.vertical_color=p.horizontal_color=p.diagonal_color=p.diagonal2_color=p.highlight_color={1,1,1,1};
 p.vertical_ramp=p.horizontal_ramp=p.diagonal_ramp=p.diagonal2_ramp=p.highlight_ramp=olm::kirakira::editor::preset<OLMKiraKiraRampData>(0);
 PF_EffectWorld iw{w,h,(void*)src},ow{w,h,dst};RenderTyped<FloatRGBA>(&iw,&ow,p,32,1.0f);
}
